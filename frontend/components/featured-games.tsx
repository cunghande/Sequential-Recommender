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
              Featured <span className="text-primary">Products</span>
            </h2>
            <p className="text-muted-foreground max-w-xl">
              Handpicked selection of the most popular and highly-rated products in our store.
            </p>
          </div>
          <Button variant="outline" className="border-border hover:bg-secondary w-fit">
            View All Products
            <ArrowRight className="h-4 w-4 ml-2" />
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
