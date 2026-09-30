from core.trade.engine import FinalTradeEngine
from core.volume_profile.quant.nodes import VolumeNode


nodes = [
    VolumeNode(
        kind="HVN",
        lower_price=96.5,
        upper_price=97.5,
        center_price=97.0,
        peak_volume=160.0,
        total_volume=160.0,
        relative_strength=4.57,
        density=160.0,
        width=1.0,
    ),
]


engine = FinalTradeEngine(
    capital=100.0,
    risk_percent=0.01,
    reward_risk=3.0,
)


profile = {
    "val": 100.0,
    "vah": 107.0,
    "std": 4.0,
}


result = engine.evaluate(
    direction="LONG",
    entry=104.0,
    profile=profile,
    probability=0.72,
    expected_value=1.88,
    market_state="VALUE_MIGRATION_UP",
    confidence=0.74,
    nodes=nodes,
)


print("=" * 60)
print("CAPITAL WISE")
print("FINAL QUANTITATIVE TRADE")
print("=" * 60)

print(f"Status:            {result.status}")
print(f"Direction:         {result.direction}")

print()
print(f"Entry:             {result.entry:.6f}")
print(f"Stop Loss:         {result.stop_loss:.6f}")
print(f"Take Profit:       {result.take_profit:.6f}")

print()
print(f"Probability:       {result.probability:.2%}")
print(f"Expected Value:    {result.expected_value:.4f}R")
print(f"Confidence:        {result.confidence:.2%}")

print()
print(f"Risk:              {result.risk_percent:.2%}")
print(f"Risk Amount:       ${result.risk_amount:.6f}")

print()
print(f"Position Size:     {result.position_size:.6f}")
print(f"Notional Value:    ${result.notional_value:.6f}")

print()
print(f"RR:                1:{result.rr:.1f}")
print(f"Reason:            {result.reason}")

print("=" * 60)
