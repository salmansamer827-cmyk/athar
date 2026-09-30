from core.volume_profile.signal.engine import (
    VolumeProfileSignalEngine,
    ProfileSignalConfig,
)


engine = VolumeProfileSignalEngine(
    ProfileSignalConfig(
        min_probability=0.55,
        min_ev_r=0.0,
    )
)


profile = {
    "poc": 103.0,
    "vah": 108.0,
    "val": 98.0,
}


dynamics = {
    "value_location": 0.70,
    "poc_velocity": 1.50,
    "value_area_state": "EXPANDING",
}


signal = engine.evaluate(
    profile=profile,
    dynamics=dynamics,
    probability=0.72,
    ev_r=1.80,
    entry=104.0,
)


print("=" * 60)
print("CAPITAL WISE")
print("QUANT VOLUME PROFILE SIGNAL ENGINE")
print("=" * 60)

if signal is None:

    print("Signal: NONE")

else:

    print(
        f"Direction:       "
        f"{signal['direction']}"
    )

    print(
        f"Entry:            "
        f"{signal['entry']:.4f}"
    )

    print(
        f"Stop Loss:        "
        f"{signal['stop_loss']:.4f}"
    )

    print(
        f"Take Profit:      "
        f"{signal['take_profit']:.4f}"
    )

    print(
        f"Probability:      "
        f"{signal['probability']:.2%}"
    )

    print(
        f"Expected Value:   "
        f"{signal['ev_r']:.4f}R"
    )

    print(
        f"Market State:     "
        f"{signal['market_state']}"
    )

print("=" * 60)
