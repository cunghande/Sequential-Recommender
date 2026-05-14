"use client"

import { Star, ShoppingCart, Heart } from "lucide-react"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { useSearchParams } from "next/navigation"
import { useUserStore } from "@/lib/user-store-context"
import { useAuth } from "@/lib/auth-context"
import { api } from "@/lib/api"

interface GameCardProps {
  asin: string
  title: string
  img_url?: string
  image_url?: string
  price: number
  category?: string
  rating?: number
}

export function GameCard({ asin, title, img_url, image_url, price, category, rating = 4.5 }: GameCardProps) {
  const { addToCart, isFavorite, toggleFavorite } = useUserStore()
  const { user, guestId } = useAuth()
  const searchParams = useSearchParams()
  const image = img_url || image_url || `https://placehold.co/800x500/1e293b/64748b?text=${encodeURIComponent(title)}`
  const product = { asin, title, img_url, image_url, price, category, rating }
  const wishlisted = isFavorite(asin)
  const currentQuery = searchParams.toString()
  const productHref = currentQuery
    ? `/product/${asin}?from=${encodeURIComponent(`/products?${currentQuery}`)}`
    : `/product/${asin}`

  const recordInteraction = (actionType: "cart" | "like") => {
    api.post("/interaction", {
      product_asin: asin,
      action_type: actionType,
      user_id: user?.user_id || guestId,
    }).catch((error) => console.warn("Could not save product interaction.", error))
  }

  return (
    <div className="group relative rounded-xl overflow-hidden bg-card border border-border hover:border-primary/50 transition-all duration-300">
      {/* Image */}
      <Link href={productHref}>
        <div className="relative aspect-[16/10] overflow-hidden cursor-pointer">
          <img
            src={image}
            alt={title}
            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-card via-transparent to-transparent" />
        </div>
      </Link>

      {/* Wishlist Button */}
      <button
        onClick={() => {
          toggleFavorite(product)
          if (!wishlisted) recordInteraction("like")
        }}
        className={`absolute top-3 right-3 p-2 rounded-full transition-all ${
          wishlisted 
            ? "bg-accent text-accent-foreground" 
            : "bg-background/80 text-muted-foreground hover:text-primary"
        }`}
        title={wishlisted ? "Remove from favorites" : "Add to favorites"}
      >
        <Heart className={`h-4 w-4 ${wishlisted ? "fill-current" : ""}`} />
      </button>

      {/* Content */}
      <div className="p-4">
        {/* Category Tag */}
        {category && (
          <div className="flex flex-wrap gap-1 mb-2">
            <span className="px-2 py-0.5 rounded text-xs text-muted-foreground bg-secondary">
              {category}
            </span>
          </div>
        )}

        {/* Title */}
        <Link href={productHref}>
          <h3 className="font-bold text-lg mb-2 line-clamp-1 group-hover:text-primary transition-colors cursor-pointer" title={title}>
            {title}
          </h3>
        </Link>

        {/* Rating */}
        <div className="flex items-center gap-1 mb-3">
          <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />
          <span className="text-sm font-semibold">{rating.toFixed(1)}</span>
        </div>

        {/* Price & CTA */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xl font-black text-primary">${price > 0 ? Number(price).toFixed(2) : "99.99"}</span>
          </div>
          <Button
            size="sm"
            className="bg-primary text-primary-foreground hover:bg-primary/90"
            onClick={() => {
              addToCart(product)
              recordInteraction("cart")
            }}
          >
            <ShoppingCart className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}
