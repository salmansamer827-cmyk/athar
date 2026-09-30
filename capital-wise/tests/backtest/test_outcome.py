from core.backtest.outcome import (
    TradeOutcomeEngine,
    OutcomeStatus,
)


engine = TradeOutcomeEngine()


candles = [
    {
        "high": 101.0,
        "low": 99.5,
    },
    {
        "high": 102.0,
        "low": 100.0,
    },
    {
        "high": 103.5,
        "low": 101.0,
    },
]


result = engine.evaluate(
    entry=100.0,
    stop_loss=99.0,
    take_profit=103.0,
    candles=candles,
    direction="LONG",
)


print("=" * 60)
print("CAPITAL WISE")
print("TRADE OUTCOME ENGINE")
print("=" * 60)

print(
    f"Status:        "
    f"{result.status.value}"
)

print(
    f"Realized R:    "
    f"{result.realized_r:.4f}R"
)

print(
    f"Exit Price:    "
    f"{result.exit_price}"
)

print(
    f"Bars Held:     "
    f"{result.bars_held}"
)

print("=" * 60)
