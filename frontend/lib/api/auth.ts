import { apiClient } from "./client"

export type LoginPayload = {
  email: string
  password: string
}

export type RegisterPayload = LoginPayload & {
  full_name: string
}

export const authApi = {
  // Goi API dang nhap va tra token + user cho AuthContext.
  login(payload: LoginPayload) {
    return apiClient.post("/auth/login", payload)
  },
  // Tao tai khoan moi va dang nhap ngay sau khi backend tra token.
  register(payload: RegisterPayload) {
    return apiClient.post("/auth/register", payload)
  },
  // Lay lai thong tin user tu JWT hien tai.
  me() {
    return apiClient.get("/auth/me")
  },
  // Cap nhat ten hien thi/avatar trong trang profile.
  updateProfile(payload: { full_name: string; avatar_url?: string }) {
    return apiClient.put("/auth/profile", payload)
  },
  logout() {
    return apiClient.post("/auth/logout", {})
  },
}

