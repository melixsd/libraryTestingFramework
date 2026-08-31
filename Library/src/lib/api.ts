/* ── Typed API client for the Library Management backend ── */

import type {
  Token,
  UserOut,
  BookOut,
  BookCreate,
  AuthorOut,
  MemberOut,
  MemberSummaryOut,
  BorrowOut,
  MembershipTypeOut,
  TestResultsSummary,
} from "./types"

const API_BASE = "http://localhost:8000"

/* ── helpers ──────────────────────────────────────── */

function getToken(): string | null {
  if (typeof window === "undefined") return null
  return localStorage.getItem("library_token")
}

function setToken(token: string | null) {
  if (typeof window === "undefined") return
  if (token) {
    localStorage.setItem("library_token", token)
  } else {
    localStorage.removeItem("library_token")
  }
}

async function request<T>(
  path: string,
  opts: RequestInit = {},
): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(opts.headers as Record<string, string>),
  }
  if (token) {
    headers["Authorization"] = `Bearer ${token}`
  }

  const res = await fetch(`${API_BASE}${path}`, { ...opts, headers })

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }))
    // Pydantic validation errors return detail as an array of {msg, loc, ...}
    let message: string
    if (Array.isArray(body.detail)) {
      message = body.detail.map((e: { msg: string }) => e.msg).join("; ")
    } else if (typeof body.detail === "string") {
      message = body.detail
    } else {
      message = res.statusText
    }
    throw new ApiError(message, res.status)
  }

  // 204 No Content
  if (res.status === 204) return undefined as T

  return res.json() as Promise<T>
}

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.name = "ApiError"
    this.status = status
  }
}

/* ── Auth ─────────────────────────────────────────── */

export async function login(
  username: string,
  password: string,
): Promise<Token> {
  // OAuth2PasswordRequestForm expects form data
  const body = new URLSearchParams()
  body.append("username", username)
  body.append("password", password)

  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  })

  if (!res.ok) {
    const detail = await res.json().then((b) => b.detail).catch(() => "Login failed")
    throw new ApiError(detail, res.status)
  }

  const token: Token = await res.json()
  setToken(token.access_token)
  return token
}

export function logout() {
  setToken(null)
}

export async function getMe(): Promise<UserOut> {
  return request<UserOut>("/auth/me")
}

export async function register(data: {
  username: string
  email: string
  password: string
  full_name?: string
  membership_type_id?: number
}): Promise<UserOut> {
  return request<UserOut>("/auth/register", {
    method: "POST",
    body: JSON.stringify(data),
  })
}

/* ── Books ─────────────────────────────────────────── */

export async function listBooks(search?: string): Promise<BookOut[]> {
  const q = search ? `?search=${encodeURIComponent(search)}` : ""
  return request<BookOut[]>(`/books${q}`)
}

export async function getBook(id: number): Promise<BookOut> {
  return request<BookOut>(`/books/${id}`)
}

export async function createBook(data: BookCreate): Promise<BookOut> {
  return request<BookOut>("/books", {
    method: "POST",
    body: JSON.stringify(data),
  })
}

export async function addCopies(bookId: number, count: number): Promise<void> {
  return request<void>(`/books/${bookId}/copies?count=${count}`, {
    method: "POST",
  })
}

export async function removeCopy(bookId: number, copyId: number): Promise<void> {
  return request<void>(`/books/${bookId}/copies/${copyId}`, {
    method: "DELETE",
  })
}

/* ── Authors ──────────────────────────────────────── */

export async function listAuthors(): Promise<AuthorOut[]> {
  return request<AuthorOut[]>("/authors")
}

export async function deleteAuthor(authorId: number): Promise<void> {
  return request<void>(`/authors/${authorId}`, {
    method: "DELETE",
  })
}

/* ── Members ──────────────────────────────────────── */

export async function listMembers(): Promise<MemberOut[]> {
  return request<MemberOut[]>("/members")
}

export async function getMember(id: number): Promise<MemberOut> {
  return request<MemberOut>(`/members/${id}`)
}

export async function getMemberSummary(): Promise<MemberSummaryOut> {
  return request<MemberSummaryOut>("/members/me/summary")
}

export async function payFine(memberId: number, amount: number): Promise<MemberOut> {
  return request<MemberOut>(`/members/${memberId}/pay-fine?amount=${amount}`, {
    method: "POST",
  })
}

export async function changeMembership(
  memberId: number,
  membershipTypeId: number,
): Promise<MemberOut> {
  return request<MemberOut>(`/members/${memberId}/membership`, {
    method: "PATCH",
    body: JSON.stringify({ membership_type_id: membershipTypeId }),
  })
}

/* ── Borrowing ────────────────────────────────────── */

export async function borrowBook(bookId: number, memberId: number): Promise<BorrowOut> {
  return request<BorrowOut>("/borrow", {
    method: "POST",
    body: JSON.stringify({ book_id: bookId, member_id: memberId }),
  })
}

export async function returnBook(borrowId: number): Promise<BorrowOut> {
  return request<BorrowOut>(`/return/${borrowId}`, {
    method: "POST",
  })
}

export async function renewBook(borrowId: number): Promise<BorrowOut> {
  return request<BorrowOut>(`/renew/${borrowId}`, {
    method: "POST",
  })
}

export async function markCopyLost(copyId: number): Promise<void> {
  return request<void>(`/copies/${copyId}/lost`, {
    method: "POST",
  })
}

/* ── Reservations ─────────────────────────────────── */

export async function reserveBook(bookId: number, memberId: number): Promise<unknown> {
  return request<unknown>("/reservations", {
    method: "POST",
    body: JSON.stringify({ book_id: bookId, member_id: memberId }),
  })
}

export async function cancelReservation(reservationId: number): Promise<void> {
  return request<void>(`/reservations/${reservationId}/cancel`, {
    method: "POST",
  })
}

/* ── Membership types ─────────────────────────────── */

export async function listMembershipTypes(): Promise<MembershipTypeOut[]> {
  return request<MembershipTypeOut[]>("/membership-types")
}

/* ── Test Results (Phase 4) ───────────────────────── */

export async function getTestResults(): Promise<TestResultsSummary> {
  return request<TestResultsSummary>("/tests/results")
}

export async function triggerTestRun(): Promise<TestResultsSummary> {
  return request<TestResultsSummary>("/tests/run", {
    method: "POST",
  })
}

/* Re-export for convenience */
export { getToken, setToken, request }
