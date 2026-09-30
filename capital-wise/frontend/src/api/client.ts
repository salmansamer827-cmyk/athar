import axios from "axios";

export const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

export async function healthCheck() {
  const response = await api.get("/health");
  return response.data;
}

export async function fetchSymbols(): Promise<string[]> {
  const response = await api.get("/api/v1/markets/symbols");

  if (!Array.isArray(response.data?.symbols)) {
    throw new Error("Invalid Binance symbols response");
  }

  return response.data.symbols;
}

export interface OHLCVCandle {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export async function fetchOHLCV(
  symbol: string,
  timeframe: string,
  limit = 100
): Promise<OHLCVCandle[]> {
  const response = await api.get(
    "/api/v1/markets/ohlcv",
    {
      params: {
        symbol,
        timeframe,
        limit,
      },
    }
  );

  if (
    !Array.isArray(response.data?.candles)
  ) {
    throw new Error("Invalid OHLCV response");
  }

  return response.data.candles;
}

export async function analyzeQuant(payload: {
  symbol: string;
  market: string;
  timeframe: string;
  capital: number;
  limit: number;
  tick_size?: number;
  wins: number;
  losses: number;
}) {
  const response = await api.post(
    "/api/v1/quant/analyze",
    payload
  );

  return response.data;
}
