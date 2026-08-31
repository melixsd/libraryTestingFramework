"use client"

import { useLibraryStore } from "@/store/library-store"
import { cn } from "@/lib/utils"
import { Library, User, PenTool, Shield, LogOut } from "lucide-react"
import { motion } from "framer-motion"
import { InitialAvatar } from "@/components/shared/initial-avatar"
import { springSnappy } from "@/lib/motion"

export function Header() {
  const currentView = useLibraryStore((s) => s.currentView)
  const currentUser = useLibraryStore((s) => s.currentUser)
  const logout = useLibraryStore((s) => s.logout)
  const setView = useLibraryStore((s) => s.setView)

  const role = currentUser?.role ?? "member"
  const isAdmin = role === "admin" || role === "librarian"
  const isMember = role === "member"
  const initials = currentUser
    ? currentUser.username.slice(0, 2).toUpperCase()
    : "??"

  return (
    <header
      className="sticky top-0 z-40 border-b border-border/60 bg-background/80 backdrop-blur-md"
      data-testid="app-header"
    >
      <div className="mx-auto flex h-16 max-w-7xl items-center gap-3 px-4 sm:px-6 lg:px-8">
        <motion.button
          whileHover={{ rotate: -3, scale: 1.04 }}
          whileTap={{ scale: 0.94 }}
          transition={springSnappy}
          onClick={() => setView("home")}
          className="group flex items-center gap-2.5"
          aria-label="Go to home"
          data-testid="nav-home"
        >
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-card transition-lift group-hover:shadow-lifted">
            <Library className="h-5 w-5" />
          </div>
          <div className="hidden flex-col leading-tight sm:flex">
            <span className="font-serif text-base font-semibold tracking-tight">
              Aldenwood Library
            </span>
            <span className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
              Est. 1894
            </span>
          </div>
        </motion.button>

        {/* Primary nav */}
        <nav className="ml-6 hidden items-center gap-1 md:flex" aria-label="Primary">
          <NavButton
            label="Browse"
            active={currentView === "home" || currentView === "book-detail"}
            onClick={() => setView("home")}
            testId="nav-browse"
          />
          {isMember && (
            <NavButton
              label="My Profile"
              active={currentView === "member-profile"}
              onClick={() => setView("member-profile")}
              testId="nav-profile"
            />
          )}
          <NavButton
            label="Authors"
            active={currentView === "author-profile"}
            onClick={() => setView("author-profile")}
            testId="nav-authors"
          />
          {isAdmin && (
            <NavButton
              label="Admin"
              active={currentView === "admin"}
              onClick={() => setView("admin")}
              testId="nav-admin"
            />
          )}
          {isAdmin && (
            <NavButton
              label="Test Results"
              active={currentView === "test-results"}
              onClick={() => setView("test-results")}
              testId="nav-test-results"
            />
          )}
        </nav>

        <div className="flex-1" />

        <div className="hidden items-center gap-2.5 sm:flex">
          <RoleBadge role={role} />
          <motion.div
            whileHover={{ y: -1 }}
            transition={springSnappy}
            className="flex items-center gap-2 rounded-full border border-border bg-card/60 py-1 pl-1 pr-3 shadow-card"
          >
            <InitialAvatar initials={initials} size="sm" />
            <div className="flex flex-col leading-tight">
              <span className="text-xs font-medium">{currentUser?.username}</span>
              <span className="text-[10px] text-muted-foreground capitalize">
                {role.toLowerCase()}
              </span>
            </div>
          </motion.div>
          <motion.button
            whileHover={{ y: -1 }}
            whileTap={{ scale: 0.96 }}
            transition={springSnappy}
            onClick={logout}
            className="flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-muted-foreground transition-smooth hover:border-primary/30 hover:bg-accent hover:text-foreground"
            aria-label="Sign out"
            data-testid="btn-logout"
          >
            <LogOut className="h-3.5 w-3.5" />
            <span className="hidden lg:inline">Sign out</span>
          </motion.button>
        </div>
      </div>

      {/* Mobile nav */}
      <div
        className="flex items-center gap-1 overflow-x-auto border-t border-border/40 px-4 py-2 md:hidden scrollbar-warm"
        data-testid="mobile-nav"
      >
        <NavButton
          label="Browse"
          active={currentView === "home" || currentView === "book-detail"}
          onClick={() => setView("home")}
          compact
          testId="mobile-nav-browse"
        />
        {isMember && (
          <NavButton
            label="Profile"
            active={currentView === "member-profile"}
            onClick={() => setView("member-profile")}
            compact
            testId="mobile-nav-profile"
          />
        )}
        <NavButton
          label="Authors"
          active={currentView === "author-profile"}
          onClick={() => setView("author-profile")}
          compact
          testId="mobile-nav-authors"
        />
        {isAdmin && (
          <NavButton
            label="Admin"
            active={currentView === "admin"}
            onClick={() => setView("admin")}
            compact
            testId="mobile-nav-admin"
          />
        )}
        {isAdmin && (
          <NavButton
            label="Tests"
            active={currentView === "test-results"}
            onClick={() => setView("test-results")}
            compact
            testId="mobile-nav-test-results"
          />
        )}
        <div className="flex-1" />
        <button
          onClick={logout}
          className="rounded-md px-3 py-1.5 text-xs font-medium text-muted-foreground hover:bg-accent hover:text-foreground"
          data-testid="mobile-btn-logout"
        >
          Sign out
        </button>
      </div>
    </header>
  )
}

function RoleBadge({ role }: { role: string }) {
  const config: Record<string, { label: string; icon: React.ComponentType<{ className?: string }> }> = {
    admin: { label: "Admin", icon: Shield },
    librarian: { label: "Librarian", icon: PenTool },
    member: { label: "Member", icon: User },
  }
  const { label, icon: Icon } = config[role] ?? config.member
  return (
    <span
      className="inline-flex items-center gap-1 rounded-full border border-border bg-card/60 px-2.5 py-1 text-[11px] font-medium text-muted-foreground"
      data-testid={`role-badge-${role.toLowerCase()}`}
    >
      <Icon className="h-3 w-3" />
      {label}
    </span>
  )
}

function NavButton({
  label,
  active,
  onClick,
  compact,
  testId,
}: {
  label: string
  active: boolean
  onClick: () => void
  compact?: boolean
  testId?: string
}) {
  return (
    <button
      onClick={onClick}
      data-testid={testId}
      aria-current={active ? "page" : undefined}
      className={cn(
        "relative rounded-md text-sm font-medium transition-smooth cursor-pointer",
        compact ? "px-3 py-1.5" : "px-3 py-2",
        active
          ? "text-primary"
          : "text-muted-foreground hover:text-foreground",
      )}
    >
      {label}
      {active && (
        <motion.span
          layoutId={compact ? "mobile-nav-underline" : "nav-underline"}
          className="absolute -bottom-px left-2 right-2 h-0.5 rounded-full bg-primary"
          transition={{ type: "spring", stiffness: 380, damping: 30 }}
        />
      )}
    </button>
  )
}
