import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { searchScreening, getPresets, savePreset, deletePreset } from '../api/client';
import type { ScreeningRequest } from '../types';

export function useScreeningSearch(request: ScreeningRequest, enabled = false) {
  return useQuery({
    queryKey: ['screening', request],
    queryFn: () => searchScreening(request),
    enabled,
  });
}

export function usePresets() {
  return useQuery({
    queryKey: ['presets'],
    queryFn: getPresets,
  });
}

export function useSavePreset() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ name, conditions_json }: { name: string; conditions_json: string }) =>
      savePreset(name, conditions_json),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['presets'] });
    },
  });
}

export function useDeletePreset() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => deletePreset(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['presets'] });
    },
  });
}
