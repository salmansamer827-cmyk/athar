from core.data.providers.mock import (
    MockMarketProvider,
)

from core.analysis.analyzer import (
    QuantAnalyzer,
)


provider = MockMarketProvider(
    "CRYPTO"
)

candles = provider.fetch_ohlcv(
    symbol="BTC/USDT",
    timeframe="15m",
    limit=100,
)


analyzer = QuantAnalyzer()

stats = analyzer.analyze_prices(
    candles
)


print("=" * 60)
print("CAPITAL WISE")
print("QUANT ANALYZER")
print("=" * 60)

print(
    f"Symbol:              BTC/USDT"
)

print(
    f"Observations:        {len(candles)}"
)

print(
    f"Minimum:             "
    f"{stats.minimum:.6f}"
)

print(
    f"Maximum:             "
    f"{stats.maximum:.6f}"
)

print(
    f"Mean:                "
    f"{stats.mean:.6f}"
)

print(
    f"Standard Deviation:  "
    f"{stats.standard_deviation:.6f}"
)

print("=" * 60)
