export interface QuantResponse {
  status: string;
  data_source: string;
  candles_count: number;
  volume_sum: number;
  last_price: number;

  symbol: string;
  market: string;
  timeframe: string;

  profile: {
    price_low: number;
    price_high: number;
    bins: number;
    total_volume: number;
    poc: number;
    vah: number;
    val: number;
    weighted_mean: number;
    variance: number;
    std: number;
    skewness: number;
    kurtosis: number;
    entropy: number;
    volume_concentration: number;

    hvn_nodes: Array<{
      kind: string;
      lower_price: number;
      upper_price: number;
      center_price: number;
      peak_volume: number;
      relative_strength: number;
    }>;

    lvn_nodes: Array<unknown>;
  };

  dynamics: {
    poc_change: number;
    poc_velocity: number;
    vah_change: number;
    val_change: number;
    value_area_width: number;
    value_area_width_change: number;
    value_location: number;
    poc_direction: string;
    value_area_state: string;
  };

  state: {
    migration_score: number;
    expansion_score: number;
    balance_score: number;
    concentration_score: number;
    state: string;
    confidence: number;
  };

  probability: {
    observations: number;
    wins: number;
    losses: number;
    probability: number;
    lower_bound: number;
    upper_bound: number;
    confidence_level: number;
  };

  expected_value_r: number;

  signal: {
    status?: string;
    direction?: string;
    entry?: number;
    stop_loss?: number;
    take_profit?: number;
    probability?: number;
    expected_value_r?: number;
    confidence?: number;
    reason?: string;
  } | null;

  risk: {
    status?: string;
    direction?: string;
    entry?: number;
    stop_loss?: number;
    take_profit?: number;
    probability?: number;
    expected_value_r?: number;
    confidence?: number;
    risk_percent?: number;
    risk_amount?: number;
    position_size?: number;
    notional?: number;
    reward_risk?: number;
    reason?: string;
  } | null;
}
