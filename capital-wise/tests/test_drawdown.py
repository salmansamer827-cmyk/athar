from core.risk.drawdown import (
    DrawdownEngine,
)


engine = DrawdownEngine(
    initial_equity=100.0
)


equity_curve = [
    100.0,
    103.0,
    101.97,
    105.0291,
    103.9788,
    107.0982,
]


print("=" * 60)
print("CAPITAL WISE")
print("DRAWDOWN ENGINE")
print("=" * 60)

for index, equity in enumerate(
    equity_curve,
    start=1,
):

    snapshot = engine.update(
        equity
    )

    print(
        f"{index}: "
        f"Equity=${snapshot.equity:.4f} | "
        f"Peak=${snapshot.peak_equity:.4f} | "
        f"DD=${snapshot.drawdown_amount:.4f} | "
        f"DD%={snapshot.drawdown_percent:.2%}"
    )

print("-" * 60)

print(
    f"Maximum Drawdown: "
    f"${engine.max_drawdown_amount:.4f}"
)

print(
    f"Maximum Drawdown %: "
    f"{engine.max_drawdown_percent:.2%}"
)

print("=" * 60)
