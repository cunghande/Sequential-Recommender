"use client"

import { useEffect, useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { Header } from "@/components/header"
import { Footer } from "@/components/footer"
import { GameCard } from "@/components/game-card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { useAuth } from "@/lib/auth-context"
import { useUserStore } from "@/lib/user-store-context"
import { api } from "@/lib/api"
import { Heart, History, KeyRound, Loader2, Settings, Trash2, Upload, UserRound } from "lucide-react"

export default function ProfilePage() {
  const { user, updateUser, token } = useAuth()
  const { favorites, removeFavorite } = useUserStore()
  const router = useRouter()
  const searchParams = useSearchParams()
  const tab = searchParams.get("tab") || "history"

  const [history, setHistory] = useState<any[]>([])
  const [loadingHistory, setLoadingHistory] = useState(false)
  
  // Profile Form
  const [fullName, setFullName] = useState(user?.full_name || "")
  const [avatarUrl, setAvatarUrl] = useState(user?.avatar_url || "")
  const [profileMsg, setProfileMsg] = useState("")

  // Password Form
  const [oldPassword, setOldPassword] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [passMsg, setPassMsg] = useState("")
  const [passErr, setPassErr] = useState("")
  const [savingPass, setSavingPass] = useState(false)

  useEffect(() => {
    if (!token) {
      router.push("/login")
      return
    }

    if (user?.user_id) {
      setLoadingHistory(true)
      api.get(`/users/${user.user_id}/history`)
        .then((res) => {
          if (res.history) setHistory(res.history)
        })
        .catch(console.error)
        .finally(() => setLoadingHistory(false))
    }
  }, [user, token, router])

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault()
    setProfileMsg("")
    try {
      await api.put("/auth/profile", { full_name: fullName, avatar_url: avatarUrl })
      updateUser({ full_name: fullName, avatar_url: avatarUrl })
      setProfileMsg("Profile updated successfully!")
      setTimeout(() => setProfileMsg(""), 3000)
    } catch (err: any) {
      updateUser({ full_name: fullName, avatar_url: avatarUrl })
      setProfileMsg("Saved locally. Backend is not available right now.")
      setTimeout(() => setProfileMsg(""), 3000)
      console.error(err)
    }
  }

  const handleAvatarUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = () => {
      const value = String(reader.result || "")
      setAvatarUrl(value)
      updateUser({ avatar_url: value })
    }
    reader.readAsDataURL(file)
  }

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setPassMsg("")
    setPassErr("")
    setSavingPass(true)
    try {
      await api.post("/auth/change-password", { old_password: oldPassword, new_password: newPassword })
      setPassMsg("Password changed successfully!")
      setOldPassword("")
      setNewPassword("")
    } catch (err: any) {
      setPassErr(err.response?.data?.detail || "Failed to change password.")
    } finally {
      setSavingPass(false)
    }
  }

  const handleDeleteHistory = async (asin: string) => {
    if (!user) return
    try {
      const res = await api.del(`/users/${user.user_id}/history/${asin}`)
      if (res.history) setHistory(res.history)
    } catch (err) {
      console.error(err)
    }
  }

  if (!user) return null

  return (
    <main className="min-h-screen bg-background pt-24">
      <Header />
      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col md:flex-row items-center md:items-start gap-8 mb-12">
          <Avatar className="w-32 h-32 border-4 border-primary/20">
            <AvatarImage src={user.avatar_url || ""} />
            <AvatarFallback className="text-4xl bg-primary/10 text-primary font-black">
              <UserRound className="h-14 w-14" />
            </AvatarFallback>
          </Avatar>
          <div className="text-center md:text-left mt-4 md:mt-0">
            <h1 className="text-4xl font-black">{user.full_name || "Nexus User"}</h1>
            <p className="text-lg text-muted-foreground mt-2">{user.email}</p>
            <div className="mt-4 inline-block px-3 py-1 rounded-full text-xs font-semibold bg-primary/20 text-primary border border-primary/30">
              Pro Member
            </div>
          </div>
        </div>

        <Tabs defaultValue={tab} className="w-full">
          <TabsList className="grid w-full grid-cols-2 gap-1 md:w-[720px] md:grid-cols-4 mb-8 bg-secondary border-border h-auto p-1">
            <TabsTrigger value="history" className="gap-2 text-sm data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
              <History className="h-4 w-4" />
              History
            </TabsTrigger>
            <TabsTrigger value="favorites" className="gap-2 text-sm data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
              <Heart className="h-4 w-4" />
              Favorites
            </TabsTrigger>
            <TabsTrigger value="password" className="gap-2 text-sm data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
              <KeyRound className="h-4 w-4" />
              Password
            </TabsTrigger>
            <TabsTrigger value="settings" className="gap-2 text-sm data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
              <Settings className="h-4 w-4" />
              Settings
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="history" className="animate-in fade-in-50 duration-500">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold">Recently Viewed</h2>
              <span className="text-muted-foreground">{history.length} items</span>
            </div>
            
            {loadingHistory ? (
              <div className="flex justify-center py-12"><Loader2 className="w-8 h-8 animate-spin text-primary" /></div>
            ) : history.length === 0 ? (
              <div className="text-center py-20 bg-secondary/30 rounded-xl border border-border">
                <p className="text-lg text-muted-foreground">You haven't viewed any products yet.</p>
                <Button className="mt-4" onClick={() => router.push("/")}>Browse Store</Button>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                {history.map((item) => (
                  <div key={item.asin} className="relative group">
                    <GameCard {...item} />
                    <button 
                      onClick={(e) => { e.preventDefault(); handleDeleteHistory(item.asin); }}
                      className="absolute top-3 left-3 p-2 rounded-full bg-red-500/80 text-white opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-500"
                      title="Remove from history"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="favorites" className="animate-in fade-in-50 duration-500">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold">Favorite Products</h2>
              <span className="text-muted-foreground">{favorites.length} items</span>
            </div>

            {favorites.length === 0 ? (
              <div className="text-center py-20 bg-secondary/30 rounded-xl border border-border">
                <Heart className="mx-auto mb-4 h-10 w-10 text-muted-foreground" />
                <p className="text-lg text-muted-foreground">Products you rate 4 stars or higher will appear here.</p>
                <Button className="mt-4" onClick={() => router.push("/products")}>Browse Products</Button>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                {favorites.map((item) => (
                  <div key={item.asin} className="relative group">
                    <GameCard {...item} />
                    <button
                      onClick={() => removeFavorite(item.asin)}
                      className="absolute top-3 left-3 p-2 rounded-full bg-red-500/80 text-white opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-500"
                      title="Remove from favorites"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="password" className="animate-in fade-in-50 duration-500">
            <Card className="max-w-xl bg-card/50 backdrop-blur-xl border-border">
              <CardHeader>
                <CardTitle>Change Password</CardTitle>
                <CardDescription>Update the password used with your user/email login.</CardDescription>
              </CardHeader>
              <form onSubmit={handleChangePassword}>
                <CardContent className="space-y-4">
                  {passMsg && <div className="text-green-500 text-sm bg-green-500/10 p-3 rounded">{passMsg}</div>}
                  {passErr && <div className="text-red-500 text-sm bg-red-500/10 p-3 rounded">{passErr}</div>}
                  <div className="space-y-2">
                    <Label htmlFor="oldPassword">Current Password</Label>
                    <Input id="oldPassword" type="password" required value={oldPassword} onChange={(e) => setOldPassword(e.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="newPassword">New Password</Label>
                    <Input id="newPassword" type="password" required value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
                  </div>
                </CardContent>
                <CardFooter>
                  <Button type="submit" variant="secondary" disabled={savingPass}>
                    {savingPass ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
                    Update Password
                  </Button>
                </CardFooter>
              </form>
            </Card>
          </TabsContent>
          
          <TabsContent value="settings" className="space-y-8 animate-in fade-in-50 duration-500">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <Card className="bg-card/50 backdrop-blur-xl border-border">
                <CardHeader>
                  <CardTitle>Profile Information</CardTitle>
                  <CardDescription>Update your personal details and avatar.</CardDescription>
                </CardHeader>
                <form onSubmit={handleUpdateProfile}>
                  <CardContent className="space-y-4">
                    {profileMsg && <div className="text-green-500 text-sm bg-green-500/10 p-3 rounded">{profileMsg}</div>}
                    <div className="space-y-2">
                      <Label htmlFor="fullName">Full Name</Label>
                      <Input id="fullName" value={fullName} onChange={(e) => setFullName(e.target.value)} />
                    </div>
                    <div className="space-y-3">
                      <Label>Avatar</Label>
                      <div className="flex items-center gap-4">
                        <Avatar className="h-20 w-20 border border-border">
                          <AvatarImage src={avatarUrl || ""} />
                          <AvatarFallback className="bg-primary/10 text-primary">
                            <UserRound className="h-8 w-8" />
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <Input
                            id="avatarFile"
                            type="file"
                            accept="image/*"
                            onChange={handleAvatarUpload}
                            className="hidden"
                          />
                          <Button type="button" variant="outline" asChild>
                            <Label htmlFor="avatarFile" className="cursor-pointer">
                              <Upload className="mr-2 h-4 w-4" />
                              Upload Image
                            </Label>
                          </Button>
                        </div>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="avatarUrl">Avatar URL (Optional)</Label>
                      <Input id="avatarUrl" placeholder="https://..." value={avatarUrl} onChange={(e) => setAvatarUrl(e.target.value)} />
                    </div>
                  </CardContent>
                  <CardFooter>
                    <Button type="submit">Save Changes</Button>
                  </CardFooter>
                </form>
              </Card>

              <Card className="bg-card/50 backdrop-blur-xl border-border">
                <CardHeader>
                  <CardTitle>Recommendation Settings</CardTitle>
                  <CardDescription>Viewing history and high ratings are used to update realtime recommendations.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4 text-sm text-muted-foreground">
                  <p>Product views are added when you open a product detail page.</p>
                  <p>Ratings of 4 stars or higher are saved as strong preference signals and added to favorites.</p>
                  <p>You can remove viewed products from the History tab to refresh the recommendation sequence.</p>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
      <Footer />
    </main>
  )
}
