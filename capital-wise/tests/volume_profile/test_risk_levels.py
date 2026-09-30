from core.volume_profile.quant.nodes import (
    VolumeNode,
)

from core.volume_profile.risk.levels import (
    ProfileRiskLevelEngine,
)


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


engine = ProfileRiskLevelEngine(
    volatility_buffer=0.25,
    reward_risk=3.0,
)


result = engine.calculate(
    direction="LONG",
    entry=104.0,
    val=100.0,
    vah=107.0,
    std=4.0,
    nodes=nodes,
)


print("=" * 60)
print("CAPITAL WISE")
print("PROFILE RISK LEVEL ENGINE")
print("=" * 60)

print(
    f"Direction:       {result.direction}"
)

print(
    f"Entry:           {result.entry:.6f}"
)

print(
    f"Reference:       "
    f"{result.reference_level:.6f}"
)

print(
    f"Buffer:          "
    f"{result.buffer:.6f}"
)

print(
    f"Stop Loss:       "
    f"{result.stop_loss:.6f}"
)

print(
    f"Take Profit:     "
    f"{result.take_profit:.6f}"
)

print(
    f"Price Risk:      "
    f"{result.price_risk:.6f}"
)

print(
    f"RR:              "
    f"1:{result.rr:.1f}"
)

print("=" * 60)
