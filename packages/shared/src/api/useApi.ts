import { useState, useCallback, useRef, useEffect, useMemo } from 'react';
import { ApiResponse, ApiError } from './types/api.types'; // Corrected path

interface ApiState<T> {
  data: T | null;
  error: ApiError | null;
  loading: boolean;
}

interface UseApiOptions<T> {
  onSuccess?: (data: T) => void;
  onError?: (error: ApiError) => void;
  initialData?: T | null;
  // removed immediate option as it wasn't used in the original hook logic provided
}

interface UseApiResult<T, Args extends any[]> extends ApiState<T> {
  execute: (...args: Args) => Promise<T | null>;
  cancel: () => void;
  reset: () => void;
}

export function useApi<T, Args extends any[]>(
  apiFunction: (...args: [...Args, { signal?: AbortSignal }]) => Promise<ApiResponse<T>>,
  options: UseApiOptions<T> = {}
): UseApiResult<T, Args> {
  const [state, setState] = useState<ApiState<T>>({
    data: options.initialData ?? null,
    error: null,
    loading: false,
  });

  const controllerRef = useRef<AbortController | null>(null);

  const abortCurrentRequest = useCallback(() => {
    if (controllerRef.current) {
      controllerRef.current.abort();
      controllerRef.current = null;
    }
  }, []);

  useEffect(() => {
    return () => abortCurrentRequest();
  }, [abortCurrentRequest]);

  const execute = useCallback(
    async (...args: Args): Promise<T | null> => {
      abortCurrentRequest();
      controllerRef.current = new AbortController();
      setState((prevState: ApiState<T>) => ({ ...prevState, loading: true, error: null }));

      try {
        const response = await apiFunction(...args, { 
          signal: controllerRef.current.signal 
        });
        
        // Check for abort signal *after* the await, before processing response
        if (controllerRef.current?.signal.aborted) {
          console.log('Request aborted during execution');
          // Reset loading state maybe?
          // setState(prev => ({ ...prev, loading: false })); 
          return null;
        }

        const responseData = response.data;
        setState({ data: responseData, error: null, loading: false });
        options.onSuccess?.(responseData);
        return responseData;
      } catch (error) {
        // Handle errors thrown by apiFunction or the ApiClient
        const apiError = error as ApiError;
        if (apiError.error_code === 'REQUEST_ABORTED') {
          console.log('Caught request aborted error');
          setState((prevState: ApiState<T>) => ({ ...prevState, loading: false })); // Ensure loading is false
          return null;
        }
        
        setState({
          data: null,
          error: apiError,
          loading: false,
        });
        options.onError?.(apiError);
        // Re-throwing might be useful if caller needs to react, but often hooks handle errors internally.
        // Consider if re-throwing is desired behavior.
        // throw apiError; 
        return null; // Return null on error to align with Promise<T | null> signature
      }
    },
    // Removed apiFunction from dependency array if it's expected to be stable (e.g., imported)
    // If apiFunction can change (e.g., passed as prop), it MUST be included.
    [options.onSuccess, options.onError, abortCurrentRequest]
  );

  const cancel = useCallback(() => {
    abortCurrentRequest();
    setState((prevState: ApiState<T>) => ({ ...prevState, loading: false }));
  }, [abortCurrentRequest]);

  const reset = useCallback(() => {
    // Cancel any ongoing request when resetting
    abortCurrentRequest(); 
    setState({
      data: options.initialData ?? null,
      error: null,
      loading: false,
    });
  }, [options.initialData, abortCurrentRequest]);
  
  // Removed debugging code

  return {
    data: state.data,
    loading: state.loading,
    error: state.error,
    execute,
    cancel,
    reset,
  };
} 