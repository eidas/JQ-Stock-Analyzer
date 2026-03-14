import { useQuery } from '@tanstack/react-query';
import { getStockSummary, getQuotes, getFinancials, getTechnicals, getImpact } from '../api/client';

export function useStockSummary(code: string) {
  return useQuery({
    queryKey: ['stock', code],
    queryFn: () => getStockSummary(code),
    enabled: !!code,
  });
}

export function useQuotes(code: string, from?: string, to?: string) {
  return useQuery({
    queryKey: ['quotes', code, from, to],
    queryFn: () => getQuotes(code, from, to),
    enabled: !!code,
  });
}

export function useFinancials(code: string) {
  return useQuery({
    queryKey: ['financials', code],
    queryFn: () => getFinancials(code),
    enabled: !!code,
  });
}

export function useTechnicals(code: string, from?: string, to?: string, indicators?: string) {
  return useQuery({
    queryKey: ['technicals', code, from, to, indicators],
    queryFn: () => getTechnicals(code, from, to, indicators),
    enabled: !!code,
  });
}

export function useImpact(code: string, params: Record<string, number>, enabled = false) {
  return useQuery({
    queryKey: ['impact', code, params],
    queryFn: () => getImpact(code, params),
    enabled: enabled && !!code,
  });
}
