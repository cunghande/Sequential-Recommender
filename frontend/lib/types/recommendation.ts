import type { Product } from "./product"

export type RecommendationSource = "popular" | "personalized" | "realtime_demo"

export type RecommendationResponse = {
  source?: RecommendationSource
  recommendations: Product[]
}

