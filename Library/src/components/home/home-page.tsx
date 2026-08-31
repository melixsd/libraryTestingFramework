"use client"

import { useEffect } from "react"
import { useLibraryStore } from "@/store/library-store"
import { BookCover } from "@/components/shared/book-cover"
import { cn } from "@/lib/utils"
import {
  Search,
  SlidersHorizontal,
  BookOpen,
  X,
  Library,
  Loader2,
} from "lucide-react"
import { motion } from "framer-motion"
import { useMemo } from "react"

export function HomePage() {
  const allBooks = useLibraryStore((s) => s.books)
  const status = useLibraryStore((s) => s.status)
  const searchQuery = useLibraryStore((s) => s.searchQuery)
  const searchField = useLibraryStore((s) => s.searchField)
  const selectedGenres = useLibraryStore((s) => s.selectedGenres)
  const availabilityFilter = useLibraryStore((s) => s.availabilityFilter)

  const setSearchQuery = useLibraryStore((s) => s.setSearchQuery)
  const setSearchField = useLibraryStore((s) => s.setSearchField)
  const toggleGenre = useLibraryStore((s) => s.toggleGenre)
  const clearGenres = useLibraryStore((s) => s.clearGenres)
  const setAvailabilityFilter = useLibraryStore((s) => s.setAvailabilityFilter)
  const selectBook = useLibraryStore((s) => s.selectBook)
  const fetchBooks = useLibraryStore((s) => s.fetchBooks)

  // Debounced server-side search
  useEffect(() => {
    const timer = setTimeout(() => {
      fetchBooks(searchQuery || undefined)
    }, 300)
    return () => clearTimeout(timer)
  }, [searchQuery, fetchBooks])

  // Get unique genres from books
  const allGenres = useMemo(() => {
    const genreSet = new Set(allBooks.map((b) => b.genre))
    return Array.from(genreSet).sort()
  }, [allBooks])

  // Client-side filter for genre and availability (server handles text search)
  const filteredBooks = useMemo(() => {
    return allBooks.filter((book) => {
      if (selectedGenres.length > 0 && !selectedGenres.includes(book.genre)) {
        return false
      }
      if (availabilityFilter === "available" && book.available_copies === 0)
        return false
      if (availabilityFilter === "unavailable" && book.available_copies > 0)
        return false
      return true
    })
  }, [allBooks, selectedGenres, availabilityFilter])

  const totalAvailable = allBooks.filter((b) => b.available_copies > 0).length
  const authorCount = new Set(
    allBooks.flatMap((b) => b.authors.map((a) => a.id)),
  ).size
  const hasActiveFilters =
    searchQuery.trim() !== "" ||
    selectedGenres.length > 0 ||
    availabilityFilter !== "all"

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Hero */}
      <section
        className="mb-10 overflow-hidden rounded-2xl border border-primary/20 bg-gradient-to-br from-primary via-primary to-primary/90 px-6 py-10 text-primary-foreground shadow-lifted sm:px-12 sm:py-16"
        data-testid="home-hero"
      >
        <div className="flex flex-col gap-8 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-2xl">
            <span className="inline-flex items-center gap-2 rounded-full bg-primary-foreground/12 px-3.5 py-1.5 text-[11px] uppercase tracking-[0.2em] backdrop-blur-sm">
              <Library className="h-3.5 w-3.5" />
              The Aldenwood Collection
            </span>
            <h1
              className="mt-5 font-serif text-[2rem] font-semibold leading-[1.1] tracking-tightest sm:text-5xl"
              data-testid="home-title"
            >
              {allBooks.length} volumes in our collection, ready for you to explore.
            </h1>
            <p className="mt-5 max-w-lg text-sm leading-relaxed text-primary-foreground/75 sm:text-base">
              Browse the catalogue, borrow a book, or follow your favourite
              author. Every title has been hand-chosen by our librarians.
            </p>
          </div>
          <div className="flex gap-8 text-primary-foreground/85">
            <Stat label="Titles" value={allBooks.length} />
            <div className="w-px self-stretch bg-primary-foreground/15" />
            <Stat label="Available" value={totalAvailable} />
            <div className="w-px self-stretch bg-primary-foreground/15" />
            <Stat label="Authors" value={authorCount} />
          </div>
        </div>
      </section>

      {/* Search bar */}
      <section className="mb-8" data-testid="search-section">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <div className="relative flex-1">
            <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by title, author, or keyword…"
              data-testid="search-input"
              className="h-12 w-full rounded-xl border border-border bg-card pl-11 pr-11 text-sm shadow-card outline-none transition-smooth placeholder:text-muted-foreground/60 focus:border-primary/50 focus:ring-2 focus:ring-primary/15"
              aria-label="Search books"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                className="absolute right-3 top-1/2 -translate-y-1/2 rounded-full p-1 text-muted-foreground hover:bg-accent hover:text-foreground"
                aria-label="Clear search"
                data-testid="search-clear"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>

          <div className="flex items-center gap-0.5 rounded-xl border border-border bg-card p-1 shadow-card">
            {(["all", "title", "author"] as const).map((field) => (
              <button
                key={field}
                onClick={() => setSearchField(field)}
                data-testid={`search-field-${field}`}
                className={cn(
                  "rounded-lg px-3.5 py-2 text-xs font-medium capitalize transition-smooth",
                  searchField === field
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "text-muted-foreground hover:bg-accent/60 hover:text-foreground",
                )}
              >
                {field === "all" ? "All" : field}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Loading */}
      {status === "loading" && (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <span className="ml-3 text-sm text-muted-foreground">
            Loading catalogue...
          </span>
        </div>
      )}

      {/* Main content: sidebar + grid */}
      {status !== "loading" && (
        <section className="grid grid-cols-1 gap-8 lg:grid-cols-[240px_1fr]">
          <aside className="lg:sticky lg:top-24 lg:h-fit">
            <div
              className="rounded-xl border border-border bg-card p-5 shadow-card"
              data-testid="filter-sidebar"
            >
              <div className="mb-5 flex items-center justify-between">
                <h2 className="flex items-center gap-2 text-sm font-semibold">
                  <SlidersHorizontal className="h-4 w-4 text-primary" />
                  Filters
                </h2>
                {hasActiveFilters && (
                  <button
                    onClick={() => {
                      setSearchQuery("")
                      clearGenres()
                      setAvailabilityFilter("all")
                    }}
                    className="text-xs text-primary underline-offset-2 hover:underline"
                    data-testid="filters-reset"
                  >
                    Reset all
                  </button>
                )}
              </div>

              <div className="mb-6">
                <h3 className="mb-2.5 text-[11px] font-semibold uppercase tracking-[0.15em] text-muted-foreground/80">
                  Availability
                </h3>
                <div className="flex flex-col gap-0.5">
                  {(
                    [
                      { id: "all", label: "All books" },
                      { id: "available", label: "Available now" },
                      { id: "unavailable", label: "Checked out" },
                    ] as const
                  ).map((opt) => (
                    <label
                      key={opt.id}
                      className="flex cursor-pointer items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm transition-smooth hover:bg-accent/40"
                    >
                      <input
                        type="radio"
                        name="availability"
                        data-testid={`filter-availability-${opt.id}`}
                        checked={availabilityFilter === opt.id}
                        onChange={() => setAvailabilityFilter(opt.id)}
                        className="h-4 w-4 accent-primary"
                      />
                      {opt.label}
                    </label>
                  ))}
                </div>
              </div>

              {allGenres.length > 0 && (
                <div>
                  <div className="mb-2.5 flex items-center justify-between">
                    <h3 className="text-[11px] font-semibold uppercase tracking-[0.15em] text-muted-foreground/80">
                      Genre
                    </h3>
                    {selectedGenres.length > 0 && (
                      <button
                        onClick={clearGenres}
                        className="text-xs text-primary hover:underline"
                        data-testid="filter-genre-clear"
                      >
                        Clear
                      </button>
                    )}
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {allGenres.map((genre) => {
                      const active = selectedGenres.includes(genre)
                      return (
                        <button
                          key={genre}
                          onClick={() => toggleGenre(genre)}
                          data-testid={`filter-genre-${genre}`}
                          className={cn(
                            "rounded-full border px-2.5 py-1 text-xs transition-smooth",
                            active
                              ? "border-primary bg-primary text-primary-foreground"
                              : "border-border bg-background text-muted-foreground hover:border-primary/40 hover:text-foreground hover:bg-accent/30",
                          )}
                        >
                          {genre}
                        </button>
                      )
                    })}
                  </div>
                </div>
              )}
            </div>
          </aside>

          {/* Book grid */}
          <div>
            <div className="mb-5 flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                Showing{" "}
                <span className="font-semibold text-foreground" data-testid="books-count">
                  {filteredBooks.length}
                </span>{" "}
                of {allBooks.length} books
                {hasActiveFilters && " · filtered"}
              </p>
            </div>

            {filteredBooks.length === 0 ? (
              <div
                className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-border py-24 text-center"
                data-testid="no-books-found"
              >
                <BookOpen className="mb-4 h-10 w-10 text-muted-foreground/50" />
                <p className="font-serif text-base font-medium">No books match your search</p>
                <p className="mt-1.5 text-xs text-muted-foreground">
                  Try a different keyword or remove some filters.
                </p>
                <button
                  onClick={() => {
                    setSearchQuery("")
                    clearGenres()
                    setAvailabilityFilter("all")
                  }}
                  className="mt-5 rounded-lg bg-primary px-4 py-2 text-xs font-medium text-primary-foreground transition-smooth hover:bg-primary/90"
                >
                  Clear all filters
                </button>
              </div>
            ) : (
              <motion.div
                layout
                className="grid grid-cols-2 gap-x-5 gap-y-8 sm:grid-cols-3 xl:grid-cols-4"
                data-testid="books-grid"
              >
                {filteredBooks.map((book, i) => (
                  <BookCard
                    key={book.id}
                    book={book}
                    index={i}
                    onClick={() => selectBook(book.id)}
                  />
                ))}
              </motion.div>
            )}
          </div>
        </section>
      )}
    </div>
  )
}

function BookCard({
  book,
  index,
  onClick,
}: {
  book: import("@/lib/types").DisplayBook
  index: number
  onClick: () => void
}) {
  const available = book.available_copies > 0
  return (
    <motion.button
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, delay: Math.min(index * 0.025, 0.3) }}
      onClick={onClick}
      className="group flex flex-col text-left transition-lift"
      aria-label={`View details for ${book.title}`}
      data-testid={`book-card-${book.id}`}
    >
      <div className="relative">
        <BookCover
          book={book}
          size="md"
          className="w-full transition-lift group-hover:-translate-y-1.5 group-hover:shadow-lifted"
        />
        <div
          className={cn(
            "absolute right-2.5 top-2.5 flex h-6 items-center gap-1 rounded-full border px-2 text-[10px] font-medium backdrop-blur-sm transition-smooth",
            available
              ? "border-emerald-200 bg-emerald-50/90 text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950/80 dark:text-emerald-300"
              : "border-rose-200 bg-rose-50/90 text-rose-700 dark:border-rose-900 dark:bg-rose-950/80 dark:text-rose-300",
          )}
          data-testid={available ? "badge-available" : "badge-unavailable"}
        >
          <span
            className={cn(
              "h-1.5 w-1.5 rounded-full",
              available ? "bg-emerald-500" : "bg-rose-500",
            )}
          />
          {available ? `${book.available_copies} left` : "Out"}
        </div>
      </div>
      <div className="mt-3.5 px-0.5">
        <h3 className="line-clamp-1 font-serif text-sm font-semibold leading-tight tracking-tight">
          {book.title}
        </h3>
        <p className="mt-1 line-clamp-1 text-xs text-muted-foreground">
          {book.authorName}
        </p>
        <div className="mt-2 flex items-center justify-between">
          <span className="rounded-md bg-secondary/70 px-1.5 py-0.5 text-[10px] font-medium text-secondary-foreground">
            {book.genre}
          </span>
          <span className="text-[11px] text-muted-foreground/70">
            {book.total_copies} copies
          </span>
        </div>
      </div>
    </motion.button>
  )
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex flex-col">
      <span className="font-serif text-[2rem] font-semibold leading-none tracking-tight">
        {value}
      </span>
      <span className="mt-1.5 text-[10px] uppercase tracking-[0.15em] opacity-70">
        {label}
      </span>
    </div>
  )
}
