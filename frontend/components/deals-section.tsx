"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Star, ShoppingCart, Clock, Flame } from "lucide-react"

const dealGames = [
  {
    id: 1,
    title: "Warrior's Path: Complete Edition",
    image: "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=800&h=600&fit=crop",
    price: 19.99,
    originalPrice: 79.99,
    rating: 4.9,
    endTime: new Date(Date.now() + 24 * 60 * 60 * 1000),
  },
  {
    id: 2,
    title: "Space Colony Builder",
    image: "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?w=800&h=600&fit=crop",
    price: 14.99,
    originalPrice: 49.99,
    rating: 4.7,
    endTime: new Date(Date.now() + 12 * 60 * 60 * 1000),
  },
  {
    id: 3,
    title: "Zombie Survival X",
    image: "https://images.unsplash.com/photo-1478760329108-5c3ed9d495a0?w=800&h=600&fit=crop",
    price: 9.99,
    originalPrice: 39.99,
    rating: 4.5,
    endTime: new Date(Date.now() + 8 * 60 * 60 * 1000),
  },
]

function CountdownTimer({ endTime }: { endTime: Date }) {
  const [timeLeft, setTimeLeft] = useState({
    hours: 0,
    minutes: 0,
    seconds: 0,
  })

  useEffect(() => {
    const timer = setInterval(() => {
      const now = new Date()
      const diff = endTime.getTime() - now.getTime()

      if (diff <= 0) {
        clearInterval(timer)
        return
      }

      setTimeLeft({
        hours: Math.floor(diff / (1000 * 60 * 60)),
        minutes: Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60)),
        seconds: Math.floor((diff % (1000 * 60)) / 1000),
      })
    }, 1000)

    return () => clearInterval(timer)
  }, [endTime])

  return (
    <div className="flex items-center gap-2">
      <Clock className="h-4 w-4 text-accent" />
      <span className="font-mono font-bold text-accent">
        {String(timeLeft.hours).padStart(2, "0")}:
        {String(timeLeft.minutes).padStart(2, "0")}:
        {String(timeLeft.seconds).padStart(2, "0")}
      </span>
    </div>
  )
}

export function DealsSection() {
  return (
    <section className="py-16 lg:py-24 bg-background">
      <div className="container mx-auto px-4">
        <div className="flex items-center gap-3 mb-12">
          <Flame className="h-8 w-8 text-accent" />
          <h2 className="text-3xl md:text-4xl font-black tracking-tight">
            Hot <span className="text-accent">Deals</span>
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {dealGames.map((game) => {
            const discount = Math.round((1 - game.price / game.originalPrice) * 100)
            
            return (
              <div
                key={game.id}
                className="group relative rounded-xl overflow-hidden bg-card border border-border hover:border-accent/50 transition-all duration-300"
              >
                {/* Image */}
                <div className="relative aspect-[4/3] overflow-hidden">
                  <img
                    src={game.image}
                    alt={game.title}
                    className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-card via-card/50 to-transparent" />
                  
                  {/* Discount Badge */}
                  <div className="absolute top-3 left-3">
                    <span className="px-3 py-1.5 rounded-lg bg-accent text-accent-foreground font-black text-lg">
                      -{discount}%
                    </span>
                  </div>
                </div>

                {/* Content */}
                <div className="p-5">
                  {/* Timer */}
                  <div className="mb-3">
                    <CountdownTimer endTime={game.endTime} />
                  </div>

                  {/* Title */}
                  <h3 className="font-bold text-xl mb-2 group-hover:text-accent transition-colors">
                    {game.title}
                  </h3>

                  {/* Rating */}
                  <div className="flex items-center gap-1 mb-4">
                    <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />
                    <span className="text-sm font-semibold">{game.rating}</span>
                  </div>

                  {/* Price & CTA */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl font-black text-accent">${game.price}</span>
                      <span className="text-lg text-muted-foreground line-through">
                        ${game.originalPrice}
                      </span>
                    </div>
                    <Button className="bg-accent text-accent-foreground hover:bg-accent/90">
                      <ShoppingCart className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
