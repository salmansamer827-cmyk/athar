from core.risk.engine import RiskEngine


engine = RiskEngine(
    risk_percent=0.01,
    reward_risk=3.0,
)


result = engine.calculate(
    capital=100.0,
    entry_price=100.0,
    stop_price=99.0,
)


print("=" * 60)
print("CAPITAL WISE")
print("RISK MANAGEMENT ENGINE")
print("=" * 60)

print(f"Capital:        ${result.capital:.2f}")
print(f"Risk:            {result.risk_percent * 100:.2f}%")
print(f"Risk Amount:     ${result.risk_amount:.2f}")

print(f"Entry:           {result.entry_price:.4f}")
print(f"Stop Loss:       {result.stop_price:.4f}")
print(f"Take Profit:     {result.take_profit_price:.4f}")

print(f"Price Risk:      {result.price_risk:.4f}")
print(f"Position Size:   {result.position_size:.6f}")
print(f"Notional Value:  ${result.notional_value:.2f}")

print(f"RR:              1:{result.reward_risk_ratio:.1f}")
print(f"Potential Loss:  ${result.potential_loss:.2f}")
print(f"Potential Profit:${result.potential_profit:.2f}")

print("=" * 60)
