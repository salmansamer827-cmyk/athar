from core.expected_value import (
    ExpectedValueEngine,
)


engine = ExpectedValueEngine()


result = engine.calculate(
    probability=0.715686,
    reward_r=3.0,
    risk_r=1.0,
    transaction_cost_r=0.05,
)


print("=" * 60)
print("CAPITAL WISE")
print("EXPECTED VALUE ENGINE")
print("=" * 60)

print(
    f"Probability:          "
    f"{result.probability:.6f}"
)

print(
    f"Reward:               "
    f"{result.reward_r:.2f}R"
)

print(
    f"Risk:                 "
    f"{result.risk_r:.2f}R"
)

print(
    f"Gross EV:             "
    f"{result.gross_ev_r:.6f}R"
)

print(
    f"Transaction Cost:     "
    f"{result.transaction_cost_r:.6f}R"
)

print(
    f"Net EV:               "
    f"{result.net_ev_r:.6f}R"
)

print(
    f"Break-even:           "
    f"{result.break_even_probability:.2%}"
)

print(
    f"Probability Edge:     "
    f"{result.edge_probability:.2%}"
)

print(
    f"Profitable:           "
    f"{result.profitable}"
)

print("=" * 60)
