from __future__ import annotations
import os, time, logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Tuple

import ccxt
import numpy as np
import pandas as pd
import requests

# ============================================================
# EXCORA INSTITUTIONAL SMC - FINAL CLEAN VERSION
# 1D  = macro direction + EMA200
# 4H  = primary institutional structure + BOS/CHoCH
# 1H  = confirmation
# 15M = execution: liquidity sweep + displacement + OB/FVG
# Risk = 1% default, 2% maximum, RR >= 3:1
# Only CLOSED candles are analyzed. Score != win probability.
# ============================================================

def load_env(path=".env"):
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k,v=line.split("=",1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

load_env()

@dataclass
class Config:
    SYMBOLS: List[str] = field(default_factory=lambda: [
        "BTC/USDT","ETH/USDT","SOL/USDT","XRP/USDT"
    ])
    CAPITAL: float = 100.0
    RISK_PERCENT: float = 1.0
    MAX_RISK_PERCENT: float = 2.0
    REWARD_RISK: float = 3.0
    MIN_SCORE: float = 80.0
    CANDLE_LIMIT: int = 500
    EMA_PERIOD: int = 200
    ATR_PERIOD: int = 14
    SWING_LEFT: int = 3
    SWING_RIGHT: int = 3
    BREAK_ATR_MIN: float = 0.10
    DISPLACEMENT_ATR: float = 1.20
    MIN_BODY_RATIO: float = 0.55
    EQ_TOLERANCE_ATR: float = 0.15
    MAX_OB_AGE: int = 100
    FVG_MIN_ATR: float = 0.10
    SL_ATR_BUFFER: float = 0.25
    MIN_STOP_ATR: float = 0.20
    MAX_STOP_ATR: float = 6.0
    POLL_SECONDS: int = 60
    TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN","")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID","")
    TIMEFRAMES: Dict[str,str] = field(default_factory=lambda:{
        "macro":"1d","structure":"4h","confirmation":"1h","execution":"15m"
    })

CFG=Config()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(),
              logging.FileHandler("excora_institutional_smc.log",encoding="utf-8")]
)
log=logging.getLogger("EXCORA")

class Trend(Enum):
    BULLISH="BULLISH"; BEARISH="BEARISH"; RANGE="RANGE"

class Event(Enum):
    NONE="NONE"; BOS_BULLISH="BOS_BULLISH"; BOS_BEARISH="BOS_BEARISH"
    CHOCH_BULLISH="CHoCH_BULLISH"; CHOCH_BEARISH="CHoCH_BEARISH"

class Liq(Enum):
    BSL="BUY_SIDE_LIQUIDITY"; SSL="SELL_SIDE_LIQUIDITY"

class OBState(Enum):
    FRESH="FRESH"; MITIGATED="MITIGATED"; INVALIDATED="INVALIDATED"

@dataclass
class Swing:
    index:int; price:float; kind:str; strength:float

@dataclass
class Structure:
    trend:Trend
    event:Event
    broken:Optional[float]
    highs:List[Swing]
    lows:List[Swing]
    protected_high:Optional[float]
    protected_low:Optional[float]
    break_strength:float

@dataclass
class Pool:
    kind:Liq; price:float; strength:float

@dataclass
class Sweep:
    kind:Liq; level:float; strength:float

@dataclass
class OrderBlock:
    direction:Trend; index:int; high:float; low:float
    state:OBState; displacement:float; quality:float

@dataclass
class FVG:
    direction:Trend; index:int; high:float; low:float
    size:float; filled:bool; strength:float

@dataclass
class Signal:
    symbol:str; side:str; score:float
    entry:float; sl:float; tp:float; qty:float; risk:float
    macro:Trend; ema:Trend; h4:Trend; h1:Trend; m15:Trend
    e4:Event; e1:Event; e15:Event
    sweep:Optional[Sweep]; ob:Optional[OrderBlock]; fvg:Optional[FVG]
    reasons:List[str]; valid:bool
    @property
    def rr(self): return CFG.REWARD_RISK

class Q:
    @staticmethod
    def atr(df,n=14):
        pc=df.close.shift(1)
        tr=pd.concat([df.high-df.low,(df.high-pc).abs(),(df.low-pc).abs()],axis=1).max(axis=1)
        return tr.ewm(alpha=1/n,adjust=False,min_periods=n).mean()

    @staticmethod
    def body_ratio(r):
        return abs(float(r.close)-float(r.open))/max(float(r.high-r.low),1e-12)

    @staticmethod
    def disp(r,atr):
        return abs(float(r.close)-float(r.open))/max(float(atr),1e-12)

class Data:
    def __init__(self,cfg):
        cls=getattr(ccxt,"binance")
        self.ex=cls({"enableRateLimit":True,"options":{"defaultType":"spot"}})
    def fetch(self,symbol,tf,limit):
        raw=self.ex.fetch_ohlcv(symbol,timeframe=tf,limit=limit)
        if not raw: raise RuntimeError(f"No data: {symbol} {tf}")
        df=pd.DataFrame(raw,columns=["timestamp","open","high","low","close","volume"])
        df.timestamp=pd.to_datetime(df.timestamp,unit="ms",utc=True)
        for c in ["open","high","low","close","volume"]: df[c]=df[c].astype(float)
        if len(df)>2: df=df.iloc[:-1]
        df=df.dropna().reset_index(drop=True)
        if len(df)<max(50,CFG.ATR_PERIOD+10):
            raise RuntimeError(f"Not enough closed candles: {symbol} {tf}")
        return df

class StructureEngine:
    def __init__(self,cfg): self.cfg=cfg
    def swings(self,df):
        hs=[]; ls=[]; L=self.cfg.SWING_LEFT; R=self.cfg.SWING_RIGHT
        atr=Q.atr(df,self.cfg.ATR_PERIOD)
        for i in range(L,len(df)-R):
            h=float(df.high.iloc[i]); l=float(df.low.iloc[i])
            lh=float(df.high.iloc[i-L:i].max()); rh=float(df.high.iloc[i+1:i+1+R].max())
            ll=float(df.low.iloc[i-L:i].min()); rl=float(df.low.iloc[i+1:i+1+R].min())
            a=max(float(atr.iloc[i]) if np.isfinite(atr.iloc[i]) else 0,1e-12)
            if h>lh and h>=rh: hs.append(Swing(i,h,"HIGH",max(0,(h-max(lh,rh))/a)))
            if l<ll and l<=rl: ls.append(Swing(i,l,"LOW",max(0,(min(ll,rl)-l)/a)))
        return hs,ls
    def analyze(self,df):
        hs,ls=self.swings(df)
        if len(hs)<2 or len(ls)<2:
            return Structure(Trend.RANGE,Event.NONE,None,hs,ls,None,None,0)
        hh=hs[-1].price>hs[-2].price; hl=ls[-1].price>ls[-2].price
        lh=hs[-1].price<hs[-2].price; ll=ls[-1].price<ls[-2].price
        trend=Trend.BULLISH if hh and hl else Trend.BEARISH if lh and ll else Trend.RANGE
        close=float(df.close.iloc[-1]); atr=float(Q.atr(df,self.cfg.ATR_PERIOD).iloc[-1])
        event=Event.NONE; broken=None; strength=0
        if np.isfinite(atr) and atr>0:
            up=(close-hs[-1].price)/atr
            dn=(ls[-1].price-close)/atr
            if up>=self.cfg.BREAK_ATR_MIN:
                event=Event.CHOCH_BULLISH if trend==Trend.BEARISH else Event.BOS_BULLISH
                broken=hs[-1].price; strength=up
            elif dn>=self.cfg.BREAK_ATR_MIN:
                event=Event.CHOCH_BEARISH if trend==Trend.BULLISH else Event.BOS_BEARISH
                broken=ls[-1].price; strength=dn
        return Structure(trend,event,broken,hs,ls,hs[-1].price,ls[-1].price,float(strength))

class LiquidityEngine:
    def __init__(self,cfg): self.cfg=cfg
    def pools(self,df,s):
        atr=float(Q.atr(df,self.cfg.ATR_PERIOD).iloc[-1])
        if not np.isfinite(atr) or atr<=0:return []
        tol=atr*self.cfg.EQ_TOLERANCE_ATR; out=[]
        for a,b in zip(s.highs[:-1],s.highs[1:]):
            if abs(a.price-b.price)<=tol:
                out.append(Pool(Liq.BSL,(a.price+b.price)/2,1+min(a.strength+b.strength,4)))
        for a,b in zip(s.lows[:-1],s.lows[1:]):
            if abs(a.price-b.price)<=tol:
                out.append(Pool(Liq.SSL,(a.price+b.price)/2,1+min(a.strength+b.strength,4)))
        return out
    def sweep(self,df,pools):
        if not pools:return None
        r=df.iloc[-1]; atr=float(Q.atr(df,self.cfg.ATR_PERIOD).iloc[-1])
        cand=[]
        for p in pools:
            if p.kind==Liq.BSL and r.high>p.price and r.close<p.price:
                cand.append(Sweep(Liq.BSL,p.price,min(10,(r.high-p.price)/max(atr,1e-12)+p.strength)))
            if p.kind==Liq.SSL and r.low<p.price and r.close>p.price:
                cand.append(Sweep(Liq.SSL,p.price,min(10,(p.price-r.low)/max(atr,1e-12)+p.strength)))
        return max(cand,key=lambda x:x.strength) if cand else None

class OBEngine:
    def __init__(self,cfg): self.cfg=cfg
    def detect(self,df,s):
        atr=Q.atr(df,self.cfg.ATR_PERIOD)
        for i in range(len(df)-2,max(1,len(df)-self.cfg.MAX_OB_AGE),-1):
            r=df.iloc[i]; nxt=df.iloc[i+1]; a=float(atr.iloc[i])
            if not np.isfinite(a) or a<=0:continue
            d=Q.disp(nxt,a)
            if d<self.cfg.DISPLACEMENT_ATR or Q.body_ratio(nxt)<self.cfg.MIN_BODY_RATIO:continue
            if r.close<r.open and nxt.close>nxt.open and s.event in (Event.BOS_BULLISH,Event.CHOCH_BULLISH):
                ob=OrderBlock(Trend.BULLISH,i,float(r.high),float(r.low),OBState.FRESH,d,0)
            elif r.close>r.open and nxt.close<nxt.open and s.event in (Event.BOS_BEARISH,Event.CHOCH_BEARISH):
                ob=OrderBlock(Trend.BEARISH,i,float(r.high),float(r.low),OBState.FRESH,d,0)
            else:continue
            future=df.iloc[i+1:]
            if ob.direction==Trend.BULLISH:
                if (future.close<ob.low).any():ob.state=OBState.INVALIDATED
                elif ((future.low<=ob.high)&(future.high>=ob.low)).any():ob.state=OBState.MITIGATED
            else:
                if (future.close>ob.high).any():ob.state=OBState.INVALIDATED
                elif ((future.high>=ob.low)&(future.low<=ob.high)).any():ob.state=OBState.MITIGATED
            freshness=max(0,1-(len(df)-1-i)/max(self.cfg.MAX_OB_AGE,1))
            ob.quality=100*(.35*freshness+.40*min(d/3,1)+.25*({"FRESH":1,"MITIGATED":.65,"INVALIDATED":0}[ob.state.value]))
            return ob
        return None

class FVGEngine:
    def __init__(self,cfg):self.cfg=cfg
    def detect(self,df):
        atr=float(Q.atr(df,self.cfg.ATR_PERIOD).iloc[-1])
        if not np.isfinite(atr) or atr<=0:return None
        for i in range(len(df)-2,1,-1):
            a=df.iloc[i-1];m=df.iloc[i];b=df.iloc[i+1]
            size=float(b.low-a.high)
            if size>0 and size>=atr*self.cfg.FVG_MIN_ATR and m.close>m.open:
                filled=(df.iloc[i+2:].low<=a.high).any()
                return FVG(Trend.BULLISH,i,float(b.low),float(a.high),size,bool(filled),size/atr)
            size=float(a.low-b.high)
            if size>0 and size>=atr*self.cfg.FVG_MIN_ATR and m.close<m.open:
                filled=(df.iloc[i+2:].high>=b.high).any()
                return FVG(Trend.BEARISH,i,float(a.low),float(b.high),size,bool(filled),size/atr)
        return None

class MacroEngine:
    def __init__(self,cfg):self.cfg=cfg
    def ema_bias(self,df):
        ema=df.close.ewm(span=self.cfg.EMA_PERIOD,adjust=False,min_periods=self.cfg.EMA_PERIOD).mean()
        if len(df)<self.cfg.EMA_PERIOD+3:return Trend.RANGE
        now=float(ema.iloc[-1]); prev=float(ema.iloc[-4]); price=float(df.close.iloc[-1])
        if price>now and now>prev:return Trend.BULLISH
        if price<now and now<prev:return Trend.BEARISH
        return Trend.RANGE

class ScoreEngine:
    def score(self,macro,ema,h4,h1,m15,sweep,ob,fvg,zone,df):
        buy=sell=0.; br=[]; sr=[]
        def add(cond,pts,bmsg,smsg):
            nonlocal buy,sell
            if cond==1:buy+=pts;br.append(bmsg)
            elif cond==-1:sell+=pts;sr.append(smsg)
        add(1 if macro==Trend.BULLISH else -1 if macro==Trend.BEARISH else 0,15,"1D bullish structure","1D bearish structure")
        add(1 if ema==Trend.BULLISH else -1 if ema==Trend.BEARISH else 0,10,"EMA200 bullish","EMA200 bearish")
        add(1 if h4.trend==Trend.BULLISH else -1 if h4.trend==Trend.BEARISH else 0,20,"4H bullish structure","4H bearish structure")
        add(1 if h4.event in (Event.BOS_BULLISH,Event.CHOCH_BULLISH) else -1 if h4.event in (Event.BOS_BEARISH,Event.CHOCH_BEARISH) else 0,15,"4H bullish break","4H bearish break")
        add(1 if h1.trend==Trend.BULLISH else -1 if h1.trend==Trend.BEARISH else 0,15,"1H bullish confirmation","1H bearish confirmation")
        add(1 if sweep and sweep.kind==Liq.SSL else -1 if sweep and sweep.kind==Liq.BSL else 0,10,"15M SSL sweep","15M BSL sweep")
        atr=float(Q.atr(df,self.cfg.ATR_PERIOD).iloc[-1]) if hasattr(self,'cfg') else float(Q.atr(df,14).iloc[-1])
        r=df.iloc[-1]
        d=Q.disp(r,atr)
        add(1 if r.close>r.open and d>=1.2 and Q.body_ratio(r)>=.55 else -1 if r.close<r.open and d>=1.2 and Q.body_ratio(r)>=.55 else 0,5,"15M bullish displacement","15M bearish displacement")
        add(1 if ob and ob.direction==Trend.BULLISH and ob.state!=OBState.INVALIDATED else -1 if ob and ob.direction==Trend.BEARISH and ob.state!=OBState.INVALIDATED else 0,5,"Bullish OB","Bearish OB")
        add(1 if fvg and not fvg.filled and fvg.direction==Trend.BULLISH else -1 if fvg and not fvg.filled and fvg.direction==Trend.BEARISH else 0,3,"Bullish FVG","Bearish FVG")
        add(1 if zone=="DISCOUNT" else -1 if zone=="PREMIUM" else 0,2,"Discount","Premium")
        if buy>sell:return min(buy,100),br,"BUY"
        if sell>buy:return min(sell,100),sr,"SELL"
        return 0,[],"WAIT"

class RiskEngine:
    def __init__(self,cfg):self.cfg=cfg
    def calculate(self,side,entry,df,ob,sweep):
        atr=float(Q.atr(df,self.cfg.ATR_PERIOD).iloc[-1])
        if not np.isfinite(atr) or atr<=0:return None
        if side=="BUY":
            levels=[float(df.low.tail(20).min())]
            if ob and ob.direction==Trend.BULLISH:levels.append(ob.low)
            if sweep and sweep.kind==Liq.SSL:levels.append(sweep.level)
            sl=min(levels)-atr*self.cfg.SL_ATR_BUFFER
            if sl>=entry:return None
            dist=entry-sl;tp=entry+dist*self.cfg.REWARD_RISK
        elif side=="SELL":
            levels=[float(df.high.tail(20).max())]
            if ob and ob.direction==Trend.BEARISH:levels.append(ob.high)
            if sweep and sweep.kind==Liq.BSL:levels.append(sweep.level)
            sl=max(levels)+atr*self.cfg.SL_ATR_BUFFER
            if sl<=entry:return None
            dist=sl-entry;tp=entry-dist*self.cfg.REWARD_RISK
        else:return None
        stop_atr=dist/atr
        if stop_atr<self.cfg.MIN_STOP_ATR or stop_atr>self.cfg.MAX_STOP_ATR:return None
        risk=self.cfg.CAPITAL*self.cfg.RISK_PERCENT/100
        qty=risk/dist
        if not np.isfinite(qty) or qty<=0:return None
        return sl,tp,qty,risk

class DecisionEngine:
    def __init__(self,cfg):self.cfg=cfg
    def valid(self,side,score,macro,ema,h4,h1,sweep,ob,df):
        if side not in ("BUY","SELL") or score<self.cfg.MIN_SCORE:return False
        r=df.iloc[-1]; atr=float(Q.atr(df,self.cfg.ATR_PERIOD).iloc[-1])
        disp=Q.disp(r,atr)
        if side=="BUY":
            return (macro==ema==h4.trend==h1.trend==Trend.BULLISH
                    and h4.event in (Event.BOS_BULLISH,Event.CHOCH_BULLISH)
                    and sweep is not None and sweep.kind==Liq.SSL
                    and ob is not None and ob.direction==Trend.BULLISH
                    and ob.state!=OBState.INVALIDATED
                    and r.close>r.open and disp>=self.cfg.DISPLACEMENT_ATR
                    and Q.body_ratio(r)>=self.cfg.MIN_BODY_RATIO)
        return (macro==ema==h4.trend==h1.trend==Trend.BEARISH
                and h4.event in (Event.BOS_BEARISH,Event.CHOCH_BEARISH)
                and sweep is not None and sweep.kind==Liq.BSL
                and ob is not None and ob.direction==Trend.BEARISH
                and ob.state!=OBState.INVALIDATED
                and r.close<r.open and disp>=self.cfg.DISPLACEMENT_ATR
                and Q.body_ratio(r)>=self.cfg.MIN_BODY_RATIO)

class Telegram:
    def __init__(self,cfg):self.token=cfg.TELEGRAM_TOKEN;self.chat=cfg.TELEGRAM_CHAT_ID
    def enabled(self):return bool(self.token and self.chat)
    def send(self,text):
        if not self.enabled():return False
        try:
            u=f"https://api.telegram.org/bot{self.token}/sendMessage"
            requests.post(u,data={"chat_id":self.chat,"text":text},timeout=15).raise_for_status()
            return True
        except Exception as e:
            log.error("Telegram error: %s",e);return False

def fmt(x):
    if x>=1000:return f"{x:.2f}"
    if x>=1:return f"{x:.5f}"
    return f"{x:.8f}"

class EXCORA:
    def __init__(self,cfg):
        self.cfg=cfg;self.data=Data(cfg);self.struct=StructureEngine(cfg)
        self.liq=LiquidityEngine(cfg);self.ob=OBEngine(cfg);self.fvg=FVGEngine(cfg)
        self.macro=MacroEngine(cfg);self.score=ScoreEngine();self.score.cfg=cfg
        self.risk=RiskEngine(cfg);self.decision=DecisionEngine(cfg);self.tg=Telegram(cfg)
        self.last={}
    def analyze(self,symbol):
        raw={k:self.data.fetch(symbol,v,self.cfg.CANDLE_LIMIT) for k,v in self.cfg.TIMEFRAMES.items()}
        d={"1d":raw["macro"],"4h":raw["structure"],"1h":raw["confirmation"],"15m":raw["execution"]}
        s1=self.struct.analyze(d["1d"]);h4=self.struct.analyze(d["4h"]);h1=self.struct.analyze(d["1h"]);m15=self.struct.analyze(d["15m"])
        ema=self.macro.ema_bias(d["1d"])
        pools=self.liq.pools(d["15m"],m15);sweep=self.liq.sweep(d["15m"],pools)
        ob=self.ob.detect(d["15m"],m15);fvg=self.fvg.detect(d["15m"])
        hi=float(d["1h"].high.max());lo=float(d["1h"].low.min());mid=(hi+lo)/2;price=float(d["1h"].close.iloc[-1])
        zone="DISCOUNT" if price<mid else "PREMIUM" if price>mid else "EQUILIBRIUM"
        score,reasons,side=self.score.score(s1.trend,ema,h4,h1,m15,sweep,ob,fvg,zone,d["15m"])
        valid=self.decision.valid(side,score,s1.trend,ema,h4,h1,sweep,ob,d["15m"])
        entry=float(d["15m"].close.iloc[-1]);sl=tp=qty=risk=0.
        if valid:
            rr=self.risk.calculate(side,entry,d["15m"],ob,sweep)
            if rr:sl,tp,qty,risk=rr
            else:valid=False;side="WAIT"
        return Signal(symbol,side,score,entry,sl,tp,qty,risk,s1.trend,ema,h4.trend,h1.trend,m15.trend,h4.event,h1.event,m15.event,sweep,ob,fvg,reasons,valid)
    def message(self,s):
        liq=s.sweep.kind.value if s.sweep else "NONE"
        ob=f"{s.ob.direction.value}/{s.ob.state.value}" if s.ob else "NONE"
        fvg=f"{s.fvg.direction.value}/{'FILLED' if s.fvg.filled else 'UNFILLED'}" if s.fvg else "NONE"
        return "\n".join([
            "══════════════════════════════","EXCORA INSTITUTIONAL SMC",
            "══════════════════════════════",f"{s.symbol} | {s.side} | Score {s.score:.2f}/100","",
            "── MTF ──",f"1D={s.macro.value} | EMA200={s.ema.value}",
            f"4H={s.h4.value} | Event={s.e4.value}",f"1H={s.h1.value} | Event={s.e1.value}",f"15M={s.m15.value} | Event={s.e15.value}",
            "── SMART MONEY ──",f"Liquidity={liq}",f"OB={ob}",f"FVG={fvg}","",
            "── RISK ──",f"Capital=${self.cfg.CAPITAL:.2f}",f"Risk={self.cfg.RISK_PERCENT:.2f}% (${s.risk:.2f})",
            f"Entry={fmt(s.entry)}",f"SL={fmt(s.sl)}",f"TP={fmt(s.tp)}",f"Position={s.qty:.8f}",f"RR=1:{s.rr if hasattr(s,'rr') else self.cfg.REWARD_RISK:.1f}",
            "","── REASONS ──",*["✓ "+x for x in s.reasons],
            "","EXCORA STATUS: "+("VALID SIGNAL" if s.valid else "WAIT")
        ])
    def run_once(self):
        for symbol in self.cfg.SYMBOLS:
            try:
                s=self.analyze(symbol)
                log.info("%s | %s | score=%.2f | 1D=%s | EMA200=%s | 4H=%s | 1H=%s | 15M=%s | 4H_EVENT=%s",
                         symbol,s.side,s.score,s.macro.value,s.ema.value,s.h4.value,s.h1.value,s.m15.value,s.e4.value)
                if s.valid:
                    key=(s.side,round(s.entry,8),s.e4.value,s.e1.value)
                    if self.last.get(symbol)!=key:
                        if self.tg.send(self.message(s)):log.info("%s | Telegram signal sent",symbol)
                        self.last[symbol]=key
            except Exception as e:log.exception("%s | analysis failed: %s",symbol,e)
            time.sleep(.5)
    def run(self):
        log.info("================================================")
        log.info("EXCORA INSTITUTIONAL SMC STARTED")
        log.info("Capital=%.2f | Risk=%.2f%% | RR=1:%.1f | MinScore=%.1f",self.cfg.CAPITAL,self.cfg.RISK_PERCENT,self.cfg.REWARD_RISK,self.cfg.MIN_SCORE)
        log.info("Telegram: %s","ENABLED" if self.tg.enabled() else "DISABLED")
        log.info("================================================")
        while True:
            try:self.run_once()
            except KeyboardInterrupt:break
            except Exception as e:log.exception("Main loop error: %s",e)
            time.sleep(self.cfg.POLL_SECONDS)

def validate(c):
    if c.CAPITAL<=0:raise ValueError("CAPITAL must be > 0")
    if not 0<c.RISK_PERCENT<=c.MAX_RISK_PERCENT:raise ValueError("RISK_PERCENT must be > 0 and <= 2")
    if c.REWARD_RISK<3:raise ValueError("REWARD_RISK must be >= 3")
    if not 0<=c.MIN_SCORE<=100:raise ValueError("MIN_SCORE must be 0..100")

if __name__=="__main__":
    validate(CFG)
    EXCORA(CFG).run()
