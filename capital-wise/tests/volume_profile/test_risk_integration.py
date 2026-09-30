from core.volume_profile.quant.nodes import VolumeNode
from core.volume_profile.risk.levels import (
    ProfileRiskLevelEngine,
)
from core.risk.engine import RiskEngine


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


capital = 100.0
entry = 104.0

profile_risk = ProfileRiskLevelEngine(
    volatility_buffer=0.25,
    reward_risk=3.0,
)


levels = profile_risk.calculate(
    direction="LONG",
    entry=entry,
    val=100.0,
    vah=107.0,
    std=4.0,
    nodes=nodes,
)


risk_engine = RiskEngine(
    risk_percent=0.01,
    reward_risk=3.0,
)


risk = risk_engine.calculate(
    capital=capital,
    entry_price=levels.entry,
    stop_price=levels.stop_loss,
)


print("=" * 60)
print("CAPITAL WISE")
print("PROFILE + RISK INTEGRATION")
print("=" * 60)

print(f"Capital:          ${capital:.2f}")
print(f"Direction:        {levels.direction}")

print()
print(f"Entry:            {levels.entry:.6f}")
print(f"Stop Loss:        {risk.stop_price:.6f}")
print(f"Take Profit:      {risk.take_profit_price:.6f}")

print()
print(f"Price Risk:       {risk.price_risk:.6f}")
print(f"Risk %:           {risk.risk_percent:.2%}")
print(f"Risk Amount:      ${risk.risk_amount:.6f}")

print()
print(f"Position Size:    {risk.position_size:.6f}")
print(f"Notional Value:   ${risk.notional_value:.6f}")

print()
print(f"Potential Loss:   ${risk.potential_loss:.6f}")
print(f"Potential Profit: ${risk.potential_profit:.6f}")

print()
print(f"RR:               1:{risk.reward_risk_ratio:.1f}")

print("=" * 60)
