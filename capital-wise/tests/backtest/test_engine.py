from core.backtest.engine import (
    HistoricalBacktestEngine,
    BacktestConfig,
)


candles = []

price = 100.0

for i in range(350):

    candles.append(
        {
            "timestamp": i,
            "open": price,
            "high": price + 1.0,
            "low": price - 1.0,
            "close": price,
            "volume": 1000.0,
        }
    )

    price += 0.10


def signal_function(history):

    entry = history[-1]["close"]

    return {
        "direction": "LONG",

        "entry": entry,

        "stop_loss": entry - 1.0,

        "take_profit": entry + 3.0,

        "probability": 0.70,

        "ev_r": 1.80,

        "market_state":
            "VALUE_MIGRATION_UP",

        "transaction_cost_r":
            0.05,
    }


config = BacktestConfig(
    risk_percent=0.01,
    reward_risk=3.0,

    profile_lookback=100,
    forward_bars=20,

    min_probability=0.55,
    min_ev_r=0.0,
)


engine = HistoricalBacktestEngine(
    config
)


trades = engine.run(
    candles=candles,
    signal_function=signal_function,
)


print("=" * 60)
print("CAPITAL WISE")
print("HISTORICAL BACKTEST ENGINE")
print("=" * 60)

print(
    f"Generated Trades: "
    f"{len(trades)}"
)

for trade in trades[:10]:

    print(
        f"{trade.timestamp} | "
        f"{trade.outcome.value} | "
        f"{trade.realized_r:.2f}R | "
        f"{trade.market_state}"
    )

print("=" * 60)
