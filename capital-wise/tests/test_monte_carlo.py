from core.risk.monte_carlo import (
    MonteCarloEngine,
)


engine = MonteCarloEngine(
    initial_capital=100.0,
    risk_percent=0.01,
    seed=42,
)


results = [
    3.0,
    -1.0,
    3.0,
    -1.0,
    3.0,
]


result = engine.run(
    results,
    simulations=5000,
)


print("=" * 60)
print("CAPITAL WISE")
print("MONTE CARLO RISK ENGINE")
print("=" * 60)

print(
    f"Simulations:          "
    f"{result.simulations}"
)

print(
    f"Median Final Equity:  "
    f"${result.median_final_equity:.4f}"
)

print(
    f"Worst Final Equity:   "
    f"${result.worst_final_equity:.4f}"
)

print(
    f"Best Final Equity:    "
    f"${result.best_final_equity:.4f}"
)

print(
    f"Median Max DD:        "
    f"{result.median_max_drawdown:.2%}"
)

print(
    f"Worst Max DD:         "
    f"{result.worst_max_drawdown:.2%}"
)

print(
    f"P(DD >= 5%):          "
    f"{result.probability_dd_5pct:.2%}"
)

print(
    f"P(DD >= 10%):         "
    f"{result.probability_dd_10pct:.2%}"
)

print(
    f"P(DD >= 20%):         "
    f"{result.probability_dd_20pct:.2%}"
)

print("=" * 60)
