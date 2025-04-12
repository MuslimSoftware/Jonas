import { useState, useCallback, useRef } from 'react'
import { useApi } from '@/api/useApi'
import { ApiResponse, ApiError } from '@/api/types/api.types'
import { PaginatedResponseData, PaginationParams } from '@/api/types/chat.types' // Assuming chat.types has the generic structure


interface UseApiPaginatedOptions<T> {
  pageSize?: number
  onSuccess?: (data: T[]) => void
  onError?: (error: ApiError | null) => void
  initialParams?: Record<string, any>
}

export function useApiPaginated<T>(
  apiFunction: (params: PaginationParams) => Promise<ApiResponse<PaginatedResponseData<T>>>,
  options: UseApiPaginatedOptions<T> = {}
) {
  const [allData, setAllData] = useState<T[]>([])
  const [hasMore, setHasMore] = useState(true)
  const [nextCursorTimestamp, setNextCursorTimestamp] = useState<string | null>(null);
  const [loadingMore, setLoadingMore] = useState(false)
  const [currentParams, setCurrentParams] = useState<Record<string, any>>(options.initialParams || {})
  const requestIdRef = useRef(0)
  const pageSize = options.pageSize || 20

  const api = useApi<PaginatedResponseData<T>, [PaginationParams]>(apiFunction, {
    onError: options.onError, 
  })

  const fetch = useCallback(
    async (params: Record<string, any> = {}, isRefresh = false) => {
      if (!isRefresh) {
        setAllData([]);
        setHasMore(true);
        setNextCursorTimestamp(null);
      }
      setCurrentParams(params);
      
      const requestId = ++requestIdRef.current; 
      
      const response = await api.execute({
        ...params,
        limit: pageSize,
      });
      
      if (response && requestId === requestIdRef.current) {
        setAllData(response.items);
        setHasMore(response.has_more);
        setNextCursorTimestamp(response.next_cursor_timestamp);
        options.onSuccess?.(response.items);
      }
      
      return response;
    },
    [api.execute, pageSize, options.onSuccess]
  );

  const fetchMore = useCallback(async () => {
    if (api.loading || loadingMore || !hasMore || !nextCursorTimestamp) {
      return null;
    }

    setLoadingMore(true);
    const requestId = ++requestIdRef.current;

    try {
      const response = await api.execute({
        ...currentParams,
        limit: pageSize,
        before_timestamp: nextCursorTimestamp,
      });

      if (response && requestId === requestIdRef.current) {
        setAllData((prev) => [...prev, ...response.items]);
        setHasMore(response.has_more);
        setNextCursorTimestamp(response.next_cursor_timestamp);
        options.onSuccess?.(response.items);
      }
      
      return response;
    } catch (error) {
      console.error('Error loading more:', error);
      return null;
    } finally {
      if (requestId === requestIdRef.current) {
        setLoadingMore(false);
      }
    }
  }, [api.execute, loadingMore, hasMore, nextCursorTimestamp, pageSize, currentParams, options.onSuccess]);

  const reset = useCallback(() => {
    setAllData([])
    setHasMore(true)
    setNextCursorTimestamp(null)
    setLoadingMore(false)
    setCurrentParams(options.initialParams || {})
    api.reset()
  }, [api, options.initialParams])

  return {
    data: allData,
    error: api.error,
    loading: api.loading,
    loadingMore,
    hasMore,
    fetch,
    fetchMore,
    reset,
    nextCursorTimestamp,
  }
}