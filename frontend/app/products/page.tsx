"use client"

import { useEffect, useMemo, useState } from "react"
import { useSearchParams } from "next/navigation"
import { Header } from "@/components/header"
import { Footer } from "@/components/footer"
import { GameCard } from "@/components/game-card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { api } from "@/lib/api"
import { fallbackProducts } from "@/lib/fallback-products"
import { ChevronLeft, ChevronRight, Loader2, Search } from "lucide-react"

const PAGE_SIZE = 16

export default function ProductsPage() {
  const searchParams = useSearchParams()
  const initialSearch = searchParams.get("search") || ""

  const [products, setProducts] = useState<any[]>([])
  const [categories, setCategories] = useState<string[]>([])
  const [search, setSearch] = useState(initialSearch)
  const [activeCategory, setActiveCategory] = useState("")
  const [currentPage, setCurrentPage] = useState(1)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setSearch(initialSearch)
  }, [initialSearch])

  useEffect(() => {
    let cancelled = false

    async function loadCatalog() {
      setLoading(true)
      try {
        const [productRes, categoryRes] = await Promise.all([
          api.get("/products?limit=10000"),
          api.get("/products/categories"),
        ])
        if (cancelled) return
        setProducts(productRes.products || [])
        setCategories(categoryRes.categories || [])
      } catch (error) {
        console.warn("Backend unavailable, using fallback catalog.", error)
        if (cancelled) return
        setProducts(fallbackProducts)
        setCategories(Array.from(new Set(fallbackProducts.map((item) => item.category))))
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    loadCatalog()
    return () => {
      cancelled = true
    }
  }, [])

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase()
    return products.filter((product) => {
      const matchesSearch =
        !term ||
        product.title?.toLowerCase().includes(term) ||
        product.category?.toLowerCase().includes(term) ||
        product.asin?.toLowerCase().includes(term)
      const matchesCategory = !activeCategory || product.category === activeCategory
      return matchesSearch && matchesCategory
    })
  }, [products, search, activeCategory])

  useEffect(() => {
    setCurrentPage(1)
  }, [search, activeCategory])

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const page = Math.min(currentPage, totalPages)
  const paginatedProducts = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)
  const firstItem = filtered.length === 0 ? 0 : (page - 1) * PAGE_SIZE + 1
  const lastItem = Math.min(page * PAGE_SIZE, filtered.length)
  const visiblePages = Array.from({ length: totalPages }, (_, index) => index + 1).filter(
    (pageNumber) =>
      pageNumber === 1 ||
      pageNumber === totalPages ||
      Math.abs(pageNumber - page) <= 1,
  )

  return (
    <main className="min-h-screen bg-background pt-24">
      <Header />
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8 flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="text-4xl md:text-5xl font-black tracking-tight">
              Product <span className="text-primary">Catalog</span>
            </h1>
            <p className="mt-3 text-muted-foreground">
              Search all products loaded from the database and filter by category.
            </p>
          </div>
          <div className="relative w-full lg:w-96">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by name, category, asin..."
              className="h-11 bg-secondary pl-10"
            />
          </div>
        </div>

        <div className="mb-8 flex gap-2 overflow-x-auto pb-2">
          <Button
            variant={activeCategory ? "outline" : "default"}
            onClick={() => {
              setActiveCategory("")
              setCurrentPage(1)
            }}
            className="shrink-0"
          >
            All
          </Button>
          {categories.map((category) => (
            <Button
              key={category}
              variant={activeCategory === category ? "default" : "outline"}
              onClick={() => {
                setActiveCategory(category)
                setCurrentPage(1)
              }}
              className="shrink-0"
            >
              {category}
            </Button>
          ))}
        </div>

        <div className="mb-6 flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Showing {firstItem}-{lastItem} of {filtered.length} products
          </p>
          {activeCategory && (
            <Button variant="ghost" onClick={() => setActiveCategory("")}>
              Clear category
            </Button>
          )}
        </div>

        {loading ? (
          <div className="flex justify-center py-24">
            <Loader2 className="h-10 w-10 animate-spin text-primary" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="rounded-xl border border-border bg-secondary/30 py-20 text-center">
            <p className="text-lg text-muted-foreground">No products match your search.</p>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {paginatedProducts.map((product) => (
                <GameCard key={product.asin} {...product} />
              ))}
            </div>

            {totalPages > 1 && (
              <div className="mt-10 flex flex-wrap items-center justify-center gap-2">
                <Button
                  variant="outline"
                  disabled={page === 1}
                  onClick={() => setCurrentPage((value) => Math.max(1, value - 1))}
                >
                  <ChevronLeft className="mr-2 h-4 w-4" />
                  Previous
                </Button>
                {visiblePages.map((pageNumber, index) => {
                  const previous = visiblePages[index - 1]
                  return (
                    <div key={pageNumber} className="flex items-center gap-2">
                      {previous && pageNumber - previous > 1 && (
                        <span className="px-2 text-muted-foreground">...</span>
                      )}
                      <Button
                        variant={pageNumber === page ? "default" : "outline"}
                        className="h-10 w-10 p-0"
                        onClick={() => setCurrentPage(pageNumber)}
                      >
                        {pageNumber}
                      </Button>
                    </div>
                  )
                })}
                <Button
                  variant="outline"
                  disabled={page === totalPages}
                  onClick={() => setCurrentPage((value) => Math.min(totalPages, value + 1))}
                >
                  Next
                  <ChevronRight className="ml-2 h-4 w-4" />
                </Button>
              </div>
            )}
          </>
        )}
      </div>
      <Footer />
    </main>
  )
}
