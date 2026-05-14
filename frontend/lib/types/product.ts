export type Product = {
  asin: string
  title: string
  category?: string
  price?: number
  rating?: number
  img_url?: string
  image_url?: string
  score?: number
}

export type ProductListResponse = {
  total: number
  page: number
  limit: number
  products: Product[]
}

