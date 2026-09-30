from __future__ import annotations

import os
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Tuple

import ccxt
import numpy as np
import pandas as pd
import requests


# ================================================================
# EXCORA INSTITUTIONAL SMC - MTF FINAL
#
# 4H  = Macro / Institutional trend + EMA200 + structure
# 1H  = Confirmation + BOS / CHoCH
# 15M = Execution + liquidity sweep + OB + FVG + displacement
#
# Risk: 1% recommended, 2% maximum
# RR: 3:1
# Closed candles only. No real orders.
# Score is confluence, NOT win probability.
# ================================================================


@dataclass
class Config:
    SYMBOLS: List[str] = field(default_factory=lambda: [
        "BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT"
    ])
    CAPITAL: float = 100.0
    RISK_PERCENT: float = 1.0
    REWARD_RISK: float = 3.0
    MIN_SCORE: float = 80.0
    EXCHANGE_ID: str = "binance"

    TIMEFRAMES: Dict[str, str] = field(default_factory=lambda: {
        "structure": "4h",
        "confirmation": "1h",
        "execution": "15m",
    })

    CANDLE_LIMIT: int = 500
    SWING_LEFT: int = 3
    SWING_RIGHT: int = 3
    ATR_PERIOD: int = 14
    EMA_PERIOD: int = 200
    EMA_SLOPE_LOOKBACK: int = 5

    EQ_TOLERANCE_ATR: float = 0.15
    DISPLACEMENT_ATR: float = 1.20
    MIN_BODY_RATIO: float = 0.55
    FVG_MIN_ATR: float = 0.10
    MAX_OB_AGE: int = 80
    SL_ATR_BUFFER: float = 0.25

    TELEGRAM_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    POLL_SECONDS: int = 60


CONFIG = Config()


# ================================================================
# .env
# ================================================================

def load_env(path=".env"):
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and k not in os.environ:
                    os.environ[k] = v
    except Exception as e:
        logging.getLogger("EXCORA").warning(".env error: %s", e)


load_env()
CONFIG.TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CONFIG.TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


# ================================================================
# LOGGING
# ================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            "excora_institutional_mtf.log",
            encoding="utf-8"
        ),
    ],
)
logger = logging.getLogger("EXCORA")


# ================================================================
# ENUMS / DATA
# ================================================================

class Trend(Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    RANGE = "RANGE"


class StructureEvent(Enum):
    NONE = "NONE"
    BOS_BULLISH = "BOS_BULLISH"
    BOS_BEARISH = "BOS_BEARISH"
    CHOCH_BULLISH = "CHoCH_BULLISH"
    CHOCH_BEARISH = "CHoCH_BEARISH"


class LiquidityType(Enum):
    BSL = "BUY_SIDE_LIQUIDITY"
    SSL = "SELL_SIDE_LIQUIDITY"


class OBState(Enum):
    FRESH = "FRESH"
    MITIGATED = "MITIGATED"
    INVALIDATED = "INVALIDATED"


@dataclass
class Swing:
    index: int
    price: float
    kind: str


@dataclass
class Structure:
    trend: Trend
    event: StructureEvent
    broken_level: Optional[float]
    highs: List[Swing]
    lows: List[Swing]


@dataclass
class EMAResult:
    value: float
    price: float
    trend: Trend
    slope: float


@dataclass
class LiquiditySweep:
    kind: LiquidityType
    level: float
    strength: float


@dataclass
class OrderBlock:
    direction: Trend
    index: int
    high: float
    low: float
    state: OBState
    displacement: float


@dataclass
class FVG:
    direction: Trend
    index: int
    high: float
    low: float
    strength: float
    filled: bool


@dataclass
class Signal:
    symbol: str
    side: str
    score: float
    entry: float
    sl: float
    tp: float
    quantity: float
    risk_amount: float
    rr: float
    trend_4h: Trend
    ema_4h: Trend
    trend_1h: Trend
    trend_15m: Trend
    event_1h: StructureEvent
    event_15m: StructureEvent
    liquidity: Optional[LiquiditySweep]
    ob: Optional[OrderBlock]
    fvg: Optional[FVG]
    zone: str
    reasons: List[str]
    blockers: List[str]
    valid: bool


# ================================================================
# QUANT TOOLS
# ================================================================

class Q:

    @staticmethod
    def atr(df, period=14):
        pc = df["close"].shift(1)
        tr = pd.concat([
            df["high"] - df["low"],
            (df["high"] - pc).abs(),
            (df["low"] - pc).abs()
        ], axis=1).max(axis=1)
        return tr.ewm(
            alpha=1 / period,
            adjust=False,
            min_periods=period
        ).mean()

    @staticmethod
    def body(row):
        return abs(float(row["close"]) - float(row["open"]))

    @staticmethod
    def body_ratio(row):
        rng = max(float(row["high"]) - float(row["low"]), 1e-12)
        return Q.body(row) / rng

    @staticmethod
    def displacement(row, atr):
        return Q.body(row) / atr if atr > 0 and np.isfinite(atr) else 0.0


# ================================================================
# MARKET DATA
# ================================================================

class MarketData:

    def __init__(self, cfg):
        cls = getattr(ccxt, cfg.EXCHANGE_ID)
        self.exchange = cls({
            "enableRateLimit": True,
            "timeout": 20000
        })

    def fetch(self, symbol, timeframe, limit):
        raw = self.exchange.fetch_ohlcv(
            symbol, timeframe=timeframe, limit=limit
        )
        if not raw:
            raise RuntimeError(f"No data: {symbol} {timeframe}")

        df = pd.DataFrame(raw, columns=[
            "timestamp", "open", "high", "low", "close", "volume"
        ])
        df["timestamp"] = pd.to_datetime(
            df["timestamp"], unit="ms", utc=True
        )
        cols = ["open", "high", "low", "close", "volume"]
        df[cols] = df[cols].astype(float)

        # Remove currently-forming candle.
        if len(df) > 2:
            df = df.iloc[:-1].copy()

        df = df.dropna().reset_index(drop=True)

        if len(df) < 250:
            raise RuntimeError(
                f"Insufficient closed candles: {symbol} {timeframe}: {len(df)}"
            )
        return df


# ================================================================
# EMA 200
# ================================================================

class EMA200:

    def __init__(self, cfg):
        self.cfg = cfg

    def analyze(self, df):
        ema = df["close"].ewm(
            span=self.cfg.EMA_PERIOD,
            adjust=False,
            min_periods=self.cfg.EMA_PERIOD
        ).mean()

        value = float(ema.iloc[-1])
        price = float(df["close"].iloc[-1])
        n = self.cfg.EMA_SLOPE_LOOKBACK

        old = float(ema.iloc[-1 - n]) if len(ema) > n else value
        slope = (value - old) / max(abs(old), 1e-12)

        if price > value and slope > 0:
            trend = Trend.BULLISH
        elif price < value and slope < 0:
            trend = Trend.BEARISH
        else:
            trend = Trend.RANGE

        return EMAResult(value, price, trend, slope)


# ================================================================
# MARKET STRUCTURE
# ================================================================

class MarketStructure:

    def __init__(self, cfg):
        self.cfg = cfg

    def swings(self, df):
        L, R = self.cfg.SWING_LEFT, self.cfg.SWING_RIGHT
        highs, lows = [], []

        for i in range(L, len(df) - R):
            h = float(df.iloc[i]["high"])
            l = float(df.iloc[i]["low"])

            if h > float(df.iloc[i-L:i]["high"].max()) and                h >= float(df.iloc[i+1:i+1+R]["high"].max()):
                highs.append(Swing(i, h, "HIGH"))

            if l < float(df.iloc[i-L:i]["low"].min()) and                l <= float(df.iloc[i+1:i+1+R]["low"].min()):
                lows.append(Swing(i, l, "LOW"))

        return highs, lows

    def analyze(self, df):
        highs, lows = self.swings(df)

        if len(highs) < 2 or len(lows) < 2:
            return Structure(
                Trend.RANGE, StructureEvent.NONE, None, highs, lows
            )

        ph, lh = highs[-2], highs[-1]
        pl, ll = lows[-2], lows[-1]
        close = float(df.iloc[-1]["close"])

        bull = lh.price > ph.price and ll.price > pl.price
        bear = lh.price < ph.price and ll.price < pl.price

        event = StructureEvent.NONE
        broken = None

        if close > lh.price:
            event = (
                StructureEvent.CHOCH_BULLISH
                if bear else StructureEvent.BOS_BULLISH
            )
            broken = lh.price

        elif close < ll.price:
            event = (
                StructureEvent.CHOCH_BEARISH
                if bull else StructureEvent.BOS_BEARISH
            )
            broken = ll.price

        trend = (
            Trend.BULLISH if bull
            else Trend.BEARISH if bear
            else Trend.RANGE
        )

        return Structure(trend, event, broken, highs, lows)


# ================================================================
# LIQUIDITY
# ================================================================

class Liquidity:

    def __init__(self, cfg):
        self.cfg = cfg

    def pools(self, df, structure):
        atr = float(Q.atr(df, self.cfg.ATR_PERIOD).iloc[-1])
        if not np.isfinite(atr) or atr <= 0:
            return []

        tol = atr * self.cfg.EQ_TOLERANCE_ATR
        pools = []

        for a, b in zip(structure.highs[:-1], structure.highs[1:]):
            if abs(a.price - b.price) <= tol:
                pools.append((LiquidityType.BSL, (a.price + b.price) / 2))

        for a, b in zip(structure.lows[:-1], structure.lows[1:]):
            if abs(a.price - b.price) <= tol:
                pools.append((LiquidityType.SSL, (a.price + b.price) / 2))

        return pools

    def sweep(self, df, pools):
        if not pools:
            return None

        atr = float(Q.atr(df, self.cfg.ATR_PERIOD).iloc[-1])
        if not np.isfinite(atr) or atr <= 0:
            return None

        c = df.iloc[-1]
        candidates = []

        for kind, level in pools:
            if kind == LiquidityType.BSL:
                if float(c["high"]) > level and float(c["close"]) < level:
                    strength = (float(c["high"]) - level) / atr
                    candidates.append(
                        LiquiditySweep(kind, level, min(strength, 5.0))
                    )

            else:
                if float(c["low"]) < level and float(c["close"]) > level:
                    strength = (level - float(c["low"])) / atr
                    candidates.append(
                        LiquiditySweep(kind, level, min(strength, 5.0))
                    )

        return max(candidates, key=lambda x: x.strength) if candidates else None


# ================================================================
# ORDER BLOCK
# ================================================================

class OrderBlocks:

    def __init__(self, cfg):
        self.cfg = cfg

    def detect(self, df, structure):
        atrs = Q.atr(df, self.cfg.ATR_PERIOD)
        start = max(0, len(df) - self.cfg.MAX_OB_AGE)

        for i in range(len(df) - 2, start - 1, -1):
            c = df.iloc[i]
            d = df.iloc[i + 1]
            atr = float(atrs.iloc[i])

            if not np.isfinite(atr) or atr <= 0:
                continue

            disp = Q.displacement(d, atr)

            if disp < self.cfg.DISPLACEMENT_ATR:
                continue
            if Q.body_ratio(d) < self.cfg.MIN_BODY_RATIO:
                continue

            if (
                float(c["close"]) < float(c["open"])
                and float(d["close"]) > float(d["open"])
                and structure.event in (
                    StructureEvent.BOS_BULLISH,
                    StructureEvent.CHOCH_BULLISH
                )
            ):
                ob = OrderBlock(
                    Trend.BULLISH, i,
                    float(c["high"]), float(c["low"]),
                    OBState.FRESH, disp
                )
                return self.state(df, ob)

            if (
                float(c["close"]) > float(c["open"])
                and float(d["close"]) < float(d["open"])
                and structure.event in (
                    StructureEvent.BOS_BEARISH,
                    StructureEvent.CHOCH_BEARISH
                )
            ):
                ob = OrderBlock(
                    Trend.BEARISH, i,
                    float(c["high"]), float(c["low"]),
                    OBState.FRESH, disp
                )
                return self.state(df, ob)

        return None

    @staticmethod
    def state(df, ob):
        future = df.iloc[ob.index + 1:]
        if future.empty:
            return ob

        if ob.direction == Trend.BULLISH:
            if (future["close"] < ob.low).any():
                ob.state = OBState.INVALIDATED
            elif (
                (future["low"] <= ob.high)
                & (future["high"] >= ob.low)
            ).any():
                ob.state = OBState.MITIGATED

        else:
            if (future["close"] > ob.high).any():
                ob.state = OBState.INVALIDATED
            elif (
                (future["high"] >= ob.low)
                & (future["low"] <= ob.high)
            ).any():
                ob.state = OBState.MITIGATED

        return ob


# ================================================================
# FVG
# ================================================================

class FVGEngine:

    def __init__(self, cfg):
        self.cfg = cfg

    def detect(self, df):
        atr = float(Q.atr(df, self.cfg.ATR_PERIOD).iloc[-1])
        if not np.isfinite(atr) or atr <= 0:
            return None

        for i in range(len(df) - 2, 1, -1):
            left = df.iloc[i - 1]
            right = df.iloc[i + 1]

            bull_size = float(right["low"]) - float(left["high"])
            if bull_size > 0 and bull_size >= atr * self.cfg.FVG_MIN_ATR:
                later = df.iloc[i + 2:]
                filled = (
                    bool((later["low"] <= float(left["high"])).any())
                    if not later.empty else False
                )
                return FVG(
                    Trend.BULLISH, i,
                    float(right["low"]), float(left["high"]),
                    bull_size / atr, filled
                )

            bear_size = float(left["low"]) - float(right["high"])
            if bear_size > 0 and bear_size >= atr * self.cfg.FVG_MIN_ATR:
                later = df.iloc[i + 2:]
                filled = (
                    bool((later["high"] >= float(right["high"])).any())
                    if not later.empty else False
                )
                return FVG(
                    Trend.BEARISH, i,
                    float(left["low"]), float(right["high"]),
                    bear_size / atr, filled
                )

        return None


# ================================================================
# PREMIUM / DISCOUNT + VOLUME
# ================================================================

def premium_discount(df, lookback=100):
    w = df.tail(lookback)
    hi, lo = float(w["high"].max()), float(w["low"].min())
    mid = (hi + lo) / 2
    price = float(df.iloc[-1]["close"])

    if price < mid:
        return "DISCOUNT"
    if price > mid:
        return "PREMIUM"
    return "EQUILIBRIUM"


def volume_zscore(df, period=50):
    v = df["volume"]
    mean = v.rolling(period).mean().iloc[-1]
    std = v.rolling(period).std().iloc[-1]

    if not np.isfinite(std) or std <= 0:
        return 0.0
    return float((v.iloc[-1] - mean) / std)


# ================================================================
# SCORE
# ================================================================

class ScoreEngine:

    # Maximum theoretical score = 100.
    # 4H EMA/trend       15
    # 4H structure       10
    # 1H confirmation    15
    # MTF alignment      10
    # 1H/15M structure   10
    # liquidity          10
    # order block         7
    # FVG                 4
    # premium/discount    2
    # displacement        2
    # volume              5
    # --------------------
    # total              100

    def __init__(self, cfg):
        self.cfg = cfg

    def calculate(
        self, s4, s1, s15, ema,
        sweep, ob, fvg, zone, df15
    ):
        buy = sell = 0.0
        br, sr = [], []

        if ema.trend == Trend.BULLISH:
            buy += 15
            br.append("4H EMA200 bullish")
        elif ema.trend == Trend.BEARISH:
            sell += 15
            sr.append("4H EMA200 bearish")

        if s4.trend == Trend.BULLISH:
            buy += 10
            br.append("4H bullish structure")
        elif s4.trend == Trend.BEARISH:
            sell += 10
            sr.append("4H bearish structure")

        if s1.trend == Trend.BULLISH:
            buy += 15
            br.append("1H bullish confirmation")
        elif s1.trend == Trend.BEARISH:
            sell += 15
            sr.append("1H bearish confirmation")

        if (
            ema.trend == s4.trend == s1.trend == Trend.BULLISH
        ):
            buy += 10
            br.append("4H/1H full bullish alignment")

        elif (
            ema.trend == s4.trend == s1.trend == Trend.BEARISH
        ):
            sell += 10
            sr.append("4H/1H full bearish alignment")

        bull_events = (
            StructureEvent.BOS_BULLISH,
            StructureEvent.CHOCH_BULLISH
        )
        bear_events = (
            StructureEvent.BOS_BEARISH,
            StructureEvent.CHOCH_BEARISH
        )

        if s1.event in bull_events:
            buy += 10
            br.append("1H " + s1.event.value)
        elif s1.event in bear_events:
            sell += 10
            sr.append("1H " + s1.event.value)
        elif s15.event in bull_events:
            buy += 5
            br.append("15M " + s15.event.value)
        elif s15.event in bear_events:
            sell += 5
            sr.append("15M " + s15.event.value)

        if sweep:
            if sweep.kind == LiquidityType.SSL:
                buy += min(10, 5 + sweep.strength)
                br.append("15M sell-side liquidity sweep")
            else:
                sell += min(10, 5 + sweep.strength)
                sr.append("15M buy-side liquidity sweep")

        if ob and ob.state != OBState.INVALIDATED:
            if ob.direction == Trend.BULLISH:
                buy += 7
                br.append("15M bullish Order Block")
            else:
                sell += 7
                sr.append("15M bearish Order Block")

        if fvg and not fvg.filled:
            if fvg.direction == Trend.BULLISH:
                buy += 4
                br.append("15M unfilled bullish FVG")
            else:
                sell += 4
                sr.append("15M unfilled bearish FVG")

        if zone == "DISCOUNT":
            buy += 2
            br.append("15M discount")
        elif zone == "PREMIUM":
            sell += 2
            sr.append("15M premium")

        atr = float(Q.atr(df15, self.cfg.ATR_PERIOD).iloc[-1])
        c = df15.iloc[-1]
        disp = Q.displacement(c, atr)

        if (
            float(c["close"]) > float(c["open"])
            and disp >= self.cfg.DISPLACEMENT_ATR
            and Q.body_ratio(c) >= self.cfg.MIN_BODY_RATIO
        ):
            buy += 2
            br.append("15M bullish displacement")

        elif (
            float(c["close"]) < float(c["open"])
            and disp >= self.cfg.DISPLACEMENT_ATR
            and Q.body_ratio(c) >= self.cfg.MIN_BODY_RATIO
        ):
            sell += 2
            sr.append("15M bearish displacement")

        vz = volume_zscore(df15)
        if vz >= 1.0:
            if buy > sell:
                buy += 5
                br.append("15M abnormal volume")
            elif sell > buy:
                sell += 5
                sr.append("15M abnormal volume")

        if buy > sell:
            return min(buy, 100), "BUY", br
        if sell > buy:
            return min(sell, 100), "SELL", sr
        return 0.0, "WAIT", []


# ================================================================
# RISK
# ================================================================

class RiskEngine:

    def __init__(self, cfg):
        self.cfg = cfg

    def calculate(self, side, entry, df, ob, sweep):
        atr = float(Q.atr(df, self.cfg.ATR_PERIOD).iloc[-1])
        if not np.isfinite(atr) or atr <= 0 or entry <= 0:
            return None

        recent = df.tail(20)

        if side == "BUY":
            candidates = [float(recent["low"].min())]
            if ob and ob.direction == Trend.BULLISH:
                candidates.append(ob.low)
            if sweep and sweep.kind == LiquidityType.SSL:
                candidates.append(sweep.level)

            sl = min(candidates) - atr * self.cfg.SL_ATR_BUFFER
            if sl >= entry:
                return None

            distance = entry - sl
            tp = entry + distance * self.cfg.REWARD_RISK

        elif side == "SELL":
            candidates = [float(recent["high"].max())]
            if ob and ob.direction == Trend.BEARISH:
                candidates.append(ob.high)
            if sweep and sweep.kind == LiquidityType.BSL:
                candidates.append(sweep.level)

            sl = max(candidates) + atr * self.cfg.SL_ATR_BUFFER
            if sl <= entry:
                return None

            distance = sl - entry
            tp = entry - distance * self.cfg.REWARD_RISK

        else:
            return None

        if distance <= 0:
            return None

        risk_amount = self.cfg.CAPITAL * self.cfg.RISK_PERCENT / 100
        qty = risk_amount / distance

        if not np.isfinite(qty) or qty <= 0:
            return None

        return float(sl), float(tp), float(qty), float(risk_amount)


# ================================================================
# SIGNAL ENGINE
# ================================================================

class SignalEngine:

    def __init__(self, cfg):
        self.cfg = cfg
        self.ms = MarketStructure(cfg)
        self.ema = EMA200(cfg)
        self.liq = Liquidity(cfg)
        self.ob = OrderBlocks(cfg)
        self.fvg = FVGEngine(cfg)
        self.score = ScoreEngine(cfg)
        self.risk = RiskEngine(cfg)

    def analyze(self, symbol, data):
        df4 = data["4h"]
        df1 = data["1h"]
        df15 = data["15m"]

        s4 = self.ms.analyze(df4)
        s1 = self.ms.analyze(df1)
        s15 = self.ms.analyze(df15)
        ema = self.ema.analyze(df4)

        pools = self.liq.pools(df15, s15)
        sweep = self.liq.sweep(df15, pools)
        ob = self.ob.detect(df15, s15)
        fvg = self.fvg.detect(df15)
        zone = premium_discount(df15)

        score, side, reasons = self.score.calculate(
            s4, s1, s15, ema, sweep, ob, fvg, zone, df15
        )

        blockers = []

        # STRICT DIRECTION GATE:
        # 4H EMA + 4H structure + 1H confirmation must agree.
        if side == "BUY":
            if not (
                ema.trend == Trend.BULLISH
                and s4.trend == Trend.BULLISH
                and s1.trend == Trend.BULLISH
            ):
                blockers.append("4H/1H bullish alignment incomplete")
                side = "WAIT"

        elif side == "SELL":
            if not (
                ema.trend == Trend.BEARISH
                and s4.trend == Trend.BEARISH
                and s1.trend == Trend.BEARISH
            ):
                blockers.append("4H/1H bearish alignment incomplete")
                side = "WAIT"

        if score < self.cfg.MIN_SCORE:
            blockers.append(
                f"score {score:.2f} < {self.cfg.MIN_SCORE:.2f}"
            )
            side = "WAIT"

        entry = float(df15.iloc[-1]["close"])
        sl = tp = qty = 0.0
        risk_amount = self.cfg.CAPITAL * self.cfg.RISK_PERCENT / 100

        if side in ("BUY", "SELL"):
            risk = self.risk.calculate(
                side, entry, df15, ob, sweep
            )
            if risk is None:
                blockers.append("invalid risk/SL geometry")
                side = "WAIT"
            else:
                sl, tp, qty, risk_amount = risk

        valid = (
            side in ("BUY", "SELL")
            and score >= self.cfg.MIN_SCORE
            and sl > 0 and tp > 0 and qty > 0
        )

        return Signal(
            symbol=symbol,
            side=side,
            score=float(score),
            entry=entry,
            sl=sl,
            tp=tp,
            quantity=qty,
            risk_amount=risk_amount,
            rr=self.cfg.REWARD_RISK,
            trend_4h=s4.trend,
            ema_4h=ema.trend,
            trend_1h=s1.trend,
            trend_15m=s15.trend,
            event_1h=s1.event,
            event_15m=s15.event,
            liquidity=sweep,
            ob=ob,
            fvg=fvg,
            zone=zone,
            reasons=reasons,
            blockers=blockers,
            valid=valid
        )


# ================================================================
# TELEGRAM
# ================================================================

class Telegram:

    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id

    def enabled(self):
        return bool(self.token and self.chat_id)

    def send(self, text):
        if not self.enabled():
            logger.warning("Telegram is DISABLED")
            return False

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"

        try:
            r = requests.post(
                url,
                data={"chat_id": self.chat_id, "text": text},
                timeout=15
            )
            r.raise_for_status()
            data = r.json()
            return bool(data.get("ok"))
        except Exception as e:
            logger.error("Telegram error: %s", e)
            return False


# ================================================================
# FORMAT
# ================================================================

def fmt_price(x):
    if x <= 0:
        return "0"
    if x >= 1000:
        return f"{x:.2f}"
    if x >= 1:
        return f"{x:.4f}"
    return f"{x:.8f}"


def format_signal(s, cfg):
    icon = "🟢" if s.side == "BUY" else "🔴" if s.side == "SELL" else "⚪"

    lines = [
        "══════════════════════════════",
        "     EXCORA INSTITUTIONAL MTF",
        "══════════════════════════════",
        f"Symbol : {s.symbol}",
        f"Signal : {icon} {s.side}",
        f"Score  : {s.score:.2f}/100",
        "",
        "── MULTI TIMEFRAME ──",
        f"4H Trend    : {s.trend_4h.value}",
        f"4H EMA200   : {s.ema_4h.value}",
        f"1H Confirm  : {s.trend_1h.value}",
        f"1H Event    : {s.event_1h.value}",
        f"15M Execute : {s.trend_15m.value}",
        f"15M Event   : {s.event_15m.value}",
        "",
        "── SMART MONEY ──",
        f"Zone        : {s.zone}",
    ]

    if s.liquidity:
        lines += [
            f"Liquidity   : {s.liquidity.kind.value}",
            f"Sweep Level : {fmt_price(s.liquidity.level)}",
            f"Sweep Power : {s.liquidity.strength:.2f} ATR",
        ]
    else:
        lines.append("Liquidity   : NONE")

    if s.ob:
        lines += [
            f"Order Block : {s.ob.direction.value}",
            f"OB State    : {s.ob.state.value}",
            f"OB Zone     : {fmt_price(s.ob.low)} - {fmt_price(s.ob.high)}",
            f"OB Displace : {s.ob.displacement:.2f} ATR",
        ]
    else:
        lines.append("Order Block : NONE")

    if s.fvg:
        lines += [
            f"FVG         : {s.fvg.direction.value}",
            f"FVG State   : {'FILLED' if s.fvg.filled else 'UNFILLED'}",
            f"FVG Strength: {s.fvg.strength:.2f} ATR",
        ]
    else:
        lines.append("FVG         : NONE")

    lines += [
        "",
        "── RISK ENGINE ──",
        f"Capital     : ${cfg.CAPITAL:.2f}",
        f"Risk        : {cfg.RISK_PERCENT:.2f}%",
        f"Risk Amount : ${s.risk_amount:.2f}",
        f"Entry       : {fmt_price(s.entry)}",
        f"Stop Loss   : {fmt_price(s.sl)}",
        f"Take Profit : {fmt_price(s.tp)}",
        f"Position    : {s.quantity:.8f}",
        f"RR          : 1:{s.rr:.1f}",
        "",
        "── CONFLUENCE ──",
    ]

    lines += [f"✓ {x}" for x in s.reasons]

    if not s.valid and s.blockers:
        lines += ["", "── BLOCKERS ──"]
        lines += [f"• {x}" for x in s.blockers]

    lines += [
        "",
        "══════════════════════════════",
        "EXCORA STATUS: " + ("VALID SIGNAL" if s.valid else "WAIT"),
        "══════════════════════════════",
    ]
    return "\n".join(lines)


# ================================================================
# MAIN ENGINE
# ================================================================

class EXCORA:

    def __init__(self, cfg):
        self.cfg = cfg
        self.market = MarketData(cfg)
        self.engine = SignalEngine(cfg)
        self.telegram = Telegram(
            cfg.TELEGRAM_TOKEN,
            cfg.TELEGRAM_CHAT_ID
        )
        self.last_signal = {}

        logger.info("Symbols: %s", ", ".join(cfg.SYMBOLS))
        logger.info(
            "Telegram: %s",
            "ENABLED" if self.telegram.enabled() else "DISABLED"
        )

    def analyze_symbol(self, symbol):
        raw = {}

        for key, tf in self.cfg.TIMEFRAMES.items():
            raw[key] = self.market.fetch(
                symbol, tf, self.cfg.CANDLE_LIMIT
            )

        # Explicit names prevent the previous KeyError('1d').
        data = {
            "4h": raw["structure"],
            "1h": raw["confirmation"],
            "15m": raw["execution"],
        }

        return self.engine.analyze(symbol, data)

    def process(self, symbol):
        try:
            s = self.analyze_symbol(symbol)

            logger.info(
                "%s | %s | score=%.2f | 4H=%s | EMA200=%s | "
                "1H=%s | 15M=%s",
                symbol, s.side, s.score,
                s.trend_4h.value,
                s.ema_4h.value,
                s.trend_1h.value,
                s.trend_15m.value
            )

            if s.valid:
                key = (
                    s.symbol, s.side, round(s.entry, 8),
                    s.event_1h.value, round(s.score, 2)
                )

                if self.last_signal.get(symbol) == key:
                    logger.info("%s | duplicate ignored", symbol)
                    return s

                msg = format_signal(s, self.cfg)

                if self.telegram.send(msg):
                    logger.info("%s | Telegram signal sent", symbol)

                self.last_signal[symbol] = key

            return s

        except Exception as e:
            logger.exception(
                "%s | analysis failed: %s", symbol, e
            )
            return None

    def run_once(self):
        for symbol in self.cfg.SYMBOLS:
            self.process(symbol)
            time.sleep(0.3)

    def run_forever(self):
        logger.info("=" * 52)
        logger.info("EXCORA INSTITUTIONAL MTF STARTED")
        logger.info(
            "Capital=%.2f | Risk=%.2f%% | RR=1:%.1f | MinScore=%.1f",
            self.cfg.CAPITAL,
            self.cfg.RISK_PERCENT,
            self.cfg.REWARD_RISK,
            self.cfg.MIN_SCORE
        )
        logger.info(
            "4H=Trend+EMA200 | 1H=Structure Confirmation | "
            "15M=Execution"
        )
        logger.info("=" * 52)

        while True:
            try:
                self.run_once()
            except KeyboardInterrupt:
                logger.info("EXCORA stopped manually")
                break
            except Exception as e:
                logger.exception("Main loop error: %s", e)

            time.sleep(self.cfg.POLL_SECONDS)


# ================================================================
# VALIDATION
# ================================================================

def validate(cfg):
    if cfg.CAPITAL <= 0:
        raise ValueError("CAPITAL must be > 0")

    if not 0 < cfg.RISK_PERCENT <= 2:
        raise ValueError("RISK_PERCENT must be > 0 and <= 2")

    if cfg.REWARD_RISK < 3:
        raise ValueError("REWARD_RISK must be >= 3")

    if not 0 <= cfg.MIN_SCORE <= 100:
        raise ValueError("MIN_SCORE must be between 0 and 100")

    if cfg.CANDLE_LIMIT < cfg.EMA_PERIOD + 50:
        raise ValueError("CANDLE_LIMIT is too small for EMA200")


if __name__ == "__main__":
    validate(CONFIG)
    EXCORA(CONFIG).run_forever()
