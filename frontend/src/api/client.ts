import axios from 'axios';
import type {
  ScreeningRequest, ScreeningResponse, StockSummary, Quote,
  FinancialStatement, SyncStatus, PortfolioSummary, PortfolioDetail,
  ImpactResult, TechnicalData, ScreeningPreset,
} from '../types';

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

// Sync
export const syncAll = () => api.post('/sync/all');
export const syncQuotes = () => api.post('/sync/quotes');
export const syncStatements = () => api.post('/sync/statements');
export const syncListings = () => api.post('/sync/listings');
export const getSyncStatus = () => api.get<SyncStatus>('/sync/status').then(r => r.data);

// Screening
export const searchScreening = (req: ScreeningRequest) =>
  api.post<ScreeningResponse>('/screening/search', req).then(r => r.data);
export const getPresets = () =>
  api.get<ScreeningPreset[]>('/screening/presets').then(r => r.data);
export const savePreset = (name: string, conditions_json: string) =>
  api.post('/screening/presets', { name, conditions_json });
export const deletePreset = (id: number) =>
  api.delete(`/screening/presets/${id}`);

// Stocks
export const getStockSummary = (code: string) =>
  api.get<StockSummary>(`/stocks/${code}`).then(r => r.data);
export const getQuotes = (code: string, from?: string, to?: string) =>
  api.get<Quote[]>(`/stocks/${code}/quotes`, { params: { from, to } }).then(r => r.data);
export const getFinancials = (code: string) =>
  api.get<FinancialStatement[]>(`/stocks/${code}/financials`).then(r => r.data);
export const getTechnicals = (code: string, from?: string, to?: string, indicators?: string) =>
  api.get<TechnicalData>(`/stocks/${code}/technicals`, { params: { from, to, indicators } }).then(r => r.data);
export const getImpact = (code: string, params: Record<string, number>) =>
  api.get<ImpactResult>(`/stocks/${code}/impact`, { params }).then(r => r.data);

// Portfolios
export const getPortfolios = () =>
  api.get<PortfolioSummary[]>('/portfolios').then(r => r.data);
export const createPortfolio = (name: string, description?: string) =>
  api.post('/portfolios', { name, description }).then(r => r.data);
export const getPortfolio = (id: number) =>
  api.get<PortfolioDetail>(`/portfolios/${id}`).then(r => r.data);
export const updatePortfolio = (id: number, name: string, description?: string) =>
  api.put(`/portfolios/${id}`, { name, description });
export const deletePortfolio = (id: number) =>
  api.delete(`/portfolios/${id}`);
export const addPortfolioItem = (portfolioId: number, data: { code: string; shares: number; avg_cost: number; acquired_date?: string; memo?: string }) =>
  api.post(`/portfolios/${portfolioId}/items`, data);
export const updatePortfolioItem = (portfolioId: number, itemId: number, data: { shares?: number; avg_cost?: number; memo?: string }) =>
  api.put(`/portfolios/${portfolioId}/items/${itemId}`, data);
export const deletePortfolioItem = (portfolioId: number, itemId: number) =>
  api.delete(`/portfolios/${portfolioId}/items/${itemId}`);
export const getPortfolioPerformance = (id: number) =>
  api.get(`/portfolios/${id}/performance`).then(r => r.data);

// Master
export const getSectors = () =>
  api.get('/master/sectors').then(r => r.data);
export const getMarkets = () =>
  api.get('/master/markets').then(r => r.data);
export const searchStocks = (q: string) =>
  api.get('/master/stocks/search', { params: { q } }).then(r => r.data);

// Export
export const exportScreening = (req: ScreeningRequest) =>
  api.post('/export/screening', req, { responseType: 'blob' }).then(r => r.data);
export const exportPortfolio = (id: number) =>
  api.get(`/export/portfolio/${id}`, { responseType: 'blob' }).then(r => r.data);
