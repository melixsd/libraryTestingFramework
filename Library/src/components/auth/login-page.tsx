"use client"

import { useEffect, useState } from "react"
import { useLibraryStore } from "@/store/library-store"
import { Library, Eye, EyeOff, LogIn, UserPlus, CheckCircle2, ArrowLeft } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { cn } from "@/lib/utils"
import { fadeUp, springSoft } from "@/lib/motion"

type AuthMode = "login" | "signup"

export function LoginPage() {
  const login = useLibraryStore((s) => s.login)
  const error = useLibraryStore((s) => s.error)
  const status = useLibraryStore((s) => s.status)
  const [mode, setMode] = useState<AuthMode>("login")
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
        <motion.div
          aria-hidden
          animate={{ y: [0, -14, 0], x: [0, 6, 0] }}
          transition={{ duration: 11, repeat: Infinity, ease: "easeInOut" }}
          className="absolute left-[10%] top-[15%] h-72 w-72 rounded-full bg-primary/5 blur-3xl"
        />
        <motion.div
          aria-hidden
          animate={{ y: [0, 12, 0], x: [0, -8, 0] }}
          transition={{ duration: 13, repeat: Infinity, ease: "easeInOut" }}
          className="absolute bottom-[10%] right-[15%] h-80 w-80 rounded-full bg-accent/10 blur-3xl"
        />
      </div>
      <div className="w-full max-w-md">
        <motion.div
          variants={fadeUp}
          initial="hidden"
          animate="show"
          className="mb-8 flex flex-col items-start gap-3"
        >
          <motion.div
            whileHover={{ rotate: -4, scale: 1.05 }}
            transition={springSoft}
            className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-lifted"
          >
            <Library className="h-7 w-7" />
          </motion.div>
          <div>
            <h1 className="font-serif text-[2rem] font-semibold leading-tight tracking-tight">
              Aldenwood Library
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Sign in to access the catalogue and your account.
            </p>
          </div>
        </motion.div>

        {/* Mode toggle */}
        <div
          className="mb-4 grid grid-cols-2 gap-1 rounded-xl border border-border bg-card p-1 shadow-card"
          data-testid="auth-mode-toggle"
        >
          <AuthModeButton
            active={mode === "login"}
            onClick={() => setMode("login")}
            icon={<LogIn className="h-3.5 w-3.5" />}
            label="Sign in"
            testId="auth-mode-login"
          />
          <AuthModeButton
            active={mode === "signup"}
            onClick={() => setMode("signup")}
            icon={<UserPlus className="h-3.5 w-3.5" />}
            label="Sign up"
            testId="auth-mode-signup"
          />
        </div>

        <AnimatePresence mode="wait">
          {mode === "login" ? (
            <motion.div
              key="login"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8, transition: { duration: 0.15 } }}
              transition={springSoft}
            >
              <LoginForm
                username={username}
                setUsername={setUsername}
                password={password}
                setPassword={setPassword}
                showPassword={showPassword}
                setShowPassword={setShowPassword}
                isLoggingIn={isLoggingIn}
                error={error}
                onSubmit={handleSubmit}
              />
            </motion.div>
          ) : (
            <motion.div
              key="signup"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8, transition: { duration: 0.15 } }}
              transition={springSoft}
            >
              <SignupForm onBackToLogin={() => setMode("login")} />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}

/* ───────────────────────────  LOGIN  ─────────────────────────── */

function LoginForm({
  username,
  setUsername,
  password,
  setPassword,
  showPassword,
  setShowPassword,
  isLoggingIn,
  error,
  onSubmit,
}: {
  username: string
  setUsername: (v: string) => void
  password: string
  setPassword: (v: string) => void
  showPassword: boolean
  setShowPassword: (v: boolean) => void
  isLoggingIn: boolean
  error: string | null
  onSubmit: (e: React.FormEvent) => void
}) {
  return (
    <motion.form
      onSubmit={onSubmit}
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ ...springSoft, delay: 0.08 }}
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
        <motion.div
          initial={{ opacity: 0, y: -6, scale: 0.98 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={springSoft}
          className="mt-4 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-300"
          data-testid="login-error"
          role="alert"
        >
          {error}
        </motion.div>
      )}

      <motion.button
        type="submit"
        disabled={isLoggingIn || !username.trim() || !password.trim()}
        whileHover={{ scale: isLoggingIn ? 1 : 1.015 }}
        whileTap={{ scale: isLoggingIn ? 1 : 0.98 }}
        transition={springSoft}
        data-testid="login-submit"
        className="mt-7 flex w-full cursor-pointer items-center justify-center gap-2 rounded-lg bg-primary px-4 py-3 text-sm font-medium text-primary-foreground shadow-card transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
      >
        <LogIn className="h-4 w-4" />
        {isLoggingIn ? "Signing in..." : "Sign in"}
      </motion.button>

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
    </motion.form>
  )
}

/* ───────────────────────────  SIGNUP  ─────────────────────────── */

function SignupForm({ onBackToLogin }: { onBackToLogin: () => void }) {
  const register = useLibraryStore((s) => s.register)
  const membershipTypes = useLibraryStore((s) => s.membershipTypes)
  const fetchMembershipTypes = useLibraryStore((s) => s.fetchMembershipTypes)

  const [fullName, setFullName] = useState("")
  const [username, setUsername] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [planId, setPlanId] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState("")
  const [registered, setRegistered] = useState(false)

  // The plan list endpoint is public, so it can be fetched while signed out.
  useEffect(() => {
    fetchMembershipTypes()
  }, [fetchMembershipTypes])

  // Default to the first available plan until the user picks one explicitly.
  const effectivePlanId = planId || (membershipTypes[0] ? String(membershipTypes[0].id) : "")

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setFormError("")
    if (!fullName.trim() || !username.trim() || !email.trim() || !password || !effectivePlanId) {
      setFormError("Please fill in every field.")
      return
    }
    setSubmitting(true)
    try {
      await register({
        username: username.trim(),
        email: email.trim(),
        password,
        full_name: fullName.trim(),
        membership_type_id: parseInt(effectivePlanId),
      })
      setRegistered(true)
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Registration failed")
    } finally {
      setSubmitting(false)
    }
  }

  if (registered) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ ...springSoft, delay: 0.08 }}
        className="rounded-2xl border border-border bg-card p-7 shadow-lifted"
        data-testid="signup-success"
      >
        <div className="flex flex-col items-center py-4 text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-950/40">
            <CheckCircle2 className="h-7 w-7 text-emerald-600 dark:text-emerald-400" />
          </div>
          <h2 className="mt-4 font-serif text-xl font-semibold tracking-tight">
            Registration received
          </h2>
          <p className="mt-2 max-w-xs text-sm text-muted-foreground">
            Your membership request has been sent to the library administrators.
            You can sign in as soon as your account has been approved.
          </p>
          <button
            onClick={onBackToLogin}
            data-testid="signup-success-back"
            className="mt-6 inline-flex cursor-pointer items-center gap-1.5 rounded-lg border border-border px-4 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to sign in
          </button>
        </div>
      </motion.div>
    )
  }

  return (
    <motion.form
      onSubmit={handleSubmit}
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ ...springSoft, delay: 0.08 }}
      className="rounded-2xl border border-border bg-card p-7 shadow-lifted"
      data-testid="signup-form"
    >
      <div className="space-y-4">
        <div>
          <label
            htmlFor="signup-name"
            className="mb-2 block text-xs font-medium uppercase tracking-[0.1em] text-muted-foreground"
          >
            Full name
          </label>
          <input
            id="signup-name"
            type="text"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="e.g. Jane Whitfield"
            autoComplete="name"
            required
            data-testid="signup-name"
            className="h-11 w-full rounded-lg border border-border bg-background px-3.5 text-sm shadow-card outline-none transition-smooth placeholder:text-muted-foreground/50 focus:border-primary/50 focus:ring-2 focus:ring-primary/15"
          />
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label
              htmlFor="signup-username"
              className="mb-2 block text-xs font-medium uppercase tracking-[0.1em] text-muted-foreground"
            >
              Username
            </label>
            <input
              id="signup-username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g. jane.w"
              autoComplete="username"
              required
              data-testid="signup-username"
              className="h-11 w-full rounded-lg border border-border bg-background px-3.5 text-sm shadow-card outline-none transition-smooth placeholder:text-muted-foreground/50 focus:border-primary/50 focus:ring-2 focus:ring-primary/15"
            />
          </div>
          <div>
            <label
              htmlFor="signup-email"
              className="mb-2 block text-xs font-medium uppercase tracking-[0.1em] text-muted-foreground"
            >
              Email
            </label>
            <input
              id="signup-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="jane@example.com"
              autoComplete="email"
              required
              data-testid="signup-email"
              className="h-11 w-full rounded-lg border border-border bg-background px-3.5 text-sm shadow-card outline-none transition-smooth placeholder:text-muted-foreground/50 focus:border-primary/50 focus:ring-2 focus:ring-primary/15"
            />
          </div>
        </div>

        <div>
          <label
            htmlFor="signup-password"
            className="mb-2 block text-xs font-medium uppercase tracking-[0.1em] text-muted-foreground"
          >
            Password
          </label>
          <div className="relative">
            <input
              id="signup-password"
              type={showPassword ? "text" : "password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="At least 6 characters"
              autoComplete="new-password"
              required
              minLength={6}
              data-testid="signup-password"
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

        <div>
          <label
            htmlFor="signup-plan"
            className="mb-2 block text-xs font-medium uppercase tracking-[0.1em] text-muted-foreground"
          >
            Membership plan
          </label>
          <select
            id="signup-plan"
            value={effectivePlanId}
            onChange={(e) => setPlanId(e.target.value)}
            required
            data-testid="signup-plan"
            className="h-11 w-full cursor-pointer rounded-lg border border-border bg-background px-3 text-sm shadow-card outline-none transition-smooth focus:border-primary/50 focus:ring-2 focus:ring-primary/15"
          >
            {membershipTypes.length === 0 && <option value="">Loading plans…</option>}
            {membershipTypes.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
          <p className="mt-2 text-xs text-muted-foreground/70">
            New memberships are activated after an administrator approves your request.
          </p>
        </div>
      </div>

      {formError && (
        <motion.div
          initial={{ opacity: 0, y: -6, scale: 0.98 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={springSoft}
          className="mt-4 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-300"
          data-testid="signup-error"
          role="alert"
        >
          {formError}
        </motion.div>
      )}

      <motion.button
        type="submit"
        disabled={
          submitting ||
          !fullName.trim() ||
          !username.trim() ||
          !email.trim() ||
          !password ||
          !effectivePlanId
        }
        whileHover={{ scale: submitting ? 1 : 1.015 }}
        whileTap={{ scale: submitting ? 1 : 0.98 }}
        transition={springSoft}
        data-testid="signup-submit"
        className="mt-7 flex w-full cursor-pointer items-center justify-center gap-2 rounded-lg bg-primary px-4 py-3 text-sm font-medium text-primary-foreground shadow-card transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
      >
        <UserPlus className="h-4 w-4" />
        {submitting ? "Submitting..." : "Create account"}
      </motion.button>
    </motion.form>
  )
}

/* ───────────────────────────  SHARED  ─────────────────────────── */

function AuthModeButton({
  active,
  onClick,
  icon,
  label,
  testId,
}: {
  active: boolean
  onClick: () => void
  icon: React.ReactNode
  label: string
  testId: string
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      data-testid={testId}
      aria-pressed={active}
      className={cn(
        "flex cursor-pointer items-center justify-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
        active
          ? "bg-primary text-primary-foreground shadow-card"
          : "text-muted-foreground hover:text-foreground",
      )}
    >
      {icon}
      {label}
    </button>
  )
}
