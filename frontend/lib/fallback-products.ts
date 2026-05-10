export type Product = {
  asin: string
  title: string
  img_url: string
  price: number
  category: string
  rating: number
}

export const fallbackProducts: Product[] = [
  {
    asin: "demo-keyboard",
    title: "Mechanical Wireless Keyboard",
    img_url: "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=900&h=600&fit=crop",
    price: 89.99,
    category: "Accessories",
    rating: 4.8,
  },
  {
    asin: "demo-headphones",
    title: "Noise Cancelling Headphones",
    img_url: "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=900&h=600&fit=crop",
    price: 129.99,
    category: "Audio",
    rating: 4.7,
  },
  {
    asin: "demo-camera",
    title: "Compact Mirrorless Camera",
    img_url: "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=900&h=600&fit=crop",
    price: 599.99,
    category: "Photography",
    rating: 4.6,
  },
  {
    asin: "demo-watch",
    title: "Fitness Smart Watch",
    img_url: "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=900&h=600&fit=crop",
    price: 149.99,
    category: "Wearables",
    rating: 4.5,
  },
  {
    asin: "demo-speaker",
    title: "Portable Bluetooth Speaker",
    img_url: "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=900&h=600&fit=crop",
    price: 59.99,
    category: "Audio",
    rating: 4.4,
  },
  {
    asin: "demo-laptop-stand",
    title: "Aluminum Laptop Stand",
    img_url: "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=900&h=600&fit=crop",
    price: 39.99,
    category: "Office",
    rating: 4.6,
  },
  {
    asin: "demo-backpack",
    title: "Everyday Tech Backpack",
    img_url: "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=900&h=600&fit=crop",
    price: 74.99,
    category: "Bags",
    rating: 4.7,
  },
  {
    asin: "demo-monitor",
    title: "27 Inch 4K Productivity Monitor",
    img_url: "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=900&h=600&fit=crop",
    price: 329.99,
    category: "Displays",
    rating: 4.8,
  },
]

export function findFallbackProduct(asin: string) {
  return fallbackProducts.find((product) => product.asin === asin)
}
