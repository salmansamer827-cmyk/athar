from core.risk.equity import (
    EquityConfig,
    EquityRiskEngine,
)


engine = EquityRiskEngine(
    EquityConfig(
        initial_capital=100.0,
        risk_percent=0.01,
        reward_risk=3.0,
    )
)


results = []

sequence = [
    3.0,
    -1.0,
    3.0,
    -1.0,
    3.0,
]


for realized_r in sequence:

    result = engine.apply_trade(
        realized_r
    )

    results.append(result)


print("=" * 60)
print("CAPITAL WISE")
print("EQUITY & RISK ENGINE")
print("=" * 60)

for index, result in enumerate(
    results,
    start=1,
):

    print(
        f"Trade {index}: "
        f"{result.realized_r:+.2f}R | "
        f"Risk=${result.risk_amount:.4f} | "
        f"PnL=${result.pnl:+.4f} | "
        f"Equity=${result.equity_after:.4f}"
    )

print("-" * 60)

print(
    f"Initial Capital: "
    f"${engine.config.initial_capital:.2f}"
)

print(
    f"Final Equity:    "
    f"${engine.equity:.4f}"
)

print(
    f"Total Return:    "
    f"{(
        engine.equity
        / engine.config.initial_capital
        - 1.0
    ):.2%}"
)

print("=" * 60)
