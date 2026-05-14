"use client"

import Link from "next/link"
import { Button } from "@/components/ui/button"
import { BrainCircuit, PackageCheck, ShoppingCart, Sparkles, TrendingUp } from "lucide-react"

const commerceFeatures = [
  {
    title: "AI picks from real behavior",
    description: "New players see popular gear first. Returning users get suggestions from views, likes, cart actions, ratings, and purchases.",
    icon: BrainCircuit,
  },
  {
    title: "Full gaming catalog",
    description: "Browse games, Nintendo, PlayStation, Xbox, controllers, headsets, gift cards, subscriptions, and accessories from the database.",
    icon: PackageCheck,
  },
  {
    title: "Cart-ready shopping flow",
    description: "Every product detail page connects to cart, favorites, history, and realtime recommendation updates.",
    icon: ShoppingCart,
  },
]

export function DealsSection() {
  return (
    <section className="py-16 lg:py-24 bg-background">
      <div className="container mx-auto px-4">
        <div className="mb-12 grid gap-6 lg:grid-cols-[1fr_360px] lg:items-end">
          <div>
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-4 py-2 text-sm font-semibold text-primary">
              <Sparkles className="h-4 w-4" />
              Built for gaming commerce
            </div>
            <h2 className="text-3xl md:text-4xl font-black tracking-tight">
              Shop smarter with <span className="text-primary">GameGear AI</span>
            </h2>
            <p className="mt-4 max-w-2xl text-muted-foreground">
              This storefront is more than a product grid: it learns from user behavior and turns the catalog into personalized shopping paths.
            </p>
          </div>
          <div className="rounded-xl border border-primary/20 bg-primary/10 p-5">
            <div className="mb-2 flex items-center gap-2 text-primary">
              <TrendingUp className="h-5 w-5" />
              <span className="text-sm font-bold uppercase tracking-wide">Recommendation engine</span>
            </div>
            <p className="text-sm text-muted-foreground">
              Popular products for new users. Personalized sequences for returning users.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {commerceFeatures.map((feature) => {
            const Icon = feature.icon
            return (
              <div
                key={feature.title}
                className="group rounded-xl border border-border bg-card p-6 transition-all duration-300 hover:border-primary/50"
              >
                <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary">
                  <Icon className="h-6 w-6" />
                </div>
                <h3 className="mb-2 text-xl font-bold group-hover:text-primary">{feature.title}</h3>
                <p className="text-sm leading-6 text-muted-foreground">{feature.description}</p>
              </div>
            )
          })}
        </div>

        <div className="mt-10 flex flex-wrap gap-3">
          <Button asChild className="bg-primary text-primary-foreground hover:bg-primary/90">
            <Link href="/products">Browse Catalog</Link>
          </Button>
          <Button asChild variant="outline">
            <Link href="/recommendations">View AI Picks</Link>
          </Button>
        </div>
      </div>
    </section>
  )
}
