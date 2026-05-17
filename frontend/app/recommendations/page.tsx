"use client"

import { useCallback, useEffect, useState } from "react"
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
  const [contextItems, setContextItems] = useState<any[]>([])
  const [source, setSource] = useState<string>("")
  const [modelSource, setModelSource] = useState<string>("")
  const [loading, setLoading] = useState(true)
  const isPersonalized = source === "personalized"
  const identity = user?.user_id || guestId

  const loadRecommendations = useCallback(() => {
    if (!identity) return
    setLoading(true)
    // Determine the endpoint to call
    const endpoint = `/recommend?top_k=16&user_id=${encodeURIComponent(identity)}`
    // If user is logged in, the auth-context intercepts and adds the token.
    // The backend uses the token to return personalized recommendations.
    
    api.get(endpoint)
      .then((res) => {
        if (res.recommendations) {
          setRecommendations(res.recommendations)
          setContextItems(res.context_items || [])
          setSource(res.source || "popular")
          setModelSource(res.model_source || "")
        }
      })
      .catch(() => {
        console.warn("Backend unavailable, using fallback recommendations.")
        setRecommendations(fallbackProducts)
        setContextItems([])
        setSource("popular")
        setModelSource("")
      })
      .finally(() => setLoading(false))
  }, [identity])

  useEffect(() => {
    loadRecommendations()
  }, [loadRecommendations])

  useEffect(() => {
    const refreshWhenVisible = () => {
      if (document.visibilityState === "visible") {
        loadRecommendations()
      }
    }
    window.addEventListener("focus", loadRecommendations)
    document.addEventListener("visibilitychange", refreshWhenVisible)
    return () => {
      window.removeEventListener("focus", loadRecommendations)
      document.removeEventListener("visibilitychange", refreshWhenVisible)
    }
  }, [loadRecommendations])

  return (
    <main className="min-h-screen bg-background pt-24">
      <Header />
      
      <div className="container mx-auto px-4 py-8">
        {loading ? (
          <div className="flex justify-center items-center py-24">
            <Loader2 className="w-10 h-10 animate-spin text-primary" />
          </div>
        ) : recommendations.length === 0 ? (
          <div className="text-center py-20 bg-secondary/30 rounded-xl border border-border">
            <p className="text-lg text-muted-foreground">Not enough data to generate recommendations yet.</p>
          </div>
        ) : (
          <section className="mb-12">
            <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
              <div className="flex items-start gap-4">
                <div className={`inline-flex shrink-0 items-center justify-center rounded-full p-3 ${
                  isPersonalized ? "bg-primary/10" : "bg-amber-500/10"
                }`}>
                  {isPersonalized ? (
                    <Sparkles className="h-7 w-7 text-primary" />
                  ) : (
                    <TrendingUp className="h-7 w-7 text-amber-500" />
                  )}
                </div>
                <div>
                  <h1 className="text-3xl font-black tracking-tight md:text-4xl">
                    {isPersonalized ? (
                      <>Recommended <span className="text-primary">For You</span></>
                    ) : (
                      <>Trending <span className="text-amber-500">Now</span></>
                    )}
                  </h1>
                  <p className="mt-2 max-w-2xl text-muted-foreground">
                    {isPersonalized
                      ? "Products ranked from the items you viewed most recently, with the Colab model blended with product similarity."
                      : "Popular products loved by our community. Sign in and browse more to get personalized recommendations."}
                  </p>
                  {isPersonalized && contextItems.length > 0 && (
                    <div className="mt-4 flex flex-wrap gap-2">
                      {contextItems.map((item) => (
                        <span
                          key={item.asin}
                          className="max-w-full truncate rounded-full border border-border bg-secondary px-3 py-1 text-xs font-medium text-muted-foreground sm:max-w-72"
                          title={item.title}
                        >
                          Based on: {item.title}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
              <div className="text-sm font-medium text-muted-foreground sm:text-right">
                <p>{recommendations.length} products</p>
                {modelSource && <p className="mt-1">Model: {modelSource}</p>}
              </div>
            </div>

            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {recommendations.map((item) => (
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
