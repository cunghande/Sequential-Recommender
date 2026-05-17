"use client"

import { useState } from "react"
import Link from "next/link"
import { Header } from "@/components/header"
import { Footer } from "@/components/footer"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useUserStore } from "@/lib/user-store-context"
import { useAuth } from "@/lib/auth-context"
import { api } from "@/lib/api"
import { Minus, Plus, Trash2, ShoppingBag } from "lucide-react"

export default function CartPage() {
  const { cart, removeFromCart, updateCartQuantity, clearCart } = useUserStore()
  const { user, guestId } = useAuth()
  const [isCheckingOut, setIsCheckingOut] = useState(false)
  const subtotal = cart.reduce((total, item) => total + Number(item.price || 0) * item.quantity, 0)

  const handleCheckout = async () => {
    setIsCheckingOut(true)
    await Promise.all(
      cart.map((item) =>
        api.post("/interaction", {
          product_asin: item.asin,
          action_type: "purchase",
          user_id: user?.user_id || guestId,
        }).catch(() => console.warn("Could not save purchase interaction.")),
      ),
    )
    clearCart()
    setIsCheckingOut(false)
  }

  return (
    <main className="min-h-screen bg-background pt-24">
      <Header />
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8 flex items-center justify-between gap-4">
          <div>
            <h1 className="text-4xl md:text-5xl font-black tracking-tight">
              Shopping <span className="text-primary">Cart</span>
            </h1>
            <p className="mt-3 text-muted-foreground">{cart.length} product types in your cart.</p>
          </div>
          {cart.length > 0 && (
            <Button variant="outline" onClick={clearCart}>
              Clear Cart
            </Button>
          )}
        </div>

        {cart.length === 0 ? (
          <div className="rounded-xl border border-border bg-secondary/30 py-20 text-center">
            <ShoppingBag className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
            <p className="text-lg text-muted-foreground">Your cart is empty.</p>
            <Button asChild className="mt-5">
              <Link href="/products">Browse Products</Link>
            </Button>
          </div>
        ) : (
          <div className="grid gap-8 lg:grid-cols-[1fr_360px]">
            <div className="space-y-4">
              {cart.map((item) => {
                const image =
                  item.img_url ||
                  item.image_url ||
                  `https://placehold.co/200x140/1e293b/64748b?text=${encodeURIComponent(item.title)}`
                return (
                  <div key={item.asin} className="grid gap-4 rounded-xl border border-border bg-card p-4 sm:grid-cols-[140px_1fr_auto]">
                    <Link href={`/product/${item.asin}`} className="block overflow-hidden rounded-lg bg-secondary">
                      <img src={image} alt={item.title} className="h-32 w-full object-cover sm:h-full" />
                    </Link>
                    <div>
                      <Link href={`/product/${item.asin}`} className="text-lg font-bold hover:text-primary">
                        {item.title}
                      </Link>
                      <p className="mt-1 text-sm text-muted-foreground">{item.category || "General"}</p>
                      <p className="mt-4 text-xl font-black text-primary">
                        ${Number(item.price || 0).toFixed(2)}
                      </p>
                    </div>
                    <div className="flex items-center gap-2 sm:flex-col sm:items-end sm:justify-between">
                      <div className="flex items-center gap-2">
                        <Button
                          size="icon"
                          variant="outline"
                          onClick={() => updateCartQuantity(item.asin, item.quantity - 1)}
                        >
                          <Minus className="h-4 w-4" />
                        </Button>
                        <Input
                          value={item.quantity}
                          onChange={(e) => updateCartQuantity(item.asin, Number(e.target.value) || 1)}
                          className="h-10 w-16 text-center"
                        />
                        <Button
                          size="icon"
                          variant="outline"
                          onClick={() => updateCartQuantity(item.asin, item.quantity + 1)}
                        >
                          <Plus className="h-4 w-4" />
                        </Button>
                      </div>
                      <Button variant="ghost" className="text-red-500 hover:text-red-500" onClick={() => removeFromCart(item.asin)}>
                        <Trash2 className="mr-2 h-4 w-4" />
                        Remove
                      </Button>
                    </div>
                  </div>
                )
              })}
            </div>

            <aside className="h-fit rounded-xl border border-border bg-card p-5">
              <h2 className="mb-5 text-xl font-bold">Order Summary</h2>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Subtotal</span>
                  <span>${subtotal.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Shipping</span>
                  <span>Calculated later</span>
                </div>
                <div className="border-t border-border pt-3 text-lg font-black">
                  <div className="flex justify-between">
                    <span>Total</span>
                    <span className="text-primary">${subtotal.toFixed(2)}</span>
                  </div>
                </div>
              </div>
              <Button className="mt-6 w-full" onClick={handleCheckout}>Checkout</Button>
            </aside>
          </div>
        )}
      </div>
      <Footer />
    </main>
  )
}
