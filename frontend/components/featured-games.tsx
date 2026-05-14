"use client"

import { useEffect, useState } from "react"
import { GameCard } from "./game-card"
import { Button } from "@/components/ui/button"
import { ArrowRight } from "lucide-react"
import { api } from "@/lib/api"
import { fallbackProducts } from "@/lib/fallback-products"

export function FeaturedGames() {
  const [products, setProducts] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/recommend/popular?top_k=8')
      .then(res => {
        if (res.recommendations) {
          setProducts(res.recommendations)
        }
      })
      .catch((error) => {
        console.warn("Backend unavailable, using fallback products.", error)
        setProducts(fallbackProducts.slice(0, 8))
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) return null

  return (
    <section className="py-16 lg:py-24 bg-secondary/30">
      <div className="container mx-auto px-4">
        <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4 mb-12">
          <div>
            <h2 className="text-3xl md:text-4xl font-black tracking-tight mb-4">
              Popular <span className="text-primary">Game Gear</span>
            </h2>
            <p className="text-muted-foreground max-w-xl">
              Products many players view, rate, add to cart, and buy across the gaming catalog.
            </p>
          </div>
          <Button asChild variant="outline" className="border-border hover:bg-secondary w-fit">
            <a href="/products">
              View Catalog
              <ArrowRight className="h-4 w-4 ml-2" />
            </a>
          </Button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {products.map((product) => (
            <GameCard key={product.asin} {...product} />
          ))}
        </div>
      </div>
    </section>
  )
}
