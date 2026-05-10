"use client"

import { useEffect, useState } from "react"
import { Swords, Rocket, Car, Puzzle, Users, Trophy, Gamepad, Ghost } from "lucide-react"
import { api } from "@/lib/api"

const icons = [Swords, Rocket, Car, Puzzle, Users, Trophy, Gamepad, Ghost]
const colors = [
  "from-red-500/20 to-orange-500/20",
  "from-blue-500/20 to-cyan-500/20",
  "from-yellow-500/20 to-amber-500/20",
  "from-green-500/20 to-emerald-500/20",
  "from-pink-500/20 to-rose-500/20",
  "from-orange-500/20 to-amber-500/20",
  "from-indigo-500/20 to-blue-500/20",
  "from-gray-500/20 to-slate-500/20"
]

export function CategoriesSection() {
  const [categories, setCategories] = useState<{name: string, icon: any, color: string}[]>([])

  useEffect(() => {
    api.get('/products/categories').then(res => {
      if (res.categories) {
        const mapped = res.categories.slice(0, 8).map((catName: string, index: number) => ({
          name: catName,
          icon: icons[index % icons.length],
          color: colors[index % colors.length]
        }))
        setCategories(mapped)
      }
    }).catch(console.error)
  }, [])

  if (categories.length === 0) return null

  return (
    <section className="py-16 lg:py-24 bg-background">
      <div className="container mx-auto px-4">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-black tracking-tight mb-4">
            Browse by <span className="text-primary">Category</span>
          </h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Discover products across all categories. Find exactly what you are looking for.
          </p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {categories.map((category) => {
            const Icon = category.icon
            return (
              <button
                key={category.name}
                className="group relative p-6 rounded-xl bg-card border border-border hover:border-primary/50 transition-all duration-300 overflow-hidden"
              >
                <div className={`absolute inset-0 bg-gradient-to-br ${category.color} opacity-0 group-hover:opacity-100 transition-opacity`} />
                <div className="relative z-10">
                  <Icon className="h-10 w-10 mb-4 text-muted-foreground group-hover:text-primary transition-colors" />
                  <h3 className="font-bold text-lg mb-1">{category.name}</h3>
                </div>
              </button>
            )
          })}
        </div>
      </div>
    </section>
  )
}
