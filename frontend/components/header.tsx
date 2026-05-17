"use client"

import { useState } from "react"
import Link from "next/link"
import { Search, ShoppingCart, Menu, X, Gamepad2, User, LogOut, Settings, History, Heart, KeyRound, UserRound, Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useAuth } from "@/lib/auth-context"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { usePathname, useRouter } from "next/navigation"
import { useUserStore } from "@/lib/user-store-context"

export function Header() {
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const [searchOpen, setSearchOpen] = useState(false)
  const [search, setSearch] = useState("")
  const { user, logout } = useAuth()
  const { cartCount } = useUserStore()
  const router = useRouter()
  const pathname = usePathname()

  const handleLogout = () => {
    logout()
    router.push("/")
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    const query = search.trim()
    router.push(query ? `/products?search=${encodeURIComponent(query)}` : "/products")
    setSearchOpen(false)
    setIsMenuOpen(false)
  }

  const menuItemClass = "cursor-pointer focus:bg-primary/10 focus:text-primary data-[highlighted]:bg-primary/10 data-[highlighted]:text-primary"
  const navLinkClass = (href: string) =>
    `text-sm transition-colors ${
      pathname === href
        ? "font-bold text-primary hover:text-primary/80"
        : "font-medium text-muted-foreground hover:text-primary"
    }`

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-xl border-b border-border">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16 lg:h-20">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 group">
            <div className="relative flex h-10 w-10 items-center justify-center rounded-xl border border-primary/30 bg-primary/10">
              <Gamepad2 className="h-6 w-6 text-primary transition-transform group-hover:scale-110" />
              <Sparkles className="absolute -right-1 -top-1 h-4 w-4 text-primary" />
            </div>
            <span className="text-xl lg:text-2xl font-bold tracking-tight">
              GAMEGEAR<span className="text-primary">AI</span>
            </span>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden lg:flex items-center gap-8">
            <Link href="/" className={navLinkClass("/")}>
              Home
            </Link>
            <Link href="/recommendations" className={navLinkClass("/recommendations")}>
              AI Picks
            </Link>
            <Link href="/products" className={navLinkClass("/products")}>
              Catalog
            </Link>
            <Link href="/cart" className={navLinkClass("/cart")}>
              Cart
            </Link>
          </nav>

          {/* Desktop Actions */}
          <div className="hidden lg:flex items-center gap-4">
            <div className="relative">
              {searchOpen ? (
                <form onSubmit={handleSearch} className="flex items-center gap-2 animate-in slide-in-from-right-5">
                  <Input
                    type="search"
                    placeholder="Search products..."
                    className="w-64 bg-secondary border-border focus:border-primary"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    autoFocus
                  />
                </form>
              ) : (
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setSearchOpen(true)}
                  className="text-muted-foreground hover:text-primary"
                >
                  <Search className="h-5 w-5" />
                </Button>
              )}
            </div>
            
            <Button asChild variant="ghost" size="icon" className="text-muted-foreground hover:text-primary relative mr-2">
              <Link href="/cart">
                <ShoppingCart className="h-5 w-5" />
                <span className="absolute -top-1 -right-1 h-5 w-5 rounded-full bg-primary text-primary-foreground text-xs flex items-center justify-center font-bold">
                  {cartCount}
                </span>
              </Link>
            </Button>

            {user ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="relative h-10 w-10 rounded-full p-0 hover:bg-primary/10">
                    <Avatar className="h-10 w-10 border border-border bg-secondary text-primary transition-colors hover:border-primary hover:bg-primary/10">
                      <AvatarImage src={user.avatar_url || ""} alt={user.full_name || user.email} />
                      <AvatarFallback className="bg-primary/10 text-primary font-bold">
                        <UserRound className="h-5 w-5" />
                      </AvatarFallback>
                    </Avatar>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent className="w-56 mt-2" align="end" forceMount>
                  <DropdownMenuLabel className="font-normal">
                    <div className="flex flex-col space-y-1">
                      <p className="text-sm font-medium leading-none">{user.full_name || "User"}</p>
                      <p className="text-xs leading-none text-muted-foreground">
                        {user.email}
                      </p>
                    </div>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem asChild className={menuItemClass}>
                    <Link href="/profile">
                      <User className="mr-2 h-4 w-4" />
                      <span>Profile</span>
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild className={menuItemClass}>
                    <Link href="/profile?tab=history">
                      <History className="mr-2 h-4 w-4" />
                      <span>Viewing History</span>
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild className={menuItemClass}>
                    <Link href="/profile?tab=favorites">
                      <Heart className="mr-2 h-4 w-4" />
                      <span>Favorites</span>
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild className={menuItemClass}>
                    <Link href="/profile?tab=password">
                      <KeyRound className="mr-2 h-4 w-4" />
                      <span>Change Password</span>
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild className={menuItemClass}>
                    <Link href="/profile?tab=settings">
                      <Settings className="mr-2 h-4 w-4" />
                      <span>Settings</span>
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleLogout} className="cursor-pointer text-red-500 focus:text-red-500 focus:bg-red-500/10">
                    <LogOut className="mr-2 h-4 w-4" />
                    <span>Log out</span>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <div className="flex items-center gap-3">
                <Button asChild variant="ghost" className="relative h-10 w-10 rounded-full p-0 hover:bg-primary/10">
                  <Link href="/login" aria-label="Sign in">
                    <Avatar className="h-10 w-10 border border-border bg-secondary text-primary transition-colors hover:border-primary hover:bg-primary/10">
                      <AvatarFallback className="bg-primary/10 text-primary">
                        <UserRound className="h-5 w-5" />
                      </AvatarFallback>
                    </Avatar>
                  </Link>
                </Button>
                <Button asChild className="bg-primary text-primary-foreground hover:bg-primary/90 font-semibold">
                  <Link href="/login">Sign In</Link>
                </Button>
              </div>
            )}
          </div>

          {/* Mobile Menu Button */}
          <div className="flex lg:hidden items-center gap-2">
            <Button asChild variant="ghost" size="icon" className="text-muted-foreground relative">
              <Link href="/cart">
                <ShoppingCart className="h-5 w-5" />
                <span className="absolute -top-1 -right-1 h-4 w-4 rounded-full bg-primary text-primary-foreground text-xs flex items-center justify-center font-bold">
                  {cartCount}
                </span>
              </Link>
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="text-muted-foreground"
            >
              {isMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </Button>
          </div>
        </div>

        {/* Mobile Menu */}
        {isMenuOpen && (
          <div className="lg:hidden py-4 border-t border-border animate-in slide-in-from-top-5 bg-background">
            <form onSubmit={handleSearch} className="mb-4">
              <Input
                type="search"
                placeholder="Search products..."
                className="w-full bg-secondary border-border"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </form>
            <nav className="flex flex-col gap-4">
              <Link href="/" className={navLinkClass("/")}>
                Home
              </Link>
              <Link href="/recommendations" className={navLinkClass("/recommendations")}>
                AI Picks
              </Link>
              <Link href="/products" className={navLinkClass("/products")}>
                Catalog & Categories
              </Link>
              
              {user ? (
                <>
                  <div className="h-px bg-border my-2" />
                  <div className="flex items-center gap-3 mb-2">
                    <Avatar className="h-10 w-10 border border-border bg-secondary text-primary">
                      <AvatarImage src={user.avatar_url || ""} />
                      <AvatarFallback className="bg-primary/10 text-primary">
                        <UserRound className="h-5 w-5" />
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex flex-col">
                      <span className="font-semibold text-sm">{user.full_name || "User"}</span>
                      <span className="text-xs text-muted-foreground">{user.email}</span>
                    </div>
                  </div>
                  <Link href="/profile" className="text-sm font-medium text-muted-foreground hover:text-primary">
                    Profile & History
                  </Link>
                  <Link href="/profile?tab=favorites" className="text-sm font-medium text-muted-foreground hover:text-primary">
                    Favorites
                  </Link>
                  <Link href="/cart" className="text-sm font-medium text-muted-foreground hover:text-primary">
                    Cart
                  </Link>
                  <Button variant="outline" className="w-full justify-start text-red-500 border-red-500/20 hover:bg-red-500/10 hover:text-red-500" onClick={handleLogout}>
                    <LogOut className="mr-2 h-4 w-4" />
                    Log out
                  </Button>
                </>
              ) : (
                <div className="flex items-center gap-3 mt-2">
                  <Avatar className="h-10 w-10 border border-border bg-secondary text-primary">
                    <AvatarFallback className="bg-primary/10 text-primary">
                      <UserRound className="h-5 w-5" />
                    </AvatarFallback>
                  </Avatar>
                  <Button asChild className="bg-primary text-primary-foreground hover:bg-primary/90 font-semibold">
                    <Link href="/login">Sign In</Link>
                  </Button>
                </div>
              )}
            </nav>
          </div>
        )}
      </div>
    </header>
  )
}
