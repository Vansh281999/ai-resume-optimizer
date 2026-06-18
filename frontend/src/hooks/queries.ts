import { useState } from 'react';
import { getTrends, getFocusAreas } from '../lib/api';
import { getErrorMessage } from '../lib/utils';

export interface QueryState<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
}

export function createEmptyQueryState<T>(): QueryState<T> {
  return {
    data: null,
    error: null,
    loading: false,
  };
}

export function useTrendsQuery() {
  const [state, setState] = useState<QueryState<Awaited<ReturnType<typeof getTrends>>>>(createEmptyQueryState());

  const run = async () => {
    setState((current) => ({ ...current, loading: true, error: null }));
    try {
      const data = await getTrends();
      setState({ data, error: null, loading: false });
    } catch (error) {
      setState({ data: null, error: getErrorMessage(error), loading: false });
    }
  };

  return { ...state, refetch: run };
}

export function useFocusAreasQuery() {
  const [state, setState] = useState<QueryState<Awaited<ReturnType<typeof getFocusAreas>>>>(createEmptyQueryState());

  const run = async () => {
    setState((current) => ({ ...current, loading: true, error: null }));
    try {
      const data = await getFocusAreas();
      setState({ data, error: null, loading: false });
    } catch (error) {
      setState({ data: null, error: getErrorMessage(error), loading: false });
    }
  };

  return { ...state, refetch: run };
}
