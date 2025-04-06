import { useState, useCallback, useRef } from 'react'
import { useApi } from '@/api/useApi'
import { ApiResponse } from '@/api/types/api.types'

interface PaginationParams {
  page: number
  limit: number
  [key: string]: any // For additional filter params
}

interface PaginatedResponse<T> {
  data: T[]
  total: number
  hasMore: boolean
}

interface UseApiPaginatedOptions<T> {
  pageSize?: number
  onSuccess?: (data: T[]) => void
  onError?: (error: any) => void
  initialParams?: Record<string, any>
}

export function useApiPaginated<T>(
  apiFunction: (params: PaginationParams) => Promise<ApiResponse<PaginatedResponse<T>>>,
  options: UseApiPaginatedOptions<T> = {}
) {
  const [page, setPage] = useState(1)
  const [allData, setAllData] = useState<T[]>([])
  const [hasMore, setHasMore] = useState(true)
  const [total, setTotal] = useState(0)
  const [loadingMore, setLoadingMore] = useState(false)
  const [currentParams, setCurrentParams] = useState<Record<string, any>>(options.initialParams || {})
  
  // Track request identifiers to avoid race conditions
  const requestIdRef = useRef(0)

  const pageSize = options.pageSize || 20

  const api = useApi<PaginatedResponse<T>, [PaginationParams]>(apiFunction, {
    onSuccess: (response: PaginatedResponse<T>) => {
      options.onSuccess?.(response.data)
    },
    onError: options.onError,
  })

  const fetch = useCallback(
    async (params: Record<string, any> = {}) => {
      setPage(1)
      setAllData([])
      setCurrentParams(params)
      
      // Increment request ID to handle race conditions
      const requestId = ++requestIdRef.current
      
      const response = await api.execute({
        ...params,
        page: 1,
        limit: pageSize,
      }) as PaginatedResponse<T>;
      
      // Only update state if this is the most recent request
      if (requestId === requestIdRef.current) {
        setAllData(response.data)
        setHasMore(response.hasMore)
        setTotal(response.total)
      }
      
      return response
    },
    [api, pageSize]
  )

  const fetchMore = useCallback(async () => {
    if (api.loading || loadingMore || !hasMore) return null

    setLoadingMore(true)
    const nextPage = page + 1
    
    // Increment request ID to handle race conditions
    const requestId = ++requestIdRef.current

    try {
      const response = await api.execute({
        ...currentParams,
        page: nextPage,
        limit: pageSize,
      }) as PaginatedResponse<T>;

      // Only update state if this is the most recent request
      if (requestId === requestIdRef.current) {
        setPage(nextPage)
        setAllData((prev) => [...prev, ...response.data])
        setHasMore(response.hasMore)
        setTotal(response.total)
      }
      
      return response
    } catch (error) {
      // Keep existing data on error during pagination
      console.error('Error loading more:', error)
      return null
    } finally {
      if (requestId === requestIdRef.current) {
        setLoadingMore(false)
      }
    }
  }, [api, loadingMore, hasMore, page, pageSize, currentParams])

  const reset = useCallback(() => {
    setPage(1)
    setAllData([])
    setHasMore(true)
    setTotal(0)
    setLoadingMore(false)
    setCurrentParams({})
    api.reset()
  }, [api])

  return {
    data: allData,
    error: api.error,
    loading: api.loading,
    loadingMore,
    hasMore,
    total,
    fetch,
    fetchMore,
    reset,
    currentPage: page,
  }
}