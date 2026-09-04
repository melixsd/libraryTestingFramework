"use client"

import { create } from "zustand"
import type {
  DisplayBook,
  BookOut,
  AuthorOut,
  MemberOut,
  MemberSummaryOut,
  MembershipTypeOut,
  UserRole,
  UserOut,
  ViewName,
  TestResultsSummary,
} from "@/lib/types"
import { toDisplayBook } from "@/lib/types"
import * as api from "@/lib/api"

// ─── Async helpers ──────────────────────────────────

type LoadingState = "idle" | "loading" | "error"

interface AsyncSlice {
  status: LoadingState
  error: string | null
}

// ─── Per-operation status tracking ─────────────────

interface OperationStatus {
  booksStatus: LoadingState
  booksError: string | null
  authorsStatus: LoadingState
  authorsError: string | null
  membersStatus: LoadingState
  membersError: string | null
  summaryStatus: LoadingState
  summaryError: string | null
  membershipTypesStatus: LoadingState
  membershipTypesError: string | null
  testResultsStatus: LoadingState
  testResultsError: string | null
}

// ─── Test results slice ─────────────────────────────

interface TestResultsSlice {
  testResults: TestResultsSummary | null
  fetchTestResults: () => Promise<void>
  runTests: () => Promise<void>
}

// ─── Store state ────────────────────────────────────

interface LibraryState extends AsyncSlice, OperationStatus, TestResultsSlice {
  // Auth
  token: string | null
  currentUser: UserOut | null

  // Data (fetched from API)
  books: DisplayBook[]
  authors: AuthorOut[]
  members: MemberOut[]
  memberSummary: MemberSummaryOut | null
  membershipTypes: MembershipTypeOut[]

  // Navigation
  currentView: ViewName
  selectedBookId: number | null
  selectedAuthorId: number | null

  // Search & filter (client-side on already-fetched books)
  searchQuery: string
  searchField: "title" | "author" | "all"
  selectedGenres: string[]
  availabilityFilter: "all" | "available" | "unavailable"

  // Admin tab
  adminTab: "books" | "authors" | "members"

  // Actions — Auth
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  fetchCurrentUser: () => Promise<void>

  // Actions — Data fetching
  fetchBooks: (search?: string) => Promise<void>
  fetchBook: (id: number) => Promise<BookOut | undefined>
  fetchAuthors: () => Promise<void>
  fetchMembers: () => Promise<void>
  fetchMemberSummary: () => Promise<void>
  fetchMembershipTypes: () => Promise<void>

  // Actions — Navigation
  setView: (view: ViewName) => void
  selectBook: (bookId: number | null) => void
  selectAuthor: (authorId: number | null) => void

  // Actions — Search & filter
  setSearchQuery: (q: string) => void
  setSearchField: (field: "title" | "author" | "all") => void
  toggleGenre: (genre: string) => void
  clearGenres: () => void
  setAvailabilityFilter: (f: "all" | "available" | "unavailable") => void

  // Actions — Admin
  setAdminTab: (tab: "books" | "authors" | "members") => void

  // Actions — Mutations (call API then refresh)
  createBook: (data: Parameters<typeof api.createBook>[0]) => Promise<void>
  addCopies: (bookId: number, count: number) => Promise<void>
  removeCopy: (bookId: number, copyId: number) => Promise<void>
  createAuthor: (data: { name: string; nationality?: string }) => Promise<void>
  deleteAuthor: (authorId: number) => Promise<void>
  register: (data: {
    username: string
    email: string
    password: string
    full_name: string
    membership_type_id: number
  }) => Promise<void>
  approveMember: (memberId: number) => Promise<void>
  rejectMember: (memberId: number) => Promise<void>
  payFine: (memberId: number, amount: number) => Promise<void>

  // Actions — Borrowing (member)
  borrowBook: (bookId: number) => Promise<void>
  returnBook: (borrowId: number) => Promise<void>
  renewBook: (borrowId: number) => Promise<void>
  reserveBook: (bookId: number) => Promise<void>

  // Actions — Membership plan (member)
  changeMembership: (membershipTypeId: number) => Promise<void>

  // Convenience
  isAdmin: () => boolean
}

export const useLibraryStore = create<LibraryState>((set, get) => ({
  // ─── Initial state ──────────────────────────────
  // Global (kept for backward compat — login uses it)
  status: "idle",
  error: null,

  // Per-operation
  booksStatus: "idle",
  booksError: null,
  authorsStatus: "idle",
  authorsError: null,
  membersStatus: "idle",
  membersError: null,
  summaryStatus: "idle",
  summaryError: null,
  membershipTypesStatus: "idle",
  membershipTypesError: null,
  testResultsStatus: "idle",
  testResultsError: null,

  token: typeof window !== "undefined" ? localStorage.getItem("library_token") : null,
  currentUser: null,

  books: [],
  authors: [],
  members: [],
  memberSummary: null,
  membershipTypes: [],
  testResults: null,

  currentView: "home",
  selectedBookId: null,
  selectedAuthorId: null,

  searchQuery: "",
  searchField: "all",
  selectedGenres: [],
  availabilityFilter: "all",

  adminTab: "books",

  // ─── Auth actions ──────────────────────────────
  login: async (username, password) => {
    set({ status: "loading", error: null })
    try {
      const token = await api.login(username, password)
      const user = await api.getMe()
      set({ token: token.access_token, currentUser: user, status: "idle" })
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Login failed"
      set({ status: "error", error: msg })
      throw err
    }
  },

  logout: () => {
    api.logout()
    set({
      token: null,
      currentUser: null,
      memberSummary: null,
      currentView: "home",
    })
  },

  fetchCurrentUser: async () => {
    try {
      const user = await api.getMe()
      set({ currentUser: user, token: get().token })
    } catch {
      // Token might be expired — clear it
      api.logout()
      set({ token: null, currentUser: null })
    }
  },

  // ─── Data fetching ─────────────────────────────
  fetchBooks: async (search?: string) => {
    set({ booksStatus: "loading", booksError: null })
    try {
      const raw = await api.listBooks(search)
      set({ books: raw.map(toDisplayBook), booksStatus: "idle" })
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to fetch books"
      set({ booksStatus: "error", booksError: msg, status: "error", error: msg })
    }
  },

  fetchBook: async (id: number) => {
    try {
      const raw = await api.getBook(id)
      const display = toDisplayBook(raw)
      // Update or add to the books array
      set((state) => {
        const exists = state.books.findIndex((b) => b.id === id)
        if (exists >= 0) {
          const newBooks = [...state.books]
          newBooks[exists] = display
          return { books: newBooks }
        }
        return { books: [...state.books, display] }
      })
      return raw
    } catch {
      return undefined
    }
  },

  fetchAuthors: async () => {
    set({ authorsStatus: "loading", authorsError: null })
    try {
      const authors = await api.listAuthors()
      set({ authors, authorsStatus: "idle" })
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to fetch authors"
      set({ authorsStatus: "error", authorsError: msg })
    }
  },

  fetchMembers: async () => {
    set({ membersStatus: "loading", membersError: null })
    try {
      const members = await api.listMembers()
      set({ members, membersStatus: "idle" })
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to fetch members"
      set({ membersStatus: "error", membersError: msg })
    }
  },

  fetchMemberSummary: async () => {
    set({ summaryStatus: "loading", summaryError: null })
    try {
      const summary = await api.getMemberSummary()
      set({ memberSummary: summary, summaryStatus: "idle" })
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to fetch member summary"
      set({ summaryStatus: "error", summaryError: msg, memberSummary: null })
    }
  },

  fetchMembershipTypes: async () => {
    set({ membershipTypesStatus: "loading", membershipTypesError: null })
    try {
      const types = await api.listMembershipTypes()
      set({ membershipTypes: types, membershipTypesStatus: "idle" })
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to fetch membership plans"
      set({ membershipTypesStatus: "error", membershipTypesError: msg })
    }
  },

  // ─── Test Results ─────────────────────────────
  fetchTestResults: async () => {
    set({ testResultsStatus: "loading", testResultsError: null })
    try {
      const results = await api.getTestResults()
      set({ testResults: results, testResultsStatus: "idle" })
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to fetch test results"
      set({ testResultsStatus: "error", testResultsError: msg })
    }
  },

  runTests: async () => {
    set({ testResultsStatus: "loading", testResultsError: null })
    try {
      const results = await api.triggerTestRun()
      set({ testResults: results, testResultsStatus: "idle" })
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to run tests"
      set({ testResultsStatus: "error", testResultsError: msg })
    }
  },

  // ─── Navigation ─────────────────────────────────
  setView: (view) => set({ currentView: view }),

  selectBook: (bookId) =>
    set({
      selectedBookId: bookId,
      currentView: bookId ? "book-detail" : "home",
    }),

  selectAuthor: (authorId) =>
    set({
      selectedAuthorId: authorId,
      currentView: authorId ? "author-profile" : "home",
    }),

  // ─── Search & filter ───────────────────────────
  setSearchQuery: (q) => set({ searchQuery: q }),
  setSearchField: (field) => set({ searchField: field }),
  toggleGenre: (genre) =>
    set((state) => ({
      selectedGenres: state.selectedGenres.includes(genre)
        ? state.selectedGenres.filter((g) => g !== genre)
        : [...state.selectedGenres, genre],
    })),
  clearGenres: () => set({ selectedGenres: [] }),
  setAvailabilityFilter: (f) => set({ availabilityFilter: f }),

  // ─── Admin ─────────────────────────────────────
  setAdminTab: (tab) => set({ adminTab: tab }),

  // ─── Mutations ─────────────────────────────────
  createBook: async (data) => {
    await api.createBook(data)
    await get().fetchBooks()
  },

  addCopies: async (bookId, count) => {
    await api.addCopies(bookId, count)
    await get().fetchBooks()
  },

  removeCopy: async (bookId, copyId) => {
    await api.removeCopy(bookId, copyId)
    await get().fetchBooks()
  },

  createAuthor: async (data) => {
    await api.request("/authors", {
      method: "POST",
      body: JSON.stringify(data),
    })
    await get().fetchAuthors()
  },

  deleteAuthor: async (authorId) => {
    await api.deleteAuthor(authorId)
    await get().fetchAuthors()
  },

  register: async (data) => {
    // New signups are pending until an admin approves them, so the user is
    // NOT logged in afterwards — the auth page shows a confirmation instead.
    await api.register(data)
  },

  approveMember: async (memberId) => {
    await api.approveMember(memberId)
    await get().fetchMembers()
  },

  rejectMember: async (memberId) => {
    await api.rejectMember(memberId)
    await get().fetchMembers()
  },

  payFine: async (memberId, amount) => {
    await api.payFine(memberId, amount)
    await get().fetchMembers()
    await get().fetchMemberSummary()
  },

  // ─── Borrowing ─────────────────────────────────
  borrowBook: async (bookId) => {
    const user = get().currentUser
    if (!user?.member_id) return
    await api.borrowBook(bookId, user.member_id)
    await get().fetchBooks()
    await get().fetchMemberSummary()
  },

  returnBook: async (borrowId) => {
    await api.returnBook(borrowId)
    await get().fetchBooks()
    await get().fetchMemberSummary()
  },

  renewBook: async (borrowId) => {
    await api.renewBook(borrowId)
    await get().fetchMemberSummary()
  },

  reserveBook: async (bookId) => {
    const user = get().currentUser
    if (!user?.member_id) return
    await api.reserveBook(bookId, user.member_id)
    await get().fetchMemberSummary()
  },

  // ─── Membership plan ───────────────────────────
  changeMembership: async (membershipTypeId) => {
    const user = get().currentUser
    if (!user?.member_id) return
    await api.changeMembership(user.member_id, membershipTypeId)
    await get().fetchMemberSummary()
  },

  // ─── Convenience ───────────────────────────────
  isAdmin: () => {
    const role = get().currentUser?.role
    return role === "admin" || role === "librarian"
  },
}))
