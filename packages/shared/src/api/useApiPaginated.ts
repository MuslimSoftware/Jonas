import { useState, useCallback, useRef } from 'react';
import { useApi } from './useApi'; // Corrected path
import { ApiResponse, ApiError } from './types/api.types'; // Corrected path

interface PaginationParams {
  page: number;
  limit: number;
  [key: string]: any;
}

interface PaginatedResponse<T> {
  data: T[];
  total: number;
  hasMore: boolean;
}

interface UseApiPaginatedOptions<T> {
  pageSize?: number;
  onSuccess?: (data: T[], page: number) => void;
  onError?: (error: ApiError) => void;
  initialParams?: Record<string, any>;
}

export function useApiPaginated<T>(
  // Type the apiFunction more specifically
  apiFunction: (params: PaginationParams & { signal?: AbortSignal }) => Promise<ApiResponse<PaginatedResponse<T>>>,
  options: UseApiPaginatedOptions<T> = {}
) {
  const [page, setPage] = useState(1);
  const [allData, setAllData] = useState<T[]>([]);
  const [hasMore, setHasMore] = useState(true);
  const [total, setTotal] = useState(0);
  const [loadingMore, setLoadingMore] = useState(false);
  // Store params including page and limit, maybe filter separate?
  const [currentParams, setCurrentParams] = useState<Record<string, any>>(options.initialParams || {});
  
  const requestIdRef = useRef(0);
  const pageSize = options.pageSize || 20;

  // Use the shared useApi hook
  const api = useApi<PaginatedResponse<T>, [PaginationParams]>(apiFunction, {
    // onSuccess/onError are handled within fetch/fetchMore callbacks now
  });

  const handleApiResponse = (
    response: PaginatedResponse<T> | null, 
    requestId: number, 
    isFetchingMore: boolean = false
  ) => {
    if (requestId !== requestIdRef.current || !response) {
      // Stale request or error already handled by useApi
      if (isFetchingMore) setLoadingMore(false);
      return;
    }

    if (isFetchingMore) {
      setPage((prevPage: number) => prevPage + 1);
      setAllData((prevData: T[]) => [...prevData, ...response.data]);
      setLoadingMore(false);
    } else {
      setPage(1); // Reset page on initial fetch
      setAllData(response.data);
    }
    setHasMore(response.hasMore);
    setTotal(response.total);
    options.onSuccess?.(response.data, isFetchingMore ? page + 1 : 1); // Pass page number
  };

  const fetch = useCallback(
    async (params: Record<string, any> = {}, replaceCurrentParams = true) => {
      const newParams = replaceCurrentParams ? params : { ...currentParams, ...params };
      setCurrentParams(newParams); // Update current params used for fetchMore
      const requestId = ++requestIdRef.current;
      
      try {
        const response = await api.execute({
          ...newParams,
          page: 1, // Always start at page 1 for a new fetch
          limit: pageSize,
        });
        handleApiResponse(response, requestId, false); // Handle success/stale state
        return response;
      } catch (error) {
        // Error is already handled by useApi hook (state.error)
        // Call options.onError provided to useApiPaginated
        options.onError?.(error as ApiError);
        return null;
      }
    },
    [api, pageSize, options.onError, currentParams] // Added currentParams dependency
  );

  const fetchMore = useCallback(async () => {
    if (api.loading || loadingMore || !hasMore) return null;

    setLoadingMore(true);
    const nextPage = page + 1;
    const requestId = ++requestIdRef.current;

    try {
      const response = await api.execute({
        ...currentParams,
        page: nextPage,
        limit: pageSize,
      });
      handleApiResponse(response, requestId, true); // Handle success/stale state for fetchMore
      return response;
    } catch (error) {
      console.error('Error loading more:', error);
      options.onError?.(error as ApiError);
      setLoadingMore(false); // Ensure loadingMore is reset on error
      return null;
    } 
  }, [api, loadingMore, hasMore, page, pageSize, currentParams, options.onError]); // Added options.onError

  const reset = useCallback(() => {
    setPage(1);
    setAllData([]);
    setHasMore(true);
    setTotal(0);
    setLoadingMore(false);
    setCurrentParams(options.initialParams || {});
    requestIdRef.current = 0; // Reset request ID
    api.reset();
  }, [api, options.initialParams]);

  return {
    data: allData,
    error: api.error, // Get error state from useApi
    loading: api.loading && !loadingMore, // Initial loading state
    loadingMore,
    hasMore,
    total,
    fetch,
    fetchMore,
    reset,
    currentPage: page,
  };
} 