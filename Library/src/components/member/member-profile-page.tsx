"use client"

import { useEffect } from "react"
import { useLibraryStore } from "@/store/library-store"
import { MemberStatusBadge, MembershipTierBadge } from "@/components/shared/status-badge"
import {
  Mail,
  CalendarDays,
  BookMarked,
  AlertTriangle,
  Clock,
  ArrowUpRight,
  CheckCircle2,
  RefreshCw,
  Loader2,
  Inbox,
  XCircle,
} from "lucide-react"
import { motion } from "framer-motion"
import { cn } from "@/lib/utils"
import { useState } from "react"

export function MemberProfilePage() {
  const currentUser = useLibraryStore((s) => s.currentUser)
  const memberSummary = useLibraryStore((s) => s.memberSummary)
  const fetchMemberSummary = useLibraryStore((s) => s.fetchMemberSummary)
  const summaryStatus = useLibraryStore((s) => s.summaryStatus)
  const summaryError = useLibraryStore((s) => s.summaryError)
  const returnBook = useLibraryStore((s) => s.returnBook)
  const renewBook = useLibraryStore((s) => s.renewBook)
  const selectBook = useLibraryStore((s) => s.selectBook)
  const allBooks = useLibraryStore((s) => s.books)
  const [tab, setTab] = useState<"borrowed" | "reservations">("borrowed")
  const [actionLoading, setActionLoading] = useState<number | null>(null)

  useEffect(() => {
    fetchMemberSummary()
  }, [fetchMemberSummary])

  // Loading state
  if (summaryStatus === "loading" && !memberSummary) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-20 text-center" data-testid="member-profile-page">
        <Loader2 className="mx-auto mb-3 h-8 w-8 animate-spin text-primary" />
        <p className="text-sm text-muted-foreground">Loading your profile…</p>
      </div>
    )
  }

  // Error state
  if (summaryStatus === "error" && !memberSummary) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-20 text-center" data-testid="member-profile-page">
        <XCircle className="mx-auto mb-3 h-10 w-10 text-rose-500" />
        <p className="text-sm font-medium text-rose-600">Failed to load your profile</p>
        <p className="mt-1 text-xs text-muted-foreground">{summaryError ?? "An unexpected error occurred."}</p>
        <button
          onClick={() => fetchMemberSummary()}
          className="mt-4 inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Try again
        </button>
      </div>
    )
  }

  if (!memberSummary?.member) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-20 text-center" data-testid="member-profile-page">
        <Loader2 className="mx-auto mb-3 h-8 w-8 animate-spin text-muted-foreground" />
        <p className="text-muted-foreground">Loading your profile...</p>
      </div>
    )
  }

  const member = memberSummary.member
  const activeBorrows = memberSummary.active_borrows
  const reservations = memberSummary.reservations
  const membership = member.membership_type
  const usagePct =
    membership.max_books > 0
      ? Math.min(Math.round((activeBorrows.length / membership.max_books) * 100), 100)
      : 0

  async function handleReturn(borrowId: number) {
    setActionLoading(borrowId)
    try {
      await returnBook(borrowId)
    } finally {
      setActionLoading(null)
    }
  }

  async function handleRenew(borrowId: number) {
    setActionLoading(borrowId)
    try {
      await renewBook(borrowId)
    } finally {
      setActionLoading(null)
    }
  }

  function getBookForBorrow(borrow: typeof activeBorrows[number]) {
    // Find the book by looking through copies — we need the book title
    // Since borrows reference copies and we don't have copies in the store,
    // we'll display copy_id for now and the borrow details
    return allBooks.find((b) =>
      b.authors.some(() => true), // placeholder — match will come from backend data
    )
  }

  const hasNoData = activeBorrows.length === 0 && reservations.length === 0

  return (
    <div
      className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8"
      data-testid="member-profile-page"
    >
      {/* Profile header */}
      <motion.section
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="overflow-hidden rounded-2xl border border-border bg-card shadow-lifted"
      >
        <div className="h-20 bg-gradient-to-r from-primary via-primary to-primary/80 sm:h-28" />
        <div className="px-5 pb-6 sm:px-8">
          <div className="-mt-10 flex flex-col gap-4 sm:-mt-12 sm:flex-row sm:items-end sm:justify-between">
            <div className="flex flex-col items-start gap-4 sm:flex-row sm:items-end">
              <div
                className="flex h-20 w-20 items-center justify-center rounded-full bg-secondary text-2xl font-bold text-secondary-foreground ring-4 ring-card sm:h-24 sm:w-24"
                data-testid="member-avatar"
              >
                {member.full_name
                  .split(" ")
                  .map((n) => n[0])
                  .join("")
                  .toUpperCase()
                  .slice(0, 2)}
              </div>
              <div className="pb-2">
                <div className="flex flex-wrap items-center gap-2.5">
                  <h1
                    className="font-serif text-[1.75rem] font-semibold tracking-tight sm:text-[2rem]"
                    data-testid="member-name"
                  >
                    {member.full_name}
                  </h1>
                  <MemberStatusBadge isActive={member.is_active} />
                  <MembershipTierBadge tierName={membership.name} />
                </div>
                <p className="mt-1.5 flex items-center gap-1.5 text-sm text-muted-foreground">
                  <Mail className="h-3.5 w-3.5" />
                  {member.email}
                </p>
              </div>
            </div>
          </div>
        </div>
      </motion.section>

      {/* Stats row */}
      <section className="mt-7 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard
          icon={BookMarked}
          label="Borrowed"
          value={`${activeBorrows.length} / ${membership.max_books}`}
          sub={`${usagePct}% of limit`}
        >
          <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full bg-primary"
              style={{ width: `${usagePct}%` }}
              data-testid="borrow-progress"
            />
          </div>
        </StatCard>
        <StatCard
          icon={CalendarDays}
          label="Loan period"
          value={`${membership.loan_period_days} days`}
          sub={`Max ${membership.max_renewals} renewal(s)`}
        />
        <StatCard
          icon={BookMarked}
          label="Reservations"
          value={String(reservations.length)}
          sub="Active reservations"
        />
        <StatCard
          icon={AlertTriangle}
          label="Fines owed"
          value={
            member.outstanding_fine > 0
              ? `$${member.outstanding_fine.toFixed(2)}`
              : "$0.00"
          }
          sub={
            member.outstanding_fine > 0
              ? `$${membership.daily_fine_rate}/day late`
              : "All clear"
          }
          highlight={member.outstanding_fine > 0}
        />
      </section>

      {/* Tabs: Borrowed / Reservations */}
      <section className="mt-8">
        <div
          className="mb-4 flex items-center gap-1 border-b border-border"
          data-testid="member-tabs"
        >
          <TabButton
            label={`Borrowed (${activeBorrows.length})`}
            active={tab === "borrowed"}
            onClick={() => setTab("borrowed")}
            testId="tab-borrowed"
          />
          <TabButton
            label={`Reservations (${reservations.length})`}
            active={tab === "reservations"}
            onClick={() => setTab("reservations")}
            testId="tab-reservations"
          />
        </div>

        {tab === "borrowed" ? (
          activeBorrows.length === 0 ? (
            <EmptyState
              icon={Inbox}
              title="No books currently borrowed"
              hint="Browse the catalogue to find your next read."
            />
          ) : (
            <div
              className="space-y-3"
              data-testid="borrowed-list"
            >
              {activeBorrows.map((borrow, i) => (
                <BorrowedBookRow
                  key={borrow.id}
                  borrow={borrow}
                  index={i}
                  onReturn={handleReturn}
                  onRenew={handleRenew}
                  loading={actionLoading === borrow.id}
                />
              ))}
            </div>
          )
        ) : reservations.length === 0 ? (
          <EmptyState
            icon={Inbox}
            title="No active reservations"
            hint="Reserve a book when all copies are checked out."
          />
        ) : (
          <div className="space-y-3" data-testid="reservations-list">
            {reservations.map((res, i) => (
              <motion.div
                key={res.id}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.25, delay: Math.min(i * 0.05, 0.3) }}
              >
                <div
                  className="flex items-center gap-4 rounded-xl border border-border bg-card p-3 shadow-sm"
                  data-testid={`reservation-${res.id}`}
                >
                  <div className="min-w-0 flex-1">
                    <h3 className="truncate font-serif text-base font-semibold">
                      Book #{res.book_id}
                    </h3>
                    <p className="text-xs text-muted-foreground">
                      Reserved on {formatDate(res.reservation_date)}
                    </p>
                    <span
                      className={cn(
                        "mt-1 inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium",
                        res.status === "WAITING"
                          ? "bg-amber-100 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300"
                          : res.status === "READY"
                            ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300"
                            : "bg-secondary text-secondary-foreground",
                      )}
                    >
                      {res.status}
                    </span>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </section>

      {/* Global empty state when member has no borrows and no reservations */}
      {hasNoData && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.2 }}
          className="mt-8"
        >
          <div className="flex flex-col items-center rounded-2xl border border-dashed border-border bg-card/40 px-6 py-16 text-center">
            <div className="mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-primary/10">
              <Inbox className="h-10 w-10 text-primary/50" />
            </div>
            <h3 className="font-serif text-lg font-semibold">Your library account is empty</h3>
            <p className="mt-1.5 max-w-sm text-sm text-muted-foreground">
              You don't have any borrowed books or active reservations yet.
              Start exploring the catalogue to find something you'll love!
            </p>
            <button
              onClick={() => useLibraryStore.getState().setView("home")}
              className="mt-6 inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
            >
              <BookMarked className="h-4 w-4" />
              Browse the catalogue
            </button>
          </div>
        </motion.div>
      )}
    </div>
  )
}

function StatCard({
  icon: Icon,
  label,
  value,
  sub,
  highlight,
  children,
}: {
  icon: React.ComponentType<{ className?: string }>
  label: string
  value: string
  sub?: string
  highlight?: boolean
  children?: React.ReactNode
}) {
  return (
    <div
      className={cn(
        "rounded-xl border bg-card p-4 shadow-card transition-smooth",
        highlight ? "border-rose-200 dark:border-rose-900" : "border-border",
      )}
    >
      <div className="mb-2.5 flex items-center justify-between">
        <span className="text-[11px] font-medium uppercase tracking-[0.15em] text-muted-foreground/80">
          {label}
        </span>
        <Icon
          className={cn(
            "h-4 w-4",
            highlight ? "text-rose-500" : "text-primary/70",
          )}
        />
      </div>
      <p className="font-serif text-[1.75rem] font-semibold leading-none tracking-tight">{value}</p>
      {sub && <p className="mt-1 text-xs text-muted-foreground/80">{sub}</p>}
      {children}
    </div>
  )
}

function BorrowedBookRow({
  borrow,
  index,
  onReturn,
  onRenew,
  loading,
}: {
  borrow: import("@/lib/types").BorrowOut
  index: number
  onReturn: (id: number) => void
  onRenew: (id: number) => void
  loading: boolean
}) {
  const today = new Date()
  const due = new Date(borrow.due_date)
  const daysLeft = Math.ceil(
    (due.getTime() - today.getTime()) / (1000 * 60 * 60 * 24),
  )
  const overdue = daysLeft < 0

  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.25, delay: Math.min(index * 0.05, 0.3) }}
    >
      <div
        className="flex flex-col gap-3 rounded-xl border border-border bg-card p-4 shadow-card transition-smooth sm:flex-row sm:items-center hover:border-primary/20"
        data-testid={`borrow-${borrow.id}`}
      >
        <div className="min-w-0 flex-1">
          <h3 className="truncate font-serif text-base font-semibold tracking-tight">
            Borrow #{borrow.id} (Copy #{borrow.copy_id})
          </h3>
          <p className="mt-0.5 text-xs text-muted-foreground">
            Borrowed {formatDate(borrow.borrow_date)}
          </p>
          <div className="mt-2.5 flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <CalendarDays className="h-3 w-3" />
              Due {formatDate(borrow.due_date)}
            </span>
            <span
              className={cn(
                "flex items-center gap-1 rounded-full px-2 py-0.5 font-medium",
                overdue
                  ? "bg-rose-100 text-rose-700 dark:bg-rose-950/40 dark:text-rose-300"
                  : daysLeft <= 3
                    ? "bg-amber-100 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300"
                    : "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300",
              )}
              data-testid={`borrow-status-${borrow.id}`}
            >
              {overdue ? (
                <AlertTriangle className="h-3 w-3" />
              ) : daysLeft <= 3 ? (
                <Clock className="h-3 w-3" />
              ) : (
                <CheckCircle2 className="h-3 w-3" />
              )}
              {overdue
                ? `${Math.abs(daysLeft)} days overdue`
                : daysLeft === 0
                  ? "Due today"
                  : `${daysLeft} days left`}
            </span>
            {borrow.renewed_count > 0 && (
              <span className="text-muted-foreground">
                Renewed {borrow.renewed_count}x
              </span>
            )}
            {borrow.fine_amount > 0 && (
              <span className="text-rose-600 font-medium">
                Fine: ${borrow.fine_amount.toFixed(2)}
              </span>
            )}
          </div>
        </div>
        <div className="flex shrink-0 flex-row gap-2 sm:flex-col">
          <button
            onClick={() => onReturn(borrow.id)}
            disabled={loading}
            data-testid={`btn-return-${borrow.id}`}
            className="inline-flex items-center gap-1 rounded-lg border border-border px-3.5 py-1.5 text-xs font-medium transition-smooth hover:border-primary/30 hover:bg-accent disabled:opacity-50"
          >
            {loading ? (
              <RefreshCw className="h-3 w-3 animate-spin" />
            ) : (
              <ArrowUpRight className="h-3 w-3" />
            )}
            Return
          </button>
          {!overdue && (
            <button
              onClick={() => onRenew(borrow.id)}
              disabled={loading}
              data-testid={`btn-renew-${borrow.id}`}
              className="inline-flex items-center gap-1 rounded-lg bg-secondary/80 px-3.5 py-1.5 text-xs font-medium text-secondary-foreground transition-smooth hover:bg-secondary/60 disabled:opacity-50"
            >
              Renew
            </button>
          )}
        </div>
      </div>
    </motion.div>
  )
}

function TabButton({
  label,
  active,
  onClick,
  testId,
}: {
  label: string
  active: boolean
  onClick: () => void
  testId?: string
}) {
  return (
    <button
      onClick={onClick}
      data-testid={testId}
      className={cn(
        "-mb-px border-b-2 px-4 py-2.5 text-sm font-medium transition-smooth",
        active
          ? "border-primary text-primary"
          : "border-transparent text-muted-foreground hover:text-foreground",
      )}
    >
      {label}
    </button>
  )
}

function EmptyState({
  icon: Icon,
  title,
  hint,
}: {
  icon: React.ComponentType<{ className?: string }>
  title: string
  hint: string
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
    >
      <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border py-16 text-center">
        <Icon className="mb-3 h-10 w-10 text-muted-foreground/60" />
        <p className="text-sm font-medium">{title}</p>
        <p className="mt-1 text-xs text-muted-foreground">{hint}</p>
      </div>
    </motion.div>
  )
}

function formatDate(iso: string) {
  const d = new Date(iso)
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  })
}
