import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  headers: {
    'X-API-Key': import.meta.env.VITE_API_KEY ?? 'dev-key-123',
  },
})

export default client
