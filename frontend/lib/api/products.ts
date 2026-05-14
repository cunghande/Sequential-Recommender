import { apiClient } from "./client"

export const productsApi = {
  // Lay danh sach san pham co filter, search va phan trang.
  list(params: { category?: string; search?: string; page?: number; limit?: number } = {}) {
    const searchParams = new URLSearchParams()
    if (params.category) searchParams.set("category", params.category)
    if (params.search) searchParams.set("search", params.search)
    if (params.page) searchParams.set("page", String(params.page))
    if (params.limit) searchParams.set("limit", String(params.limit))
    const query = searchParams.toString()
    return apiClient.get(`/products${query ? `?${query}` : ""}`)
  },
  // Lay danh sach category tu database.
  categories() {
    return apiClient.get("/products/categories")
  },
  // Lay chi tiet mot san pham theo ASIN.
  detail(asin: string) {
    return apiClient.get(`/products/${asin}`)
  },
}

