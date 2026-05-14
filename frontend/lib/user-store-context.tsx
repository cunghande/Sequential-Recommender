"use client"

import React, { createContext, useContext, useEffect, useMemo, useState } from "react"

export type StoreProduct = {
  asin: string
  title: string
  img_url?: string
  image_url?: string
  price: number
  category?: string
  rating?: number
}

export type CartItem = StoreProduct & {
  quantity: number
}

type UserStoreContextType = {
  cart: CartItem[]
  favorites: StoreProduct[]
  cartCount: number
  addToCart: (product: StoreProduct) => void
  removeFromCart: (asin: string) => void
  updateCartQuantity: (asin: string, quantity: number) => void
  clearCart: () => void
  addFavorite: (product: StoreProduct) => void
  removeFavorite: (asin: string) => void
  toggleFavorite: (product: StoreProduct) => void
  isFavorite: (asin: string) => boolean
}

const UserStoreContext = createContext<UserStoreContextType | undefined>(undefined)

function readStorage<T>(key: string, fallback: T): T {
  // Đọc localStorage an toàn để tránh lỗi khi render phía server.
  if (typeof window === "undefined") return fallback
  try {
    const value = window.localStorage.getItem(key)
    return value ? JSON.parse(value) : fallback
  } catch {
    return fallback
  }
}

export function UserStoreProvider({ children }: { children: React.ReactNode }) {
  const [cart, setCart] = useState<CartItem[]>([])
  const [favorites, setFavorites] = useState<StoreProduct[]>([])

  useEffect(() => {
    // Nạp giỏ hàng và yêu thích đã lưu từ lần truy cập trước.
    setCart(readStorage<CartItem[]>("nexus_cart", []))
    setFavorites(readStorage<StoreProduct[]>("nexus_favorites", []))
  }, [])

  useEffect(() => {
    window.localStorage.setItem("nexus_cart", JSON.stringify(cart))
  }, [cart])

  useEffect(() => {
    window.localStorage.setItem("nexus_favorites", JSON.stringify(favorites))
  }, [favorites])

  const addToCart = (product: StoreProduct) => {
    // Nếu sản phẩm đã có trong giỏ, tăng số lượng thay vì thêm dòng mới.
    setCart((items) => {
      const existing = items.find((item) => item.asin === product.asin)
      if (existing) {
        return items.map((item) =>
          item.asin === product.asin ? { ...item, quantity: item.quantity + 1 } : item
        )
      }
      return [...items, { ...product, quantity: 1 }]
    })
  }

  const removeFromCart = (asin: string) => {
    setCart((items) => items.filter((item) => item.asin !== asin))
  }

  const updateCartQuantity = (asin: string, quantity: number) => {
    // Số lượng <= 0 được hiểu là xóa khỏi giỏ.
    if (quantity <= 0) {
      removeFromCart(asin)
      return
    }
    setCart((items) =>
      items.map((item) => (item.asin === asin ? { ...item, quantity } : item))
    )
  }

  const clearCart = () => setCart([])

  const addFavorite = (product: StoreProduct) => {
    setFavorites((items) => {
      if (items.some((item) => item.asin === product.asin)) return items
      return [product, ...items]
    })
  }

  const removeFavorite = (asin: string) => {
    setFavorites((items) => items.filter((item) => item.asin !== asin))
  }

  const toggleFavorite = (product: StoreProduct) => {
    // Dùng một hàm cho cả thêm và bỏ yêu thích trên ProductCard.
    setFavorites((items) =>
      items.some((item) => item.asin === product.asin)
        ? items.filter((item) => item.asin !== product.asin)
        : [product, ...items]
    )
  }

  const value = useMemo(
    () => ({
      cart,
      favorites,
      cartCount: cart.reduce((total, item) => total + item.quantity, 0),
      addToCart,
      removeFromCart,
      updateCartQuantity,
      clearCart,
      addFavorite,
      removeFavorite,
      toggleFavorite,
      isFavorite: (asin: string) => favorites.some((item) => item.asin === asin),
    }),
    [cart, favorites]
  )

  return <UserStoreContext.Provider value={value}>{children}</UserStoreContext.Provider>
}

export function useUserStore() {
  const context = useContext(UserStoreContext)
  if (!context) {
    throw new Error("useUserStore must be used within a UserStoreProvider")
  }
  return context
}
