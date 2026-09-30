from core.volume_profile.quant.state import (
    MarketStateEngine,
)


engine = MarketStateEngine()


result = engine.calculate(
    poc_velocity=2.5,
    value_area_width_change=1.0,
    value_location=0.60,
    entropy=0.944264,
    concentration=0.033713,
)


print("=" * 60)
print("CAPITAL WISE")
print("QUANT MARKET STATE ENGINE")
print("=" * 60)

print(
    f"Migration Score:      "
    f"{result.migration_score:.6f}"
)

print(
    f"Expansion Score:      "
    f"{result.expansion_score:.6f}"
)

print(
    f"Balance Score:        "
    f"{result.balance_score:.6f}"
)

print(
    f"Concentration Score:  "
    f"{result.concentration_score:.6f}"
)

print(
    f"State:                "
    f"{result.state}"
)

print(
    f"Confidence:           "
    f"{result.confidence:.6f}"
)

print("=" * 60)
