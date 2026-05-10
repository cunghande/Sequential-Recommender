import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000';

// Helper to get token from localStorage dynamically
const getAuthHeaders = () => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('nexus_token');
    if (token) {
      return { Authorization: `Bearer ${token}` };
    }
  }
  return {};
};

export const api = {
  get: async (url: string) => {
    try {
      const response = await axios.get(`${API_BASE_URL}${url}`, { headers: getAuthHeaders() });
      return response.data;
    } catch (error) {
      console.error(`API GET error on ${url}:`, error);
      throw error;
    }
  },
  post: async (url: string, data: any) => {
    try {
      const response = await axios.post(`${API_BASE_URL}${url}`, data, { headers: getAuthHeaders() });
      return response.data;
    } catch (error) {
      console.error(`API POST error on ${url}:`, error);
      throw error;
    }
  },
  put: async (url: string, data: any) => {
    try {
      const response = await axios.put(`${API_BASE_URL}${url}`, data, { headers: getAuthHeaders() });
      return response.data;
    } catch (error) {
      console.error(`API PUT error on ${url}:`, error);
      throw error;
    }
  },
  del: async (url: string) => {
    try {
      const response = await axios.delete(`${API_BASE_URL}${url}`, { headers: getAuthHeaders() });
      return response.data;
    } catch (error) {
      console.error(`API DELETE error on ${url}:`, error);
      throw error;
    }
  }
};
