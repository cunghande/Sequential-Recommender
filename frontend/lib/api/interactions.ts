import { apiClient } from "./client"

export type InteractionAction = "view" | "cart" | "purchase" | "like" | "rate"

export const interactionsApi = {
  // Luu hanh vi user de backend cap nhat history va goi y realtime.
  record(payload: { product_asin: string; action_type: InteractionAction; rating?: number; user_id?: string }) {
    return apiClient.post("/interaction", payload)
  },
  // Xoa mot san pham khoi lich su user.
  deleteHistoryItem(userId: string, asin: string) {
    return apiClient.del(`/users/${userId}/history/${asin}`)
  },
  history(userId: string) {
    return apiClient.get(`/users/${userId}/history`)
  },
}

