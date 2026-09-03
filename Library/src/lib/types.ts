/* ── Types matching the backend Pydantic schemas ── */

// ─── Auth ───────────────────────────────────────────
export interface UserOut {
  id: number
  username: string
  email: string
  role: UserRole
  is_active: boolean
  member_id: number | null
}

export type UserRole = "admin" | "librarian" | "member"

export interface Token {
  access_token: string
  token_type: string
}

// ─── Catalog ────────────────────────────────────────
export interface AuthorOut {
  id: number
  name: string
  nationality: string | null
}

export interface PublisherOut {
  id: number
  name: string
  address: string | null
}

export interface CategoryOut {
  id: number
  name: string
  is_reference_only: boolean
}

export interface MembershipTypeOut {
  id: number
  name: string
  max_books: number
  loan_period_days: number
  max_renewals: number
  can_reserve: boolean
  daily_fine_rate: number
}

// ─── Books ───────────────────────────────────────────
export interface BookOut {
  id: number
  title: string
  isbn: string
  price: number
  publication_year: number | null
  description?: string
  authors: AuthorOut[]
  available_copies: number
  total_copies: number
  // Joined fields (resolved from category/publisher on the frontend or extended schema)
  category?: CategoryOut
  publisher?: PublisherOut
}

export interface BookCreate {
  title: string
  isbn: string
  price: number
  publication_year?: number | null
  description?: string | null
  author_ids: number[]
  publisher_id?: number | null
  category_id?: number | null
  number_of_copies?: number
}

// ─── Members ────────────────────────────────────────
export interface MemberOut {
  id: number
  full_name: string
  email: string
  is_active: boolean
  outstanding_fine: number
  membership_type: MembershipTypeOut
}

// ─── Borrows ────────────────────────────────────────
export interface BorrowOut {
  id: number
  copy_id: number
  member_id: number
  borrow_date: string
  due_date: string
  return_date: string | null
  returned: boolean
  renewed_count: number
  fine_amount: number
  /** Resolved by the backend for display; may be absent on older payloads */
  book_title?: string | null
}

// ─── Reservations ───────────────────────────────────
export interface ReservationOut {
  id: number
  book_id: number
  member_id: number
  reservation_date: string
  status: string
  expiry_date: string | null
  /** Resolved by the backend for display; may be absent on older payloads */
  book_title?: string | null
}

// ─── Member Summary ─────────────────────────────────
export interface MemberSummaryOut {
  member: MemberOut
  active_borrows: BorrowOut[]
  reservations: ReservationOut[]
  total_fines: number
}

// ─── Test Results (Phase 4) ───────────────────────
export interface TestResultsSummary {
  last_run: number | null
  passed: number
  failed: number
  skipped: number
  total: number
  duration: number
  coverage_percent: number | null
  report_path: string
}

// ─── Frontend-only view types ───────────────────────
export type ViewName =
  | "home"
  | "book-detail"
  | "member-profile"
  | "author-profile"
  | "admin"
  | "login"
  | "test-results"

// ─── Frontend display helpers (cover colours for BookCover) ──
// Backend books don't have coverColor/coverAccent; we derive them
// deterministically from the book id so the CSS-only covers still work.
const COVER_PALETTE = [
  { color: "oklch(0.42 0.08 155)", accent: "oklch(0.85 0.1 75)" },
  { color: "oklch(0.5 0.07 35)", accent: "oklch(0.88 0.12 75)" },
  { color: "oklch(0.32 0.08 280)", accent: "oklch(0.82 0.08 280)" },
  { color: "oklch(0.55 0.12 30)", accent: "oklch(0.90 0.1 60)" },
  { color: "oklch(0.35 0.08 160)", accent: "oklch(0.80 0.08 200)" },
  { color: "oklch(0.45 0.06 80)", accent: "oklch(0.85 0.08 100)" },
  { color: "oklch(0.38 0.1 320)", accent: "oklch(0.82 0.1 340)" },
  { color: "oklch(0.52 0.09 190)", accent: "oklch(0.87 0.09 210)" },
]

/** Book decorated with display-only fields for BookCover component */
export interface DisplayBook extends BookOut {
  coverColor: string
  coverAccent: string
  /** Computed: first author name */
  authorName: string
  /** Computed: genre from category or fallback */
  genre: string
}

export function toDisplayBook(book: BookOut): DisplayBook {
  const palette = COVER_PALETTE[book.id % COVER_PALETTE.length]
  return {
    ...book,
    coverColor: palette.color,
    coverAccent: palette.accent,
    authorName: book.authors.map((a) => a.name).join(", ") || "Unknown",
    genre: book.category?.name ?? "General",
  }
}
