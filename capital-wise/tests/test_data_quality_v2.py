from core.data.models import OHLCV
from core.data.quality import (
    DataQualityEngine,
)


candles = [
    OHLCV(
        timestamp=1000 + i,

        open=100.0 + i,
        high=102.0 + i,
        low=99.0 + i,
        close=101.0 + i,

        volume=1000.0,

        symbol="BTC/USDT",
        market="CRYPTO",
        timeframe="15m",
    )

    for i in range(5)
]


engine = DataQualityEngine()

report = engine.validate(
    candles
)


print("=" * 60)
print("CAPITAL WISE")
print("DATA QUALITY ENGINE V2")
print("=" * 60)

print(
    f"Rows:                 "
    f"{report.rows}"
)

print(
    f"Valid:                "
    f"{report.valid}"
)

print(
    f"Missing Values:       "
    f"{report.missing_values}"
)

print(
    f"Duplicate Timestamps: "
    f"{report.duplicate_timestamps}"
)

print(
    f"Invalid Prices:       "
    f"{report.invalid_prices}"
)

print(
    f"Invalid OHLC:         "
    f"{report.invalid_ohlc}"
)

print(
    f"Negative Volume:      "
    f"{report.negative_volume}"
)

print(
    f"Invalid Timestamps:   "
    f"{report.invalid_timestamps}"
)

print(
    f"Total Volume:          "
    f"{report.total_volume:.2f}"
)

print("=" * 60)
