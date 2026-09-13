import axios from 'axios'
import type { AxiosError } from 'axios'

const client = axios.create({
  baseURL: '/api',
  headers: {
    'X-API-Key': import.meta.env.VITE_API_KEY ?? 'dev-key-123',
  },
})

function extractMessage(error: AxiosError<{ detail?: unknown }>): string {
  const detail = error.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0] as { msg?: string }
    if (first?.msg) return first.msg
  }
  return error.message
}

client.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: unknown }>) => Promise.reject(new Error(extractMessage(error))),
)

export default client
