from core.data.providers.mock import MockMarketProvider
from core.pipeline.quant_pipeline import QuantPipeline


print("=" * 60)
print("CAPITAL WISE")
print("FULL QUANTITATIVE PIPELINE")
print("=" * 60)


# ---------------------------------------------------------
# MARKET DATA
# ---------------------------------------------------------

provider = MockMarketProvider("CRYPTO")

candles = provider.fetch_ohlcv(
    symbol="BTC/USDT",
    timeframe="15m",
    limit=100,
)


# ---------------------------------------------------------
# QUANT PIPELINE
# ---------------------------------------------------------

pipeline = QuantPipeline(
    risk_percent=0.01,
    reward_risk=3.0,
    value_area=0.70,
)


result = pipeline.run(
    candles=candles,
    symbol="BTC/USDT",
    market="CRYPTO",
    timeframe="15m",

    wins=72,
    losses=28,

    capital=100.0,

    entry=None,
    stop_price=None,
)


# ---------------------------------------------------------
# OUTPUT
# ---------------------------------------------------------

print()
print(f"Market:          {result.market}")
print(f"Symbol:          {result.symbol}")
print(f"Timeframe:       {result.timeframe}")

print()
print("PROFILE")
print("-" * 60)

print(
    f"POC:             "
    f"{result.profile.poc:.6f}"
)

print(
    f"VAH:             "
    f"{result.profile.vah:.6f}"
)

print(
    f"VAL:             "
    f"{result.profile.val:.6f}"
)

print(
    f"Weighted Mean:   "
    f"{result.profile.weighted_mean:.6f}"
)

print(
    f"Std:             "
    f"{result.profile.std:.6f}"
)

print(
    f"Entropy:         "
    f"{result.profile.entropy:.6f}"
)

print(
    f"Concentration:   "
    f"{result.profile.volume_concentration:.6f}"
)


print()
print("DYNAMICS")
print("-" * 60)

print(
    f"POC Change:      "
    f"{result.dynamics.poc_change:.6f}"
)

print(
    f"POC Velocity:    "
    f"{result.dynamics.poc_velocity:.6f}"
)

print(
    f"VA Width:        "
    f"{result.dynamics.value_area_width:.6f}"
)

print(
    f"VA Width Change: "
    f"{result.dynamics.value_area_width_change:.6f}"
)

print(
    f"Value Location:  "
    f"{result.dynamics.value_location:.6f}"
)

print(
    f"POC Direction:   "
    f"{result.dynamics.poc_direction}"
)

print(
    f"VA State:        "
    f"{result.dynamics.value_area_state}"
)


print()
print("MARKET STATE")
print("-" * 60)

print(
    f"State:           "
    f"{result.state.state}"
)

print(
    f"Confidence:      "
    f"{result.state.confidence:.6f}"
)


print()
print("PROBABILITY")
print("-" * 60)

print(
    f"Observations:    "
    f"{result.probability.observations}"
)

print(
    f"Probability:     "
    f"{result.probability.probability:.6f}"
)

print(
    f"Lower Bound:     "
    f"{result.probability.lower_bound:.6f}"
)

print(
    f"Upper Bound:     "
    f"{result.probability.upper_bound:.6f}"
)


print()
print("EXPECTED VALUE")
print("-" * 60)

print(
    f"EV:              "
    f"{result.expected_value_r:.6f}R"
)


print()
print("SIGNAL")
print("-" * 60)

print(result.signal)


print()
print("RISK")
print("-" * 60)

if result.risk is None:

    print(
        "Risk calculation waiting "
        "for validated Stop Loss."
    )

else:

    print(
        f"Risk:            "
        f"{result.risk.risk_percent:.2%}"
    )

    print(
        f"Risk Amount:     "
        f"${result.risk.risk_amount:.4f}"
    )

    print(
        f"Entry:           "
        f"{result.risk.entry_price:.6f}"
    )

    print(
        f"Stop Loss:       "
        f"{result.risk.stop_price:.6f}"
    )

    print(
        f"Take Profit:     "
        f"{result.risk.take_profit_price:.6f}"
    )

    print(
        f"Position Size:   "
        f"{result.risk.position_size:.6f}"
    )

    print(
        f"Notional:        "
        f"${result.risk.notional_value:.4f}"
    )

    print(
        f"RR:              "
        f"1:{result.risk.reward_risk_ratio:.1f}"
    )


print()
print("=" * 60)
print("PIPELINE TEST COMPLETED")
print("=" * 60)
