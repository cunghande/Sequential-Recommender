import axios from "axios"

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8001"

export function getAuthHeaders() {
  // Lay JWT moi nhat tu localStorage cho moi request phia client.
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("nexus_token")
    if (token) return { Authorization: `Bearer ${token}` }
  }
  return {}
}

export const apiClient = {
  async get(url: string) {
    const response = await axios.get(`${API_BASE_URL}${url}`, { headers: getAuthHeaders() })
    return response.data
  },
  async post(url: string, data: unknown) {
    const response = await axios.post(`${API_BASE_URL}${url}`, data, { headers: getAuthHeaders() })
    return response.data
  },
  async put(url: string, data: unknown) {
    const response = await axios.put(`${API_BASE_URL}${url}`, data, { headers: getAuthHeaders() })
    return response.data
  },
  async del(url: string) {
    const response = await axios.delete(`${API_BASE_URL}${url}`, { headers: getAuthHeaders() })
    return response.data
  },
}

