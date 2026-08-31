"use client"

import { useState } from "react"
import { useLibraryStore } from "@/store/library-store"
import { Library, Eye, EyeOff, LogIn } from "lucide-react"

export function LoginPage() {
  const login = useLibraryStore((s) => s.login)
  const error = useLibraryStore((s) => s.error)
  const status = useLibraryStore((s) => s.status)
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)

  const isLoggingIn = status === "loading"

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!username.trim() || !password.trim()) return
    try {
      await login(username, password)
    } catch {
      // Error is set in store
    }
  }

  return (
    <div className="relative flex min-h-[80vh] items-center justify-center px-4">
      <div className="absolute inset-0 -z-10 overflow-hidden">
        <div className="absolute left-[10%] top-[15%] h-72 w-72 rounded-full bg-primary/5 blur-3xl" />
        <div className="absolute bottom-[10%] right-[15%] h-80 w-80 rounded-full bg-accent/10 blur-3xl" />
      </div>
      <div className="w-full max-w-md">
        <div className="mb-8 flex flex-col items-start gap-3">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-lifted">
            <Library className="h-7 w-7" />
          </div>
          <div>
            <h1 className="font-serif text-[2rem] font-semibold leading-tight tracking-tight">
              Aldenwood Library
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Sign in to access the catalogue and your account.
            </p>
          </div>
        </div>

        <form
          onSubmit={handleSubmit}
          className="rounded-2xl border border-border bg-card p-7 shadow-lifted"
          data-testid="login-form"
        >
          <div className="space-y-4">
            <div>
              <label
                htmlFor="login-username"
                className="mb-2 block text-xs font-medium uppercase tracking-[0.1em] text-muted-foreground"
              >
                Username
              </label>
              <input
                id="login-username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="e.g. admin or member1"
                autoComplete="username"
                required
                data-testid="login-username"
                className="h-11 w-full rounded-lg border border-border bg-background px-3.5 text-sm shadow-card outline-none transition-smooth placeholder:text-muted-foreground/50 focus:border-primary/50 focus:ring-2 focus:ring-primary/15"
              />
            </div>

            <div>
              <label
                htmlFor="login-password"
                className="mb-2 block text-xs font-medium uppercase tracking-[0.1em] text-muted-foreground"
              >
                Password
              </label>
              <div className="relative">
                <input
                  id="login-password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  autoComplete="current-password"
                  required
                  data-testid="login-password"
                  className="h-11 w-full rounded-lg border border-border bg-background px-3.5 pr-10 text-sm shadow-card outline-none transition-smooth placeholder:text-muted-foreground/50 focus:border-primary/50 focus:ring-2 focus:ring-primary/15"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>
          </div>

          {error && (
            <div
              className="mt-4 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-300"
              data-testid="login-error"
              role="alert"
            >
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isLoggingIn || !username.trim() || !password.trim()}
            data-testid="login-submit"
            className="mt-7 flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-3 text-sm font-medium text-primary-foreground shadow-card transition-lift hover:bg-primary/90 hover:shadow-lifted disabled:cursor-not-allowed disabled:opacity-50"
          >
            <LogIn className="h-4 w-4" />
            {isLoggingIn ? "Signing in..." : "Sign in"}
          </button>

          <div className="mt-7 border-t border-border/60 pt-5">
            <p className="text-[11px] uppercase tracking-[0.1em] text-muted-foreground/70">
              Demo credentials
            </p>
            <div className="mt-2.5 grid grid-cols-2 gap-2 text-xs">
              <div className="rounded-lg border border-border/60 bg-secondary/40 px-2.5 py-2">
                <span className="font-medium">Admin:</span> admin / Admin123!
              </div>
              <div className="rounded-lg border border-border/60 bg-secondary/40 px-2.5 py-2">
                <span className="font-medium">Member:</span> member1 / Member123!
              </div>
            </div>
          </div>
        </form>
      </div>
    </div>
  )
}
