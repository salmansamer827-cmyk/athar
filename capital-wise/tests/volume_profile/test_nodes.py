import numpy as np

from core.volume_profile.quant.nodes import (
    detect_volume_nodes,
)


prices = np.array(
    [
        90,
        91,
        92,
        93,
        94,
        95,
        96,
        97,
        98,
        99,
        100,
        101,
        102,
        103,
        104,
        105,
        106,
        107,
        108,
        109,
        110,
    ],
    dtype=float,
)


volume = np.array(
    [
        20,
        25,
        30,
        80,
        35,
        30,
        100,
        160,
        120,
        60,
        40,
        50,
        45,
        25,
        15,
        10,
        20,
        25,
        30,
        35,
        40,
    ],
    dtype=float,
)


hvn, lvn = detect_volume_nodes(
    prices,
    volume,
)


print("=" * 60)
print("CAPITAL WISE")
print("HVN / LVN CLUSTER ENGINE")
print("=" * 60)

print()
print("HVN NODES")

for node in hvn:
    print(
        f"Center={node.center_price:.2f} | "
        f"Range={node.lower_price:.2f}-"
        f"{node.upper_price:.2f} | "
        f"Strength={node.relative_strength:.2f} | "
        f"Density={node.density:.2f}"
    )


print()
print("LVN NODES")

for node in lvn:
    print(
        f"Center={node.center_price:.2f} | "
        f"Range={node.lower_price:.2f}-"
        f"{node.upper_price:.2f} | "
        f"Strength={node.relative_strength:.2f} | "
        f"Density={node.density:.2f}"
    )

print()
print("=" * 60)
