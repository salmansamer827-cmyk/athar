import { useEffect, useMemo, useState } from "react";

type Candle = {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
};

type MarketChartProps = {
  symbol: string;
  timeframe: string;
};

const API = "http://127.0.0.1:8000";

export default function MarketChart({
  symbol,
  timeframe,
}: MarketChartProps) {
  const [candles, setCandles] = useState<Candle[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError("");

      try {
        const params = new URLSearchParams({
          symbol,
          timeframe,
          limit: "100",
        });

        const response = await fetch(
          `${API}/api/v1/markets/ohlcv?${params.toString()}`
        );

        if (!response.ok) {
          throw new Error("Failed to load OHLCV");
        }

        const data = await response.json();

        if (!Array.isArray(data.candles)) {
          throw new Error("Invalid OHLCV response");
        }

        if (!cancelled) {
          setCandles(data.candles);
        }
      } catch (err) {
        if (!cancelled) {
          setCandles([]);
          setError(
            err instanceof Error
              ? err.message
              : "Unable to load market data"
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    load();

    return () => {
      cancelled = true;
    };
  }, [symbol, timeframe]);

  const profile = useMemo(() => {
  if (!candles.length) {
    return {
      poc: 0,
      vah: 0,
      val: 0,
      bins: [] as {
        price: number;
        volume: number;
      }[],
    };
  }

  const BIN_COUNT = 50;
  const VALUE_AREA_PERCENT = 0.70;

  const minPrice = Math.min(
    ...candles.map((c) => c.low)
  );

  const maxPrice = Math.max(
    ...candles.map((c) => c.high)
  );

  const range = maxPrice - minPrice || 1;
  const binSize = range / BIN_COUNT;

  const bins = Array.from(
    { length: BIN_COUNT },
    (_, index) => ({
      price:
        minPrice +
        binSize * (index + 0.5),

      volume: 0,
    })
  );

  /*
   * Distribute each candle's volume
   * across the price bins intersecting
   * its High-Low range.
   */
  for (const candle of candles) {
    const lowIndex = Math.max(
      0,
      Math.floor(
        (candle.low - minPrice) /
          binSize
      )
    );

    const highIndex = Math.min(
      BIN_COUNT - 1,
      Math.floor(
        (candle.high - minPrice) /
          binSize
      )
    );

    const coveredBins =
      highIndex - lowIndex + 1;

    if (coveredBins <= 0) {
      continue;
    }

    const volumePerBin =
      candle.volume / coveredBins;

    for (
      let index = lowIndex;
      index <= highIndex;
      index++
    ) {
      bins[index].volume +=
        volumePerBin;
    }
  }

  const totalVolume = bins.reduce(
    (sum, bin) =>
      sum + bin.volume,
    0
  );

  if (totalVolume <= 0) {
    const lastPrice =
      candles[candles.length - 1].close;

    return {
      poc: lastPrice,
      vah: lastPrice,
      val: lastPrice,
      bins,
    };
  }

  /*
   * POC:
   * Price level containing
   * the maximum traded volume.
   */
  let pocIndex = 0;

  for (
    let index = 1;
    index < bins.length;
    index++
  ) {
    if (
      bins[index].volume >
      bins[pocIndex].volume
    ) {
      pocIndex = index;
    }
  }

  /*
   * Value Area:
   * Start from POC and expand
   * until 70% of total volume
   * is included.
   */
  const targetVolume =
    totalVolume *
    VALUE_AREA_PERCENT;

  let accumulatedVolume =
    bins[pocIndex].volume;

  let lowerIndex = pocIndex;
  let upperIndex = pocIndex;

  while (
    accumulatedVolume <
      targetVolume &&
    (lowerIndex > 0 ||
      upperIndex <
        bins.length - 1)
  ) {
    const lowerVolume =
      lowerIndex > 0
        ? bins[lowerIndex - 1]
            .volume
        : -1;

    const upperVolume =
      upperIndex <
      bins.length - 1
        ? bins[upperIndex + 1]
            .volume
        : -1;

    if (
      upperVolume >= lowerVolume
    ) {
      if (
        upperIndex <
        bins.length - 1
      ) {
        upperIndex++;

        accumulatedVolume +=
          bins[upperIndex].volume;
      } else {
        lowerIndex--;

        accumulatedVolume +=
          bins[lowerIndex].volume;
      }
    } else {
      if (lowerIndex > 0) {
        lowerIndex--;

        accumulatedVolume +=
          bins[lowerIndex].volume;
      } else {
        upperIndex++;

        accumulatedVolume +=
          bins[upperIndex].volume;
      }
    }
  }

  return {
    poc: bins[pocIndex].price,
    vah: bins[upperIndex].price,
    val: bins[lowerIndex].price,
    bins,
  };
}, [candles]);



  if (loading) {
    return (
      <section className="chart-panel">
        <div className="chart-loading">
          Loading Binance market data...
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="chart-panel">
        <div className="chart-error">{error}</div>
      </section>
    );
  }

  if (!candles.length) {
    return (
      <section className="chart-panel">
        <div className="chart-loading">
          No market data available.
        </div>
      </section>
    );
  }

  const width = 1200;
  const height = 560;
  const chartTop = 30;
  const chartBottom = 430;
  const volumeTop = 450;
  const volumeBottom = 530;

  const minPrice = Math.min(
    ...candles.map((c) => c.low),
    profile.val
  );

  const maxPrice = Math.max(
    ...candles.map((c) => c.high),
    profile.vah
  );

  const priceRange = maxPrice - minPrice || 1;

  const priceY = (price: number) =>
    chartBottom -
    ((price - minPrice) / priceRange) *
      (chartBottom - chartTop);

  const maxVolume = Math.max(
    ...candles.map((c) => c.volume)
  );

  const candleWidth = Math.max(
    3,
    width / candles.length - 3
  );

  return (
    <section className="chart-panel">
      <div className="chart-header">
        <div>
          <strong>{symbol}</strong>
          <span>{timeframe}</span>
        </div>

        <div className="chart-stats">
          <span>
            POC {profile.poc.toFixed(2)}
          </span>

          <span>
            VAH {profile.vah.toFixed(2)}
          </span>

          <span>
            VAL {profile.val.toFixed(2)}
          </span>
        </div>
      </div>

      <div className="chart-container">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          preserveAspectRatio="none"
          className="market-chart"
        >
          <rect
            x="0"
            y="0"
            width={width}
            height={height}
            className="chart-background"
          />

          {[0, 1, 2, 3, 4].map((line) => {
            const y =
              chartTop +
              ((chartBottom - chartTop) / 4) *
                line;

            return (
              <line
                key={line}
                x1="0"
                x2={width}
                y1={y}
                y2={y}
                className="chart-grid"
              />
            );
          })}

          <line
            x1="0"
            x2={width}
            y1={priceY(profile.vah)}
            y2={priceY(profile.vah)}
            className="value-area-line vah"
          />

          <line
            x1="0"
            x2={width}
            y1={priceY(profile.poc)}
            y2={priceY(profile.poc)}
            className="value-area-line poc"
          />

          <line
            x1="0"
            x2={width}
            y1={priceY(profile.val)}
            y2={priceY(profile.val)}
            className="value-area-line val"
          />

          {candles.map((candle, index) => {
            const x =
              index *
                (width / candles.length) +
              width / candles.length / 2;

            const openY = priceY(candle.open);
            const closeY = priceY(candle.close);
            const highY = priceY(candle.high);
            const lowY = priceY(candle.low);

            const bullish =
              candle.close >= candle.open;

            const volumeHeight =
              maxVolume > 0
                ? (candle.volume / maxVolume) *
                  (volumeBottom - volumeTop)
                : 0;

            return (
              <g key={candle.timestamp}>
                <line
                  x1={x}
                  x2={x}
                  y1={highY}
                  y2={lowY}
                  className={
                    bullish
                      ? "candle-wick bullish"
                      : "candle-wick bearish"
                  }
                />

                <rect
                  x={x - candleWidth / 2}
                  y={Math.min(
                    openY,
                    closeY
                  )}
                  width={candleWidth}
                  height={Math.max(
                    1,
                    Math.abs(
                      closeY - openY
                    )
                  )}
                  className={
                    bullish
                      ? "candle-body bullish"
                      : "candle-body bearish"
                  }
                />

                <rect
                  x={x - candleWidth / 2}
                  y={
                    volumeBottom -
                    volumeHeight
                  }
                  width={candleWidth}
                  height={volumeHeight}
                  className={
                    bullish
                      ? "volume-bar bullish"
                      : "volume-bar bearish"
                  }
                />
              </g>
            );
          })}
        </svg>

        <div className="chart-price-label poc-label">
          POC {profile.poc.toFixed(2)}
        </div>

        <div className="chart-price-label vah-label">
          VAH {profile.vah.toFixed(2)}
        </div>

        <div className="chart-price-label val-label">
          VAL {profile.val.toFixed(2)}
        </div>
      </div>

      <div className="chart-footer">
        <span>
          Binance • {candles.length} candles
        </span>

        <span>
          Last{" "}
          {candles[candles.length - 1].close.toFixed(
            2
          )}
        </span>
      </div>
    </section>
  );
}
