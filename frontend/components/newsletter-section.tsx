"use client"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Mail, Zap } from "lucide-react"

export function NewsletterSection() {
  return (
    <section className="py-16 lg:py-24 bg-secondary/30 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 opacity-30">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-accent/20 rounded-full blur-3xl" />
      </div>

      <div className="container mx-auto px-4 relative z-10">
        <div className="max-w-3xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 mb-6">
            <Zap className="h-4 w-4 text-primary" />
            <span className="text-sm font-semibold text-primary">Gaming commerce updates</span>
          </div>

          <h2 className="text-3xl md:text-5xl font-black tracking-tight mb-4">
            Get drops for your <span className="text-primary">setup</span>
          </h2>
          
          <p className="text-lg text-muted-foreground mb-8 max-w-xl mx-auto">
            Subscribe for new gear, console accessories, gift cards, and product picks matched to how you shop.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 max-w-md mx-auto">
            <div className="relative flex-1">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
              <Input
                type="email"
                placeholder="Enter your email"
                className="pl-10 h-12 bg-card border-border focus:border-primary"
              />
            </div>
            <Button className="bg-primary text-primary-foreground hover:bg-primary/90 font-bold h-12 px-8">
              Subscribe
            </Button>
          </div>

          <p className="text-xs text-muted-foreground mt-4">
            No spam, unsubscribe at any time. By subscribing, you agree to our Privacy Policy.
          </p>
        </div>
      </div>
    </section>
  )
}
