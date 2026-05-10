"use client"

import { useEffect, useState } from "react"
import { Header } from "@/components/header"
import { Footer } from "@/components/footer"
import { GameCard } from "@/components/game-card"
import { api } from "@/lib/api"
import { useAuth } from "@/lib/auth-context"
import { fallbackProducts } from "@/lib/fallback-products"
import { Loader2, Sparkles, TrendingUp } from "lucide-react"

export default function RecommendationsPage() {
  const { user, guestId } = useAuth()
  const [recommendations, setRecommendations] = useState<any[]>([])
  const [source, setSource] = useState<string>("")
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Determine the endpoint to call
    let endpoint = '/recommend?top_k=16'
    if (!user?.user_id && guestId) {
      endpoint += `&user_id=${guestId}`
    }
    // If user is logged in, the auth-context intercepts and adds the token.
    // The backend uses the token to return personalized recommendations.
    
    api.get(endpoint)
      .then((res) => {
        if (res.recommendations) {
          setRecommendations(res.recommendations)
          setSource(res.source || "popular")
        }
      })
      .catch((error) => {
        console.warn("Backend unavailable, using fallback recommendations.", error)
        setRecommendations(fallbackProducts)
        setSource("popular")
      })
      .finally(() => setLoading(false))
  }, [user])

  return (
    <main className="min-h-screen bg-background pt-24">
      <Header />
      
      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col items-center text-center mb-12">
          {source === "personalized" ? (
            <>
              <div className="inline-flex items-center justify-center p-3 bg-primary/10 rounded-full mb-4">
                <Sparkles className="w-8 h-8 text-primary" />
              </div>
              <h1 className="text-4xl md:text-5xl font-black tracking-tight mb-4">
                For <span className="text-primary">You</span>
              </h1>
              <p className="text-lg text-muted-foreground max-w-2xl">
                Products perfectly curated by our AI based on your unique taste and viewing history.
              </p>
            </>
          ) : (
            <>
              <div className="inline-flex items-center justify-center p-3 bg-amber-500/10 rounded-full mb-4">
                <TrendingUp className="w-8 h-8 text-amber-500" />
              </div>
              <h1 className="text-4xl md:text-5xl font-black tracking-tight mb-4">
                Trending <span className="text-amber-500">Now</span>
              </h1>
              <p className="text-lg text-muted-foreground max-w-2xl">
                Discover the most popular products loved by our community. Sign in and browse more to get personalized recommendations!
              </p>
            </>
          )}
        </div>

        {loading ? (
          <div className="flex justify-center items-center py-24">
            <Loader2 className="w-10 h-10 animate-spin text-primary" />
          </div>
        ) : recommendations.length === 0 ? (
          <div className="text-center py-20 bg-secondary/30 rounded-xl border border-border">
            <p className="text-lg text-muted-foreground">Not enough data to generate recommendations yet.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
            {recommendations.map((item) => (
              <GameCard key={item.asin} {...item} />
            ))}
          </div>
        )}
      </div>

      <Footer />
    </main>
  )
}
