"use client"

import { cn } from "@/lib/utils"
import type { DisplayBook } from "@/lib/types"

interface BookCoverProps {
  book: DisplayBook
  className?: string
  size?: "sm" | "md" | "lg" | "xl"
}

const sizeMap = {
  sm: "h-32 w-24 text-[10px]",
  md: "h-44 w-32 text-xs",
  lg: "h-60 w-44 text-sm",
  xl: "h-80 w-56 text-base",
}

export function BookCover({ book, className, size = "md" }: BookCoverProps) {
  return (
    <div
      className={cn(
        "book-spine relative flex flex-col justify-between overflow-hidden rounded-md p-3 shadow-card transition-lift",
        sizeMap[size],
        className,
      )}
      style={{
        background: `linear-gradient(150deg, ${book.coverColor} 0%, ${book.coverColor} 55%, color-mix(in oklab, ${book.coverColor}, black 14%) 100%)`,
        color: book.coverAccent,
      }}
      aria-label={`Cover of ${book.title}`}
      data-testid="book-cover"
    >
      <div
        className="h-px w-full opacity-50"
        style={{ background: book.coverAccent }}
      />
      <div className="flex flex-1 flex-col justify-center text-center">
        <div
          className="mx-auto mb-1.5 font-serif text-[0.65em] uppercase tracking-[0.22em] opacity-60"
          style={{ color: book.coverAccent }}
        >
          {book.authorName.split(" ").slice(-1)[0]}
        </div>
        <h3
          className="font-serif font-semibold leading-[1.15]"
          style={{
            color: book.coverAccent,
            fontSize: size === "xl" ? "1.4em" : size === "lg" ? "1.1em" : "0.95em",
          }}
        >
          {book.title}
        </h3>
      </div>
      <div className="flex items-center justify-between opacity-60" style={{ color: book.coverAccent }}>
        <span className="font-serif text-[0.7em] uppercase tracking-[0.1em]">
          {book.genre}
        </span>
        <span className="font-mono text-[0.7em]">{book.publication_year ?? ""}</span>
      </div>
      <div
        className="pointer-events-none absolute inset-0 opacity-15"
        style={{
          background:
            "radial-gradient(circle at 30% 15%, rgba(255,255,255,0.22) 0%, transparent 45%), radial-gradient(circle at 80% 85%, rgba(0,0,0,0.12) 0%, transparent 40%)",
        }}
      />
      <div
        aria-hidden
        className="pointer-events-none absolute inset-y-0 left-1/2 w-8 -translate-x-1/2 opacity-10"
        style={{
          background:
            "linear-gradient(to right, transparent, rgba(255,255,255,0.35), transparent)",
        }}
      />
    </div>
  )
}
