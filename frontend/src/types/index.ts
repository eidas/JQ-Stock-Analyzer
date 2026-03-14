// Stock types
export interface Stock {
  code: string;
  name: string;
  market_segment: string | null;
  sector_17: string | null;
  sector_33: string | null;
}

export interface Quote {
  date: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  volume: number | null;
  turnover_value?: number | null;
  change?: number | null;
  change_pct?: number | null;
}

export interface Metrics {
  per: number | null;
  pbr: number | null;
  roe: number | null;
  dividend_yield: number | null;
  market_cap: number | null;
  turnover_days_20: number | null;
  avg_volume_20d: number | null;
  avg_volume_60d: number | null;
  volatility_20d: number | null;
  operating_margin: number | null;
  ytd_return: number | null;
}

export interface Financial {
  equity_ratio: number | null;
  shares_outstanding: number | null;
  fiscal_year: string | null;
  disclosed_date: string | null;
  net_sales: number | null;
  operating_profit: number | null;
  net_income: number | null;
  eps: number | null;
  bps: number | null;
  dividend_forecast: number | null;
}

export interface StockSummary {
  code: string;
  name: string;
  market_segment: string | null;
  sector_17: string | null;
  sector_33: string | null;
  quote: Quote;
  metrics: Metrics;
  financial: Financial;
  high_52w: number | null;
  low_52w: number | null;
}

export interface FinancialStatement {
  id: number;
  fiscal_year: string | null;
  type_of_document: string | null;
  disclosed_date: string | null;
  net_sales: number | null;
  operating_profit: number | null;
  ordinary_profit: number | null;
  net_income: number | null;
  eps: number | null;
  bps: number | null;
  total_assets: number | null;
  equity: number | null;
  equity_ratio: number | null;
  shares_outstanding: number | null;
  dividend_forecast: number | null;
  forecast_net_sales: number | null;
  forecast_operating_profit: number | null;
  forecast_net_income: number | null;
  forecast_eps: number | null;
  forecast_dividend: number | null;
}

// Screening types
export interface ScreeningCondition {
  group: number;
  field: string;
  operator: string;
  value: number | number[] | string | null;
}

export interface ScreeningRequest {
  conditions: ScreeningCondition[];
  group_logic: string;
  sort_by: string;
  sort_order: string;
  page: number;
  per_page: number;
  market_segments: string[];
  sectors_33: string[];
}

export interface ScreeningResult {
  code: string;
  name: string;
  market_segment: string | null;
  sector_33: string | null;
  close: number | null;
  change_pct: number | null;
  per: number | null;
  pbr: number | null;
  roe: number | null;
  dividend_yield: number | null;
  turnover_days_20: number | null;
  market_cap: number | null;
  date: string | null;
}

export interface ScreeningResponse {
  total: number;
  page: number;
  per_page: number;
  results: ScreeningResult[];
}

// Portfolio types
export interface PortfolioSummary {
  id: number;
  name: string;
  description: string | null;
  created_at: string | null;
  total_value: number | null;
  total_cost: number | null;
  pnl: number | null;
  pnl_pct: number | null;
  item_count: number;
}

export interface PortfolioItem {
  id: number;
  code: string;
  name: string | null;
  sector_33: string | null;
  shares: number;
  avg_cost: number;
  current_price: number | null;
  eval_amount: number | null;
  pnl: number | null;
  pnl_pct: number | null;
  dividend_yield_cost: number | null;
  allocation_pct: number | null;
  acquired_date: string | null;
  memo: string | null;
}

export interface PortfolioDetail {
  id: number;
  name: string;
  description: string | null;
  created_at: string | null;
  total_value: number;
  items: PortfolioItem[];
}

// Sync types
export interface SyncStatus {
  id?: number;
  sync_type?: string;
  status: string;
  progress_pct: number;
  current_step: string;
  records_count?: number;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
}

// Impact types
export interface ImpactResult {
  code: string;
  name: string;
  input: {
    quantity: number;
    execution_days: number;
    max_participation_rate: number;
  };
  market_data: {
    [key: string]: number | null;
  };
  result: {
    estimated_impact_pct: number;
    estimated_impact_yen: number;
    min_execution_days: number;
    daily_schedule: {
      day: number;
      quantity: number;
      participation_rate: number;
    }[];
  };
}

// Technical types
export interface TechnicalData {
  code: string;
  period: { from: string; to: string };
  indicators: Record<string, {
    params: Record<string, unknown>;
    data: Record<string, unknown>[];
  }>;
  warnings?: string[];
}

// Preset types
export interface ScreeningPreset {
  id: number;
  name: string;
  conditions_json: string;
  created_at: string | null;
}
