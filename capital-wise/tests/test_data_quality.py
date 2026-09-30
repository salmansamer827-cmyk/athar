import pandas as pd

from core.data.quality import (
    MarketDataQuality,
)


df = pd.DataFrame({
    "timestamp": pd.date_range(
        "2026-01-01",
        periods=5,
        freq="15min",
    ),
    "open": [100, 101, 102, 103, 104],
    "high": [102, 103, 104, 105, 106],
    "low": [99, 100, 101, 102, 103],
    "close": [101, 102, 103, 104, 105],
    "volume": [100, 200, 300, 400, 500],
})


engine = MarketDataQuality()

report = engine.validate(df)


print("=" * 60)
print("CAPITAL WISE")
print("DATA QUALITY ENGINE")
print("=" * 60)

print(f"Rows:                 {report.rows}")
print(f"Valid:                {report.valid}")
print(f"Missing Values:       {report.missing_values}")
print(f"Duplicate Timestamps: {report.duplicate_timestamps}")
print(f"Invalid Prices:       {report.non_positive_prices}")
print(f"Invalid OHLC:         {report.invalid_ohlc}")
print(f"Negative Volume:      {report.negative_volume}")
print(f"Total Volume:         {report.total_volume}")

print("=" * 60)
