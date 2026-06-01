import axios from 'axios'
import type { AxiosRequestConfig } from 'axios'

export function createClient(signal?: AbortSignal) {
  return axios.create({
    baseURL: '/api',
    headers: {
      'X-API-Key': import.meta.env.VITE_API_KEY ?? 'dev-key-123',
    },
    signal,
  })
}

const client = createClient()

export function apiSignal(signal?: AbortSignal): AxiosRequestConfig {
  return signal ? { signal } : {}
}

export default client
