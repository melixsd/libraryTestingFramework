"use client"

import { useLibraryStore } from "@/store/library-store"
import { BookCover } from "@/components/shared/book-cover"
import {
  ArrowLeft,
  MapPin,
  BookOpen,
  PenTool,
  Loader2,
  XCircle,
  RefreshCw,
  FileQuestion,
} from "lucide-react"
import { motion } from "framer-motion"
import { useMemo, useState } from "react"

export function AuthorProfilePage() {
  const authorId = useLibraryStore((s) => s.selectedAuthorId)
  const authors = useLibraryStore((s) => s.authors)
  const allBooks = useLibraryStore((s) => s.books)
  const booksStatus = useLibraryStore((s) => s.booksStatus)
  const authorsStatus = useLibraryStore((s) => s.authorsStatus)
  const authorsError = useLibraryStore((s) => s.authorsError)
  const author = authors.find((a) => a.id === authorId)
  const selectAuthor = useLibraryStore((s) => s.selectAuthor)
  const selectBook = useLibraryStore((s) => s.selectBook)
  const setView = useLibraryStore((s) => s.setView)
  const [sort, setSort] = useState<"title" | "year">("year")

  // Default to first author if none selected
  const effectiveAuthor = author ?? authors[0]

  // Books by this author
  const authorBooks = useMemo(() => {
    if (!effectiveAuthor) return []
    const filtered = allBooks.filter((b) =>
      b.authors.some((a) => a.id === effectiveAuthor.id),
    )
    switch (sort) {
      case "title":
        return [...filtered].sort((a, b) => a.title.localeCompare(b.title))
      default:
        return [...filtered].sort(
          (a, b) => (b.publication_year ?? 0) - (a.publication_year ?? 0),
        )
    }
  }, [allBooks, effectiveAuthor, sort])

  // Loading state while books/authors are being fetched
  if ((authorsStatus === "loading" && authors.length === 0) ||
      (booksStatus === "loading" && allBooks.length === 0 && effectiveAuthor)) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-20 text-center" data-testid="author-profile-page">
        <Loader2 className="mx-auto mb-3 h-8 w-8 animate-spin text-primary" />
        <p className="text-sm text-muted-foreground">Loading author profile…</p>
      </div>
    )
  }

  // Error state when authors fail to load
  if (authorsStatus === "error" && authors.length === 0) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-20 text-center" data-testid="author-profile-page">
        <XCircle className="mx-auto mb-3 h-10 w-10 text-rose-500" />
        <p className="text-sm font-medium text-rose-600">Failed to load authors</p>
        <p className="mt-1 text-xs text-muted-foreground">{authorsError ?? "An unexpected error occurred."}</p>
        <button
          onClick={() => setView("home")}
          className="mt-4 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          Back to browse
        </button>
      </div>
    )
  }

  if (!effectiveAuthor) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-20 text-center" data-testid="author-profile-page">
        <FileQuestion className="mx-auto mb-3 h-10 w-10 text-muted-foreground/60" />
        <p className="text-muted-foreground">No author selected.</p>
        <button
          onClick={() => setView("home")}
          className="mt-4 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          Back to browse
        </button>
      </div>
    )
  }

  return (
    <div
      className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8"
      data-testid="author-profile-page"
    >
      <button
        onClick={() => setView("home")}
        className="mb-8 inline-flex items-center gap-2 text-sm text-muted-foreground transition-smooth hover:gap-3 hover:text-foreground"
        data-testid="btn-back"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to catalogue
      </button>

      <motion.section
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="overflow-hidden rounded-2xl border border-border bg-card shadow-lifted"
      >
        <div className="grid grid-cols-1 md:grid-cols-[1fr_auto]">
          <div className="p-6 sm:p-8">
            <div className="flex items-start gap-5">
              <div
                className="flex h-20 w-20 shrink-0 items-center justify-center rounded-2xl bg-primary/12 text-2xl font-bold text-primary ring-1 ring-primary/10"
                data-testid="author-avatar"
              >
                {effectiveAuthor.name
                  .split(" ")
                  .map((n) => n[0])
                  .join("")
                  .toUpperCase()
                  .slice(0, 2)}
              </div>
              <div className="min-w-0 flex-1">
                <span className="inline-flex items-center gap-1.5 rounded-full bg-secondary/70 px-2.5 py-0.5 text-xs font-medium text-secondary-foreground">
                  <PenTool className="h-3 w-3" />
                  Author
                </span>
                <h1
                  className="mt-3 font-serif text-[1.75rem] font-semibold leading-tight tracking-tight sm:text-[2.5rem]"
                  data-testid="author-name"
                >
                  {effectiveAuthor.name}
                </h1>
                {effectiveAuthor.nationality && (
                  <div className="mt-2.5 flex items-center gap-1.5 text-sm text-muted-foreground">
                    <MapPin className="h-3.5 w-3.5" />
                    {effectiveAuthor.nationality}
                  </div>
                )}
              </div>
            </div>

            <div className="mt-7 flex flex-wrap gap-6">
              <Stat icon={BookOpen} label="Books" value={authorBooks.length} />
            </div>
          </div>

          <div className="relative hidden w-52 items-center justify-center bg-gradient-to-br from-primary/8 via-accent/12 to-primary/3 md:flex">
            <div className="text-center">
              <BookOpen className="mx-auto h-12 w-12 text-primary/25" />
              <p className="mt-3 font-serif text-[11px] uppercase tracking-[0.2em] text-primary/50">
                Aldenwood
                <br />
                Collection
              </p>
            </div>
          </div>
        </div>
      </motion.section>

      {/* Books by author */}
      <section className="mt-8">
        <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
          <h2 className="font-serif text-xl font-semibold tracking-tight sm:text-2xl">
            Books by {effectiveAuthor.name.split(" ").slice(-1)[0]}
          </h2>
          <div className="flex items-center gap-0.5 rounded-lg border border-border bg-card p-1 text-xs shadow-card">
            {(
              [
                { id: "year", label: "Recent" },
                { id: "title", label: "A-Z" },
              ] as const
            ).map((opt) => (
              <button
                key={opt.id}
                onClick={() => setSort(opt.id)}
                data-testid={`sort-${opt.id}`}
                className={
                  sort === opt.id
                    ? "rounded-md bg-primary px-3.5 py-1.5 font-medium text-primary-foreground"
                    : "rounded-md px-3.5 py-1.5 text-muted-foreground transition-smooth hover:bg-accent/60 hover:text-foreground"
                }
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        {/* Loading while books are still being fetched */}
        {booksStatus === "loading" && allBooks.length === 0 ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="h-6 w-6 animate-spin text-primary" />
            <span className="ml-3 text-sm text-muted-foreground">Loading books…</span>
          </div>
        ) : authorBooks.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25 }}
          >
            <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border py-16 text-center">
              <div className="mb-3 flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
                <FileQuestion className="h-8 w-8 text-primary/50" />
              </div>
              <p className="text-sm font-medium">No books in the catalogue yet</p>
              <p className="mt-1 text-xs text-muted-foreground">
                Books by {effectiveAuthor.name} will appear here once they're added.
              </p>
            </div>
          </motion.div>
        ) : (
          <div
            className="grid grid-cols-2 gap-x-4 gap-y-7 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5"
            data-testid="author-books-grid"
          >
            {authorBooks.map((book, i) => (
              <motion.button
                key={book.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.25, delay: Math.min(i * 0.04, 0.3) }}
                onClick={() => selectBook(book.id)}
                className="group text-left transition-lift"
                data-testid={`author-book-${book.id}`}
              >
                <BookCover
                  book={book}
                  size="md"
                  className="w-full transition-lift group-hover:-translate-y-1.5 group-hover:shadow-lifted"
                />
                <div className="mt-3.5">
                  <h3 className="line-clamp-1 font-serif text-sm font-semibold tracking-tight">
                    {book.title}
                  </h3>
                  <div className="mt-2 flex items-center justify-between">
                    <span className="rounded-md bg-secondary/70 px-1.5 py-0.5 text-[10px] font-medium text-secondary-foreground">
                      {book.genre}
                    </span>
                    <span className="text-[11px] text-muted-foreground/70">
                      {book.available_copies > 0
                        ? `${book.available_copies} avail.`
                        : "All checked out"}
                    </span>
                  </div>
                </div>
              </motion.button>
            ))}
          </div>
        )}
      </section>

      {/* Other authors */}
      {authors.length > 1 && (
        <section className="mt-14">
          <h2 className="mb-5 font-serif text-xl font-semibold tracking-tight">
            Other authors to explore
          </h2>
          <div
            className="flex gap-3 overflow-x-auto pb-3 scrollbar-warm"
            data-testid="other-authors"
          >
            {authors
              .filter((a) => a.id !== effectiveAuthor.id)
              .map((a) => (
                <button
                  key={a.id}
                  onClick={() => selectAuthor(a.id)}
                  className="flex w-36 shrink-0 flex-col items-center gap-2.5 rounded-xl border border-border bg-card p-4 text-center shadow-card transition-smooth hover:border-primary/30 hover:bg-accent/20 sm:w-44"
                  data-testid={`other-author-${a.id}`}
                >
                  <div className="flex h-14 w-14 items-center justify-center rounded-full bg-secondary/80 text-lg font-semibold text-secondary-foreground">
                    {a.name
                      .split(" ")
                      .map((n) => n[0])
                      .join("")
                      .toUpperCase()
                      .slice(0, 2)}
                  </div>
                  <div>
                    <p className="text-sm font-medium tracking-tight">{a.name}</p>
                    <p className="text-xs text-muted-foreground/80">
                      {a.nationality ?? "Unknown"}
                    </p>
                  </div>
                </button>
              ))}
          </div>
        </section>
      )}
    </div>
  )
}

function Stat({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>
  label: string
  value: number
}) {
  return (
    <div className="flex items-center gap-3">
      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-secondary text-secondary-foreground">
        <Icon className="h-4 w-4" />
      </div>
      <div>
        <p className="font-serif text-xl font-semibold leading-none">{value}</p>
        <p className="mt-1 text-xs text-muted-foreground">{label}</p>
      </div>
    </div>
  )
}
