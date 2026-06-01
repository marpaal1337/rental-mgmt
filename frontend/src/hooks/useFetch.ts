import { useEffect, useRef, useState } from 'react'

interface UseFetchResult<T> {
  data: T | null
  loading: boolean
  error: string | null
  load: () => void
}

export function useFetch<T>(
  fetchFn: () => Promise<T>,
): UseFetchResult<T> {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const mountedRef = useRef(true)

  const load = () => {
    setError(null)
    fetchFn()
      .then((result) => { if (mountedRef.current) setData(result) })
      .catch((err: unknown) => {
        if (mountedRef.current) {
          setError(err instanceof Error ? err.message : 'Error al cargar datos')
        }
      })
      .finally(() => { if (mountedRef.current) setLoading(false) })
  }

  useEffect(() => {
    mountedRef.current = true
    fetchFn()
      .then((result) => { if (mountedRef.current) setData(result) })
      .catch((err: unknown) => {
        if (mountedRef.current) {
          setError(err instanceof Error ? err.message : 'Error al cargar datos')
        }
      })
      .finally(() => { if (mountedRef.current) setLoading(false) })
    return () => { mountedRef.current = false }
  }, [])

  return { data, loading, error, load }
}
