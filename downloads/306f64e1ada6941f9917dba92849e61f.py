"""
====================================================================
EXCORA TELEGRAM NOTIFIER
====================================================================

Telegram is intentionally isolated from the EXCORA quantitative engine.

Responsibilities:
    - Validate Telegram configuration
    - Format EXCORA signal messages
    - Send messages
    - Prevent duplicate signal notifications

No market-analysis logic lives in this module.
====================================================================
"""

from __future__ import annotations

import logging
from typing import Any

import requests

logger = logging.getLogger("EXCORA.TELEGRAM")


class TelegramNotifier:
    def __init__(
        self,
        token: str | None = None,
        chat_id: str | None = None,
        timeout: int = 10,
    ) -> None:
        self.token = token
        self.chat_id = chat_id
        self.timeout = timeout
        self.last_signal_id: str | None = None

    def configured(self) -> bool:
        return bool(
            self.token
            and self.chat_id
            and self.token != "YOUR_BOT_TOKEN_HERE"
            and self.chat_id != "YOUR_CHAT_ID_HERE"
        )

    def send_raw(self, message: str) -> bool:
        """Send a raw Telegram message. Returns True only on HTTP success."""
        if not self.configured():
            logger.info("TELEGRAM | NOT CONFIGURED")
            return False

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "disable_web_page_preview": True,
        }

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()

            data = response.json()
            if not data.get("ok", False):
                logger.error("TELEGRAM API ERROR | %s", data)
                return False

            return True

        except (requests.RequestException, ValueError) as exc:
            logger.error("TELEGRAM ERROR | %s", exc)
            return False

    @staticmethod
    def format_signal(symbol: str, result: dict[str, Any]) -> str:
        """Build the Telegram presentation from an already validated signal."""
        trade = result["trade"]
        direction = result["signal"]
        emoji = "🟢" if direction == "BUY" else "🔴"
        components = result["score_components"]

        return f"""🚨 EXCORA QUANT MTF SIGNAL

{emoji} {direction} {symbol}

━━━━━━━━━━━━━━━━━━━━
SCORE: {result['score']:.2f}/100
GRADE: {result['grade']}
━━━━━━━━━━━━━━━━━━━━

TIMEFRAME

1D: {result['trend_1d']['trend']}
4H: {result['trend_4h']['trend']}
1H: {result['structure_1h']['structure']}
15M: {direction}

━━━━━━━━━━━━━━━━━━━━
SMART MONEY
━━━━━━━━━━━━━━━━━━━━

Liquidity: {result['liquidity']['type'] or 'NONE'}
Displacement: {'YES' if result['displacement'] else 'NO'}
BOS 4H: {result['structure_4h']['bos'] or 'NONE'}
CHoCH 1H: {result['structure_1h']['choch'] or 'NONE'}
FVG: {'YES' if result['fvg'] else 'NO'}
Order Block: {'YES' if result['order_block'] else 'NO'}

━━━━━━━━━━━━━━━━━━━━
QUANT DATA
━━━━━━━━━━━━━━━━━━━━

ATR: {result['atr']:.8f}
ATR %: {result['atr_pct']:.3f}%
EMA Separation: {result['ema_separation_atr']:.3f} ATR
EMA Slope: {result['ema_slope_atr']:.3f} ATR
Relative Volume: {result['relative_volume']:.2f}
VWAP: {result['vwap']:.8f}
Momentum: {result['roc5']:.3f}%
Regime: {result['regime']}

━━━━━━━━━━━━━━━━━━━━
SCORE BREAKDOWN
━━━━━━━━━━━━━━━━━━━━

1D Trend: {components['1D_TREND']}
4H Trend: {components['4H_TREND']}
Structure: {components['STRUCTURE']}
Liquidity: {components['LIQUIDITY']}
Displacement: {components['DISPLACEMENT']}
EMA: {components['EMA_ALIGNMENT']}
Separation: {components['EMA_SEPARATION']}
Slope: {components['EMA_SLOPE']}
Volume: {components['VOLUME']}
VWAP: {components['VWAP']}
Volume Profile: {components['VOLUME_PROFILE']}
FVG: {components['FVG']}
Order Block: {components['ORDER_BLOCK']}
Candle: {components['CANDLE']}
Momentum: {components['MOMENTUM']}
Regime: {components['REGIME']}

━━━━━━━━━━━━━━━━━━━━
TRADE PLAN
━━━━━━━━━━━━━━━━━━━━

Entry: {trade['entry']:.8f}
Stop Loss: {trade['stop']:.8f}
Take Profit: {trade['tp']:.8f}
Risk: ${trade['risk_usd']:.4f}
Risk Distance: {trade['risk_distance_pct']:.3f}%
Position Size: {trade['quantity']:.8f}
Notional: ${trade['notional']:.4f}
RR: 1:{trade['rr']:.2f}

━━━━━━━━━━━━━━━━━━━━

⚠️ SIGNAL ONLY — NO AUTO EXECUTION

EXCORA QUANT MTF MASTER
1D → 4H → 1H → 15M
"""

    def send_signal(self, symbol: str, result: dict[str, Any]) -> bool:
        """Send BUY/SELL once per signal_id."""
        if result.get("signal") not in ("BUY", "SELL"):
            return False

        signal_id = result.get("signal_id")
        if not signal_id:
            logger.warning("TELEGRAM | Missing signal_id | %s", symbol)
            return False

        if signal_id == self.last_signal_id:
            logger.info("TELEGRAM | DUPLICATE BLOCKED | %s", symbol)
            return False

        message = self.format_signal(symbol, result)
        sent = self.send_raw(message)

        if sent:
            self.last_signal_id = signal_id
            logger.info("TELEGRAM | SENT | %s | %s", symbol, signal_id)

        return sent
