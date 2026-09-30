from core.volume_profile.quant.dynamics import (
    ProfileDynamicsEngine,
)


engine = ProfileDynamicsEngine()


result = engine.calculate(
    current_poc=105.0,
    previous_poc=102.0,
    previous_poc_k=100.0,

    current_vah=110.0,
    previous_vah=108.0,

    current_val=95.0,
    previous_val=94.0,

    price_low=90.0,
    price_high=115.0,

    lookback=2,
)


print("=" * 60)
print("CAPITAL WISE")
print("PROFILE DYNAMICS ENGINE")
print("=" * 60)

print(
    f"POC Change:           "
    f"{result.poc_change:.6f}"
)

print(
    f"POC Velocity:         "
    f"{result.poc_velocity:.6f}"
)

print(
    f"VAH Change:           "
    f"{result.vah_change:.6f}"
)

print(
    f"VAL Change:           "
    f"{result.val_change:.6f}"
)

print(
    f"Value Area Width:     "
    f"{result.value_area_width:.6f}"
)

print(
    f"Width Change:         "
    f"{result.value_area_width_change:.6f}"
)

print(
    f"Value Location:       "
    f"{result.value_location:.6f}"
)

print(
    f"POC Direction:        "
    f"{result.poc_direction}"
)

print(
    f"Value Area State:     "
    f"{result.value_area_state}"
)

print("=" * 60)
