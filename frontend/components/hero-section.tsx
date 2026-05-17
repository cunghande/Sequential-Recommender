"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { ChevronLeft, ChevronRight, Star, ShieldCheck } from "lucide-react"
import { api } from "@/lib/api"
import { fallbackProducts } from "@/lib/fallback-products"

export function HeroSection() {
  const [featuredGames, setFeaturedGames] = useState<any[]>([])
  const [currentSlide, setCurrentSlide] = useState(0)
  const [isAutoPlaying, setIsAutoPlaying] = useState(true)

  useEffect(() => {
    api.get('/recommend/popular?top_k=3')
      .then(res => {
        if (res.recommendations) {
          setFeaturedGames(res.recommendations)
        }
      })
      .catch(() => {
        console.warn("Backend unavailable, using fallback hero products.")
        setFeaturedGames(fallbackProducts.slice(0, 3))
      })
  }, [])

  useEffect(() => {
    if (!isAutoPlaying || featuredGames.length === 0) return
    const timer = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % featuredGames.length)
    }, 5000)
    return () => clearInterval(timer)
  }, [isAutoPlaying, featuredGames.length])

  if (featuredGames.length === 0) {
    return <div className="min-h-screen bg-background flex items-center justify-center">Loading...</div>
  }

  const nextSlide = () => {
    setCurrentSlide((prev) => (prev + 1) % featuredGames.length)
    setIsAutoPlaying(false)
  }

  const prevSlide = () => {
    setCurrentSlide((prev) => (prev - 1 + featuredGames.length) % featuredGames.length)
    setIsAutoPlaying(false)
  }

  const game = featuredGames[currentSlide]

  return (
    <section className="relative min-h-screen flex items-center pt-16 lg:pt-20 overflow-hidden">
      {/* Background Image */}
      <div className="absolute inset-0">
        {featuredGames.map((g, index) => (
          <div
            key={g.asin || index}
            className={`absolute inset-0 transition-opacity duration-1000 ${
              index === currentSlide ? "opacity-100" : "opacity-0"
            }`}
          >
            <img
              src={g.img_url || g.image_url || `https://placehold.co/1920x1080/1e293b/64748b?text=${encodeURIComponent(g.title)}`}
              alt={g.title}
              className="w-full h-full object-cover opacity-50"
            />
            <div className="absolute inset-0 bg-gradient-to-r from-background via-background/80 to-transparent" />
            <div className="absolute inset-0 bg-gradient-to-t from-background via-transparent to-transparent" />
          </div>
        ))}
      </div>

      {/* Content */}
      <div className="container mx-auto px-4 relative z-10">
        <div className="max-w-2xl">
          {/* Tags */}
          <div className="flex flex-wrap gap-2 mb-4">
            <span className="px-3 py-1 rounded-full text-xs font-semibold bg-primary/20 text-primary border border-primary/30">
              {game.category || "General"}
            </span>
            <span className="px-3 py-1 rounded-full text-xs font-semibold bg-primary/20 text-primary border border-primary/30">
              Game Commerce
            </span>
          </div>

          {/* Title */}
          <h1 className="text-4xl md:text-6xl lg:text-7xl font-black tracking-tight mb-4 text-balance">
            {game.title}
          </h1>

          {/* Description */}
          <p className="text-lg md:text-xl text-muted-foreground mb-6 leading-relaxed text-pretty">
            Shop games, consoles, controllers, headsets, cards, and accessories with recommendations that adapt to every click.
          </p>

          {/* Meta Info */}
          <div className="flex flex-wrap items-center gap-6 mb-8">
            <div className="flex items-center gap-2">
              <Star className="h-5 w-5 text-yellow-500 fill-yellow-500" />
              <span className="font-semibold">{game.rating ? Number(game.rating).toFixed(1) : "4.8"}</span>
              <span className="text-muted-foreground">/5</span>
            </div>
            <div className="flex items-center gap-2 text-muted-foreground">
              <ShieldCheck className="h-5 w-5" />
              <span>Secure checkout</span>
            </div>
          </div>

          {/* Pricing */}
          <div className="flex items-center gap-4 mb-8">
            <span className="text-3xl md:text-4xl font-black text-primary">
              ${game.price > 0 ? Number(game.price).toFixed(2) : "99.99"}
            </span>
          </div>

          {/* CTA Buttons */}
          <div className="flex flex-wrap gap-4">
            <Button size="lg" className="bg-primary text-primary-foreground hover:bg-primary/90 font-bold text-lg px-8 h-14" onClick={() => window.location.href = `/product/${game.asin}`}>
              Shop Product
            </Button>
          </div>
        </div>

        {/* Slide Navigation */}
        <div className="absolute bottom-8 right-4 md:right-8 flex items-center gap-4">
          <div className="hidden md:flex items-center gap-2 mr-4">
            {featuredGames.map((_, index) => (
              <button
                key={index}
                onClick={() => {
                  setCurrentSlide(index)
                  setIsAutoPlaying(false)
                }}
                className={`w-12 h-1 rounded-full transition-all ${
                  index === currentSlide
                    ? "bg-primary"
                    : "bg-muted-foreground/30 hover:bg-muted-foreground/50"
                }`}
              />
            ))}
          </div>
          <Button
            variant="outline"
            size="icon"
            onClick={prevSlide}
            className="border-border hover:bg-secondary rounded-full h-12 w-12"
          >
            <ChevronLeft className="h-5 w-5" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            onClick={nextSlide}
            className="border-border hover:bg-secondary rounded-full h-12 w-12"
          >
            <ChevronRight className="h-5 w-5" />
          </Button>
        </div>
      </div>
    </section>
  )
}
