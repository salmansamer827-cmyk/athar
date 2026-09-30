from core.decision.engine import QuantDecisionEngine


engine = QuantDecisionEngine(
    min_probability=0.60,
    min_ev_r=0.50,
    min_confidence=0.50,
)


print("=" * 60)
print("CAPITAL WISE")
print("FINAL QUANT DECISION ENGINE")
print("=" * 60)


result = engine.evaluate(
    direction="LONG",
    probability=0.72,
    expected_value=1.88,
    market_state="VALUE_MIGRATION_UP",
    confidence=0.74,
)


print(f"Status:            {result.status}")
print(f"Direction:         {result.direction}")
print(f"Probability:       {result.probability:.2%}")
print(f"Expected Value:    {result.expected_value:.4f}R")
print(f"Market State:      {result.market_state}")
print(f"Confidence:        {result.confidence:.2%}")
print(f"Reason:            {result.reason}")

print("=" * 60)
