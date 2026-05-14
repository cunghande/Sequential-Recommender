"use client"

import { useEffect, useState } from "react"
import { useParams, useSearchParams } from "next/navigation"
import { Header } from "@/components/header"
import { Footer } from "@/components/footer"
import { GameCard } from "@/components/game-card"
import { Button } from "@/components/ui/button"
import { Star, ShoppingCart, Heart, ArrowLeft, X } from "lucide-react"
import { api } from "@/lib/api"
import { useAuth } from "@/lib/auth-context"
import { fallbackProducts, findFallbackProduct } from "@/lib/fallback-products"
import { useUserStore } from "@/lib/user-store-context"
import Link from "next/link"
import { useRouter } from "next/navigation"

export default function ProductDetailPage() {
  const { asin } = useParams()
  const router = useRouter()
  const searchParams = useSearchParams()
  const returnTo = searchParams.get("from") || "/products"
  const { user, guestId } = useAuth()
  const { addToCart, addFavorite, isFavorite, toggleFavorite } = useUserStore()
  const [product, setProduct] = useState<any>(null)
  const [similar, setSimilar] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [rating, setRating] = useState(0)

  useEffect(() => {
    if (!asin) return

    // Load product detail
    api.get(`/products/${asin}`)
      .then(res => setProduct(res))
      .catch((error) => {
        console.warn("Backend unavailable, using fallback product.", error)
        setProduct(findFallbackProduct(String(asin)))
      })
      .finally(() => setLoading(false))

    // Record view interaction
    const payload: any = { product_asin: asin, action_type: 'view' }
    if (user?.user_id) {
      payload.user_id = user.user_id
    } else {
      payload.user_id = guestId // Fallback for anonymous
    }
    
    api.post('/interaction', payload)
      .catch(console.error)

    // Load similar products. The sequence endpoint expects numeric item ids, so use popular
    // recommendations here because this route receives a product asin string.
    api.get('/recommend/popular?top_k=4')
      .then(res => {
        if (res.recommendations) setSimilar(res.recommendations)
      })
      .catch((error) => {
        console.warn("Backend unavailable, using fallback similar products.", error)
        setSimilar(fallbackProducts.filter((item) => item.asin !== asin).slice(0, 4))
      })

  }, [asin])

  if (loading) {
    return (
      <main className="min-h-screen bg-background pt-24">
        <Header />
        <div className="flex items-center justify-center min-h-[60vh]">Loading...</div>
        <Footer />
      </main>
    )
  }

  if (!product) {
    return (
      <main className="min-h-screen bg-background pt-24">
        <Header />
        <div className="flex items-center justify-center min-h-[60vh] text-xl">Product not found</div>
        <Footer />
      </main>
    )
  }

  const image = product.img_url || product.image_url || `https://placehold.co/800x800/1e293b/64748b?text=${encodeURIComponent(product.title)}`

  const handleRating = async (value: number) => {
    setRating(value)
    if (value >= 4) {
      addFavorite(product)
    }
    try {
      await api.post('/interaction', {
        product_asin: product.asin,
        action_type: 'rate',
        rating: value,
        user_id: user?.user_id || guestId,
      })
    } catch (error) {
      console.warn("Could not save rating interaction.", error)
    }
  }

  const handleAddToCart = () => {
    addToCart(product)
    api.post('/interaction', {
      product_asin: product.asin,
      action_type: 'cart',
      user_id: user?.user_id || guestId,
    }).catch((error) => console.warn("Could not save cart interaction.", error))
  }

  const handleToggleFavorite = () => {
    const wasFavorite = isFavorite(product.asin)
    toggleFavorite(product)
    if (!wasFavorite) {
      api.post('/interaction', {
        product_asin: product.asin,
        action_type: 'like',
        user_id: user?.user_id || guestId,
      }).catch((error) => console.warn("Could not save like interaction.", error))
    }
  }

  const closeProduct = () => {
    router.push(returnTo)
  }

  return (
    <main className="min-h-screen bg-background pt-24">
      <Header />
      
      <div className="container mx-auto px-4 py-8">
        <div className="mb-6 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Button
              type="button"
              variant="outline"
              size="icon"
              className="h-10 w-10 rounded-full border-border text-muted-foreground hover:border-primary hover:bg-primary/10 hover:text-primary"
              onClick={closeProduct}
              aria-label="Close product detail"
              title="Close"
            >
              <X className="h-5 w-5" />
            </Button>
            <Link href={returnTo} className="inline-flex items-center text-muted-foreground hover:text-primary transition-colors">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Products
            </Link>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 mb-16">
          {/* Product Image */}
          <div className="relative aspect-square md:aspect-[4/3] rounded-2xl overflow-hidden bg-card border border-border">
            <img 
              src={image} 
              alt={product.title} 
              className="w-full h-full object-contain p-4"
            />
          </div>

          {/* Product Info */}
          <div className="flex flex-col justify-center">
            <div className="mb-4 flex flex-wrap gap-2">
              <span className="px-3 py-1 rounded-full text-xs font-semibold bg-primary/20 text-primary border border-primary/30">
                {product.category || "General"}
              </span>
            </div>

            <h1 className="text-3xl md:text-5xl font-black tracking-tight mb-4">{product.title}</h1>
            
            <div className="flex items-center gap-4 mb-6">
              <div className="flex items-center gap-1">
                {[1, 2, 3, 4, 5].map(star => (
                  <Star 
                    key={star} 
                    className={`w-5 h-5 cursor-pointer transition-colors ${star <= (rating || product.rating || 4.5) ? 'text-yellow-500 fill-yellow-500' : 'text-muted-foreground'}`}
                    onClick={() => handleRating(star)}
                  />
                ))}
                <span className="ml-2 font-semibold text-lg">{rating || product.rating || 4.5}</span>
              </div>
            </div>

            <div className="text-4xl font-black text-primary mb-8">
              ${product.price > 0 ? Number(product.price).toFixed(2) : "99.99"}
            </div>

            <p className="text-lg text-muted-foreground mb-8 leading-relaxed">
              This premium product belongs to the {product.category} category. We guarantee the best quality and seamless delivery right to your doorstep. Experience the excellence today!
            </p>

            <div className="flex flex-wrap gap-4">
              <Button
                size="lg"
                className="bg-primary text-primary-foreground hover:bg-primary/90 font-bold text-lg px-8 h-14 flex-1"
                onClick={handleAddToCart}
              >
                <ShoppingCart className="w-5 h-5 mr-2" /> Add to Cart
              </Button>
              <Button
                size="icon"
                variant="outline"
                className="border-border hover:bg-secondary h-14 w-14 rounded-xl"
                onClick={handleToggleFavorite}
                title={isFavorite(product.asin) ? "Remove from favorites" : "Add to favorites"}
              >
                <Heart className={`w-6 h-6 ${isFavorite(product.asin) ? "fill-current text-accent" : ""}`} />
              </Button>
            </div>
          </div>
        </div>

        {/* Similar Products */}
        {similar.length > 0 && (
          <section className="py-12 border-t border-border">
            <h2 className="text-3xl font-black mb-8">You Might Also <span className="text-primary">Like</span></h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {similar.map(item => (
                <GameCard key={item.asin} {...item} />
              ))}
            </div>
          </section>
        )}
      </div>

      <Footer />
    </main>
  )
}
