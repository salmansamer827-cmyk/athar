from core.probability.historical import (
    HistoricalProbabilityEngine,
)


engine = HistoricalProbabilityEngine()

result = engine.calculate(
    wins=72,
    losses=28,
    confidence_level=0.95,
)


print("=" * 60)
print("CAPITAL WISE")
print("HISTORICAL PROBABILITY ENGINE")
print("=" * 60)

print(
    f"Observations:       "
    f"{result.observations}"
)

print(
    f"Wins:               "
    f"{result.wins}"
)

print(
    f"Losses:             "
    f"{result.losses}"
)

print(
    f"Probability:        "
    f"{result.probability:.6f}"
)

print(
    f"Lower Bound:        "
    f"{result.lower_bound:.6f}"
)

print(
    f"Upper Bound:        "
    f"{result.upper_bound:.6f}"
)

print(
    f"Confidence Level:   "
    f"{result.confidence_level:.2%}"
)

print("=" * 60)
