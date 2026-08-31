"use client"

import { useLibraryStore } from "@/store/library-store"
import { BookCover } from "@/components/shared/book-cover"
import {
  ArrowLeft,
  BookOpen,
  Hash,
  Loader2,
  RefreshCw,
} from "lucide-react"
import { motion } from "framer-motion"
import { cn } from "@/lib/utils"
import { useMemo, useState } from "react"

export function BookDetailPage() {
  const bookId = useLibraryStore((s) => s.selectedBookId)
  const allBooks = useLibraryStore((s) => s.books)
  const currentUser = useLibraryStore((s) => s.currentUser)
  const book = useLibraryStore((s) => s.books.find((b) => b.id === bookId))
  const selectBook = useLibraryStore((s) => s.selectBook)
  const selectAuthor = useLibraryStore((s) => s.selectAuthor)
  const setView = useLibraryStore((s) => s.setView)
  const borrowBook = useLibraryStore((s) => s.borrowBook)
  const reserveBook = useLibraryStore((s) => s.reserveBook)
  const [borrowing, setBorrowing] = useState(false)
  const [reserving, setReserving] = useState(false)

  // Related books: same genre or same authors
  const relatedBooks = useMemo(() => {
    if (!book) return []
    const authorIds = new Set(book.authors.map((a) => a.id))
    return allBooks.filter(
      (b) =>
        b.id !== book.id &&
        (b.authors.some((a) => authorIds.has(a.id)) || b.genre === book.genre),
    )
  }, [allBooks, book])

  if (!book) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-20 text-center">
        <Loader2 className="mx-auto mb-3 h-8 w-8 animate-spin text-muted-foreground" />
        <p className="text-muted-foreground">Loading book...</p>
        <button
          onClick={() => setView("home")}
          className="mt-4 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
        >
          Back to browse
        </button>
      </div>
    )
  }

  const available = book.available_copies > 0
  const availabilityRatio =
    book.total_copies > 0 ? book.available_copies / book.total_copies : 0

  async function handleBorrow() {
    if (!book) return
    setBorrowing(true)
    try {
      await borrowBook(book.id)
    } finally {
      setBorrowing(false)
    }
  }

  async function handleReserve() {
    if (!book) return
    setReserving(true)
    try {
      await reserveBook(book.id)
    } finally {
      setReserving(false)
    }
  }

  return (
    <div
      className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8"
      data-testid="book-detail-page"
    >
      <button
        onClick={() => setView("home")}
        className="mb-8 inline-flex items-center gap-2 text-sm text-muted-foreground transition-smooth hover:gap-3 hover:text-foreground"
        data-testid="btn-back-to-catalogue"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to catalogue
      </button>

      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="grid grid-cols-1 gap-10 lg:grid-cols-[300px_1fr]"
      >
        <div className="lg:sticky lg:top-24 lg:h-fit">
          <div className="flex justify-center">
            <BookCover
              book={book}
              size="xl"
              className="shadow-lifted"
            />
          </div>

          <div
            className="mt-6 rounded-xl border border-border bg-card p-5 shadow-card"
            data-testid="availability-card"
          >
            <div className="mb-4 flex items-center justify-between">
              <span className="text-[11px] font-semibold uppercase tracking-[0.15em] text-muted-foreground/80">
                Availability
              </span>
              <span
                className={cn(
                  "flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium",
                  available
                    ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300"
                    : "bg-rose-100 text-rose-800 dark:bg-rose-950/40 dark:text-rose-300",
                )}
                data-testid={available ? "status-available" : "status-checked-out"}
              >
                {available ? "Available" : "Checked out"}
              </span>
            </div>

            <div className="mb-3 flex items-end justify-between">
              <span className="font-serif text-lg font-semibold">
                {book.available_copies} <span className="text-sm font-normal text-muted-foreground">of {book.total_copies}</span>
              </span>
              <span className="text-xs text-muted-foreground">
                {Math.round(availabilityRatio * 100)}% available
              </span>
            </div>

            <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
              <div
                className={cn(
                  "h-full rounded-full transition-all",
                  availabilityRatio === 0
                    ? "bg-rose-500"
                    : availabilityRatio < 0.34
                      ? "bg-amber-500"
                      : "bg-emerald-500",
                )}
                style={{ width: `${Math.max(availabilityRatio * 100, 4)}%` }}
                data-testid="availability-bar"
              />
            </div>

            {/* Action buttons */}
            <div className="mt-5 flex gap-2">
              {available && currentUser?.role === "member" && (
                <button
                  onClick={handleBorrow}
                  disabled={borrowing}
                  data-testid="btn-borrow"
                  className="flex-1 rounded-lg bg-primary px-4 py-3 text-sm font-medium text-primary-foreground shadow-card transition-lift hover:bg-primary/90 hover:shadow-lifted disabled:opacity-50"
                >
                  {borrowing ? (
                    <span className="flex items-center justify-center gap-2">
                      <RefreshCw className="h-4 w-4 animate-spin" /> Borrowing...
                    </span>
                  ) : (
                    "Borrow this book"
                  )}
                </button>
              )}
              {!available && currentUser?.role === "member" && (
                <button
                  onClick={handleReserve}
                  disabled={reserving}
                  data-testid="btn-reserve"
                  className="flex-1 rounded-lg bg-primary px-4 py-3 text-sm font-medium text-primary-foreground shadow-card transition-lift hover:bg-primary/90 hover:shadow-lifted disabled:opacity-50"
                >
                  {reserving ? (
                    <span className="flex items-center justify-center gap-2">
                      <RefreshCw className="h-4 w-4 animate-spin" /> Reserving...
                    </span>
                  ) : (
                    "Reserve next copy"
                  )}
                </button>
              )}
              {!currentUser && (
                <p className="flex-1 text-center text-xs text-muted-foreground">
                  Sign in to borrow or reserve this book.
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Book info */}
        <div>
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="rounded-md bg-secondary/70 px-2 py-1 font-medium text-secondary-foreground">
              {book.genre}
            </span>
          </div>

          <h1
            className="mt-4 font-serif text-[2rem] font-semibold leading-[1.1] tracking-tight sm:text-[2.5rem]"
            data-testid="book-title"
          >
            {book.title}
          </h1>

          <div className="mt-4 flex flex-wrap items-center gap-2">
            <span className="text-xs uppercase tracking-[0.1em] text-muted-foreground/70">by</span>
            {book.authors.map((author) => (
              <button
                key={author.id}
                onClick={() => selectAuthor(author.id)}
                className="inline-flex items-center gap-1 font-serif text-lg text-primary transition-smooth hover:underline hover:underline-offset-4"
                data-testid={`author-link-${author.id}`}
              >
                {author.name}
              </button>
            ))}
          </div>

          {book.description && (
            <p className="mt-7 max-w-2xl text-[15px] leading-[1.7] text-foreground/85">
              {book.description}
            </p>
          )}

          <div className="mt-10 grid grid-cols-2 gap-x-6 gap-y-5 sm:grid-cols-3">
            <MetaItem
              icon={BookOpen}
              label="Published"
              value={book.publication_year ? String(book.publication_year) : "N/A"}
            />
            <MetaItem
              icon={BookOpen}
              label="Copies"
              value={`${book.total_copies} total`}
            />
            <MetaItem icon={Hash} label="ISBN" value={book.isbn} />
            <MetaItem icon={BookOpen} label="Price" value={`$${book.price.toFixed(2)}`} />
          </div>

          {/* Authors section */}
          {book.authors.length > 0 && (
            <div className="mt-10 rounded-xl border border-border bg-card p-6 shadow-card">
              <h2 className="mb-4 text-[11px] font-semibold uppercase tracking-[0.15em] text-muted-foreground/80">
                {book.authors.length === 1 ? "Author" : "Authors"}
              </h2>
              <div className="space-y-2">
                {book.authors.map((author) => (
                  <button
                    key={author.id}
                    onClick={() => selectAuthor(author.id)}
                    className="flex w-full items-center gap-3.5 rounded-lg p-2.5 text-left transition-smooth hover:bg-accent/40"
                    data-testid={`author-card-${author.id}`}
                  >
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-secondary/80 text-sm font-semibold text-secondary-foreground">
                      {author.name
                        .split(" ")
                        .map((n) => n[0])
                        .join("")
                        .toUpperCase()
                        .slice(0, 2)}
                    </div>
                    <div>
                      <h3 className="font-serif text-base font-semibold">
                        {author.name}
                      </h3>
                      {author.nationality && (
                        <p className="text-xs text-muted-foreground">
                          {author.nationality}
                        </p>
                      )}
                    </div>
                    <span className="ml-auto text-xs font-medium text-primary">
                      View profile
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Related books */}
          {relatedBooks.length > 0 && (
            <div className="mt-12">
              <h2 className="mb-5 font-serif text-xl font-semibold tracking-tight">
                Related books
              </h2>
              <div
                className="grid grid-cols-3 gap-x-4 gap-y-5 sm:grid-cols-5"
                data-testid="related-books"
              >
                {relatedBooks.slice(0, 5).map((b) => (
                  <button
                    key={b.id}
                    onClick={() => selectBook(b.id)}
                    className="group text-left transition-lift"
                    data-testid={`related-book-${b.id}`}
                  >
                    <BookCover
                      book={b}
                      size="sm"
                      className="w-full transition-lift group-hover:-translate-y-1 group-hover:shadow-lifted"
                    />
                    <p className="mt-2.5 line-clamp-1 text-xs font-medium tracking-tight">
                      {b.title}
                    </p>
                    <p className="line-clamp-1 text-[10px] text-muted-foreground">
                      {b.authorName}
                    </p>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  )
}

function MetaItem({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>
  label: string
  value: string
}) {
  return (
    <div className="flex items-start gap-3">
      <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-secondary/60 text-secondary-foreground">
        <Icon className="h-3.5 w-3.5" />
      </div>
      <div className="min-w-0">
        <p className="text-[10px] font-medium uppercase tracking-[0.1em] text-muted-foreground/70">
          {label}
        </p>
        <p className="truncate text-sm font-medium">{value}</p>
      </div>
    </div>
  )
}
