"use client"

import { useEffect, useState, useCallback } from "react"
import { useLibraryStore } from "@/store/library-store"
import {
  BookOpen,
  Users,
  PenTool,
  Plus,
  Trash2,
  Search,
  Shield,
  TrendingUp,
  Library,
  X,
  Save,
  Loader2,
  RefreshCw,
  AlertTriangle,
  Inbox,
  FileQuestion,
} from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { cn } from "@/lib/utils"
import { springSoft, springSnappy, fadeUp, staggerContainer } from "@/lib/motion"
import { MemberStatusBadge } from "@/components/shared/status-badge"

type AdminTab = "books" | "authors" | "members"

export function AdminProfilePage() {
  const adminTab = useLibraryStore((s) => s.adminTab)
  const setAdminTab = useLibraryStore((s) => s.setAdminTab)
  const books = useLibraryStore((s) => s.books)
  const authors = useLibraryStore((s) => s.authors)
  const members = useLibraryStore((s) => s.members)
  const booksStatus = useLibraryStore((s) => s.booksStatus)
  const authorsStatus = useLibraryStore((s) => s.authorsStatus)
  const membersStatus = useLibraryStore((s) => s.membersStatus)
  const booksError = useLibraryStore((s) => s.booksError)
  const authorsError = useLibraryStore((s) => s.authorsError)
  const membersError = useLibraryStore((s) => s.membersError)
  const fetchBooks = useLibraryStore((s) => s.fetchBooks)
  const fetchAuthors = useLibraryStore((s) => s.fetchAuthors)
  const fetchMembers = useLibraryStore((s) => s.fetchMembers)
  const [dismissedErrors, setDismissedErrors] = useState<Set<string>>(new Set())

  const dismissError = useCallback((key: string) => {
    setDismissedErrors((prev) => new Set(prev).add(key))
  }, [])

  useEffect(() => {
    fetchBooks()
    fetchAuthors()
    fetchMembers()
  }, [fetchBooks, fetchAuthors, fetchMembers])

  const totalAvailable = books.filter((b) => b.available_copies > 0).length
  const activeMembers = members.filter((m) => m.is_active).length
  const inactiveMembers = members.filter((m) => !m.is_active).length

  const anyLoading = booksStatus === "loading" || authorsStatus === "loading" || membersStatus === "loading"

  const activeErrors: { key: string; msg: string }[] = []
  if (booksError && !dismissedErrors.has("books")) activeErrors.push({ key: "books", msg: `Books: ${booksError}` })
  if (authorsError && !dismissedErrors.has("authors")) activeErrors.push({ key: "authors", msg: `Authors: ${authorsError}` })
  if (membersError && !dismissedErrors.has("members")) activeErrors.push({ key: "members", msg: `Members: ${membersError}` })

  return (
    <div
      className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8"
      data-testid="admin-page"
    >
      {/* Admin header */}
      <motion.section
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={springSoft}
        className="mb-8 overflow-hidden rounded-2xl border border-border bg-card shadow-lifted"
      >
        <div className="flex flex-col gap-4 p-6 sm:flex-row sm:items-center sm:justify-between sm:p-8">
          <div className="flex items-center gap-4">
            <motion.div
              whileHover={{ rotate: -3, scale: 1.05 }}
              transition={springSoft}
              className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-card"
            >
              <Shield className="h-7 w-7" />
            </motion.div>
            <div>
              <span className="inline-flex items-center gap-1.5 rounded-full bg-secondary/70 px-2.5 py-0.5 text-xs font-medium text-secondary-foreground">
                Administrator
              </span>
              <h1 className="mt-2 font-serif text-[1.75rem] font-semibold tracking-tight sm:text-[2rem]">
                Library Management Console
              </h1>
              <p className="mt-1 text-sm text-muted-foreground">
                Manage books, authors, and members across the Aldenwood collection.
              </p>
            </div>
          </div>
          <motion.button
            whileHover={{ y: -1 }}
            whileTap={{ scale: 0.96 }}
            transition={springSnappy}
            onClick={() => {
              setDismissedErrors(new Set())
              fetchBooks()
              fetchAuthors()
              fetchMembers()
            }}
            disabled={anyLoading}
            className="inline-flex shrink-0 cursor-pointer items-center gap-1.5 rounded-lg border border-border px-3.5 py-2 text-xs font-medium text-muted-foreground transition-colors hover:border-primary/30 hover:bg-accent hover:text-foreground disabled:cursor-not-allowed disabled:opacity-50"
            data-testid="btn-refresh-all"
          >
            <RefreshCw
              className={cn("h-3.5 w-3.5", anyLoading && "animate-spin")}
            />
            Refresh
          </motion.button>
        </div>

        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="show"
          className="grid grid-cols-2 gap-px border-t border-border bg-border sm:grid-cols-4"
        >
          <KPI
            icon={Library}
            label="Total books"
            value={String(books.length)}
          />
          <KPI
            icon={BookOpen}
            label="Available"
            value={String(totalAvailable)}
          />
          <KPI
            icon={Users}
            label="Active members"
            value={String(activeMembers)}
          />
          <KPI
            icon={TrendingUp}
            label="Inactive"
            value={String(inactiveMembers)}
            tone={inactiveMembers > 0 ? "warning" : "default"}
          />
        </motion.div>
      </motion.section>

      {/* Error banners */}
      <AnimatePresence>
        {activeErrors.map((err) => (
          <motion.div
            key={err.key}
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6, transition: { duration: 0.15 } }}
            transition={springSoft}
            className="mb-4 flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 dark:border-amber-900 dark:bg-amber-950/30"
          >
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400" />
            <p className="flex-1 text-sm text-amber-800 dark:text-amber-200">{err.msg}</p>
            <button
              onClick={() => dismissError(err.key)}
              className="shrink-0 cursor-pointer rounded-md p-1 text-amber-600 hover:bg-amber-100 dark:text-amber-400 dark:hover:bg-amber-900/40"
              aria-label="Dismiss error"
            >
              <X className="h-4 w-4" />
            </button>
          </motion.div>
        ))}
      </AnimatePresence>

      {/* Tabs */}
      <div className="mb-6 flex items-center gap-1 overflow-x-auto border-b border-border">
        <AdminTabButton
          label="Books"
          icon={BookOpen}
          count={books.length}
          active={adminTab === "books"}
          onClick={() => setAdminTab("books")}
          testId="tab-books"
        />
        <AdminTabButton
          label="Authors"
          icon={PenTool}
          count={authors.length}
          active={adminTab === "authors"}
          onClick={() => setAdminTab("authors")}
          testId="tab-authors"
        />
        <AdminTabButton
          label="Members"
          icon={Users}
          count={members.length}
          active={adminTab === "members"}
          onClick={() => setAdminTab("members")}
          testId="tab-members"
        />
      </div>

      <AnimatePresence mode="wait">
        {adminTab === "books" && <BooksAdmin key="books" />}
        {adminTab === "authors" && <AuthorsAdmin key="authors" />}
        {adminTab === "members" && <MembersAdmin key="members" />}
      </AnimatePresence>
    </div>
  )
}

/* ───────────────────────────  BOOKS  ─────────────────────────── */

function BooksAdmin() {
  const books = useLibraryStore((s) => s.books)
  const authors = useLibraryStore((s) => s.authors)
  const booksStatus = useLibraryStore((s) => s.booksStatus)
  const booksError = useLibraryStore((s) => s.booksError)
  const createBook = useLibraryStore((s) => s.createBook)
  const addCopies = useLibraryStore((s) => s.addCopies)
  const removeCopy = useLibraryStore((s) => s.removeCopy)
  const fetchBooks = useLibraryStore((s) => s.fetchBooks)

  const [search, setSearch] = useState("")
  const [showAdd, setShowAdd] = useState(false)
  const [showAddCopies, setShowAddCopies] = useState<number | null>(null)
  const [copiesCount, setCopiesCount] = useState(1)
  const [saving, setSaving] = useState(false)
  const [formError, setFormError] = useState("")

  const [newTitle, setNewTitle] = useState("")
  const [newIsbn, setNewIsbn] = useState("")
  const [newPrice, setNewPrice] = useState("29.99")
  const [newAuthorId, setNewAuthorId] = useState<number>(authors[0]?.id ?? 0)
  const [newCopies, setNewCopies] = useState("3")
  const [newDescription, setNewDescription] = useState("")

  const filtered = books.filter(
    (b) =>
      b.title.toLowerCase().includes(search.toLowerCase()) ||
      b.authorName.toLowerCase().includes(search.toLowerCase()) ||
      b.isbn.includes(search),
  )

  async function handleAddBook() {
    setFormError("")
    setSaving(true)
    try {
      await createBook({
        title: newTitle,
        isbn: newIsbn,
        price: parseFloat(newPrice) || 29.99,
        author_ids: [newAuthorId],
        number_of_copies: parseInt(newCopies) || 3,
        description: newDescription || undefined,
      })
      setShowAdd(false)
      setNewTitle("")
      setNewIsbn("")
      setNewDescription("")
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Failed to create book")
    } finally {
      setSaving(false)
    }
  }

  async function handleAddCopies(bookId: number) {
    setFormError("")
    setSaving(true)
    try {
      await addCopies(bookId, copiesCount)
      setShowAddCopies(null)
      setCopiesCount(1)
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Failed to add copies")
    } finally {
      setSaving(false)
    }
  }

  async function handleRemoveCopy(bookId: number, copyId: number) {
    if (!confirm(`Remove copy #${copyId}? This cannot be undone if the copy is borrowed.`))
      return
    setSaving(true)
    try {
      await removeCopy(bookId, copyId)
    } finally {
      setSaving(false)
    }
  }

  if (booksStatus === "loading" && books.length === 0) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
        <span className="ml-3 text-sm text-muted-foreground">Loading books…</span>
      </div>
    )
  }

  if (booksStatus === "error" && books.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border py-16 text-center">
        <FileQuestion className="mb-3 h-10 w-10 text-rose-400" />
        <p className="text-sm font-medium">Failed to load books</p>
        <p className="mt-1 text-xs text-muted-foreground">{booksError}</p>
        <motion.button
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.96 }}
          transition={springSnappy}
          onClick={() => fetchBooks()}
          className="mt-4 inline-flex cursor-pointer items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Retry
        </motion.button>
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8, transition: { duration: 0.15 } }}
      transition={springSoft}
    >
      <Toolbar
        search={search}
        onSearch={setSearch}
        placeholder="Search by title, author, or ISBN..."
        actionLabel="Add book"
        onAction={() => setShowAdd(true)}
        testId="books-toolbar"
      />

      <motion.div layout className="overflow-hidden rounded-xl border border-border bg-card shadow-card">
        <div className="overflow-x-auto">
          <table
            className="w-full min-w-[640px] text-sm"
            data-testid="books-table"
          >
            <thead className="bg-secondary/50 text-[11px] uppercase tracking-[0.1em] text-muted-foreground/80">
              <tr>
                <th className="px-4 py-3 text-left font-medium">Title</th>
                <th className="px-4 py-3 text-left font-medium">Author(s)</th>
                <th className="hidden px-4 py-3 text-left font-medium sm:table-cell">ISBN</th>
                <th className="px-4 py-3 text-left font-medium">Copies</th>
                <th className="hidden px-4 py-3 text-left font-medium md:table-cell">Price</th>
                <th className="px-4 py-3 text-right font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filtered.map((book) => (
                <tr
                  key={book.id}
                  className="transition-colors hover:bg-accent/20"
                  data-testid={`book-row-${book.id}`}
                >
                  <td className="px-4 py-3.5 font-medium tracking-tight">{book.title}</td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {book.authorName}
                  </td>
                  <td className="hidden px-4 py-3 font-mono text-xs text-muted-foreground sm:table-cell">
                    {book.isbn}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={cn(
                        "rounded-md px-2 py-0.5 text-xs font-medium",
                        book.available_copies > 0
                          ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300"
                          : "bg-rose-100 text-rose-800 dark:bg-rose-950/40 dark:text-rose-300",
                      )}
                      data-testid={`book-copies-${book.id}`}
                    >
                      {book.available_copies} / {book.total_copies}
                    </span>
                  </td>
                  <td className="hidden px-4 py-3 text-muted-foreground md:table-cell">
                    ${book.price.toFixed(2)}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-1">
                      <IconBtn
                        icon={Plus}
                        label="Add copies"
                        onClick={() => setShowAddCopies(book.id)}
                        testId={`btn-add-copies-${book.id}`}
                      />
                      <IconBtn
                        icon={Trash2}
                        label="Remove copy"
                        destructive
                        onClick={() =>
                          handleRemoveCopy(
                            book.id,
                            book.total_copies > 0 ? book.total_copies : 1,
                          )
                        }
                        testId={`btn-remove-copy-${book.id}`}
                      />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {filtered.length === 0 && books.length > 0 && (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <Search className="mb-2 h-8 w-8 text-muted-foreground/40" />
            <p className="text-sm text-muted-foreground">
              {search ? "No books match your search." : "No books in the catalogue yet."}
            </p>
          </div>
        )}
        {books.length === 0 && booksStatus !== "loading" && booksStatus !== "error" && (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <Inbox className="mb-2 h-8 w-8 text-muted-foreground/40" />
            <p className="text-sm font-medium">No books yet</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Click "Add book" to add your first book to the catalogue.
            </p>
          </div>
        )}
      </motion.div>

      {/* Add book dialog */}
      <AnimatePresence>
        {showAdd && (
          <Modal title="Add new book" onClose={() => setShowAdd(false)}>
            <div className="space-y-3">
              <Field label="Title" full>
                <Input
                  value={newTitle}
                  onChange={setNewTitle}
                  placeholder="Book title"
                  testId="add-book-title"
                />
              </Field>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <Field label="Author" full>
                  <select
                    value={newAuthorId}
                    onChange={(e) => setNewAuthorId(Number(e.target.value))}
                    data-testid="add-book-author"
                    className="h-10 w-full cursor-pointer rounded-lg border border-border bg-background px-3 text-sm outline-none transition-smooth focus:border-primary"
                  >
                    {authors.map((a) => (
                      <option key={a.id} value={a.id}>
                        {a.name}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label="ISBN" full>
                  <Input
                    value={newIsbn}
                    onChange={setNewIsbn}
                    placeholder="978-0-000-00000-0"
                    testId="add-book-isbn"
                  />
                </Field>
                <Field label="Price ($)">
                  <Input
                    value={newPrice}
                    onChange={setNewPrice}
                    type="number"
                    testId="add-book-price"
                  />
                </Field>
                <Field label="Copies">
                  <Input
                    value={newCopies}
                    onChange={setNewCopies}
                    type="number"
                    testId="add-book-copies"
                  />
                </Field>
              </div>
              <Field label="Description" full>
                <TextArea
                  value={newDescription}
                  onChange={setNewDescription}
                  testId="add-book-desc"
                />
              </Field>
            </div>

            {formError && (
              <motion.div
                initial={{ opacity: 0, y: -6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={springSoft}
                className="mt-3 rounded-lg border border-rose-200 bg-rose-50 px-4 py-2.5 text-sm text-rose-700 dark:border-rose-800 dark:bg-rose-950/30 dark:text-rose-300"
                data-testid="form-error"
              >
                {formError}
              </motion.div>
            )}

            <div className="mt-5 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
              <button
                onClick={() => setShowAdd(false)}
                className="cursor-pointer rounded-lg border border-border px-4 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-accent"
              >
                Cancel
              </button>
              <motion.button
                whileHover={{ scale: saving ? 1 : 1.02 }}
                whileTap={{ scale: saving ? 1 : 0.97 }}
                transition={springSnappy}
                onClick={handleAddBook}
                disabled={saving || !newTitle.trim() || !newIsbn.trim()}
                data-testid="btn-add-book-submit"
                className="inline-flex cursor-pointer items-center justify-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {saving ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <Save className="h-4 w-4" />
                )}
                Create book
              </motion.button>
            </div>
          </Modal>
        )}
      </AnimatePresence>

      {/* Add copies dialog */}
      <AnimatePresence>
        {showAddCopies !== null && (
          <Modal title="Add copies" onClose={() => setShowAddCopies(null)}>
            <Field label="Number of copies to add" full>
              <Input
                value={String(copiesCount)}
                onChange={(v) => setCopiesCount(Math.max(1, parseInt(v) || 1))}
                type="number"
                testId="add-copies-count"
              />
            </Field>
            {formError && (
              <motion.div
                initial={{ opacity: 0, y: -6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={springSoft}
                className="mt-3 rounded-lg border border-rose-200 bg-rose-50 px-4 py-2.5 text-sm text-rose-700 dark:border-rose-800 dark:bg-rose-950/30 dark:text-rose-300"
                data-testid="form-error"
              >
                {formError}
              </motion.div>
            )}
            <div className="mt-5 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
              <button
                onClick={() => setShowAddCopies(null)}
                className="cursor-pointer rounded-lg border border-border px-4 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-accent"
              >
                Cancel
              </button>
              <motion.button
                whileHover={{ scale: saving ? 1 : 1.02 }}
                whileTap={{ scale: saving ? 1 : 0.97 }}
                transition={springSnappy}
                onClick={() => handleAddCopies(showAddCopies)}
                disabled={saving}
                data-testid="btn-add-copies-submit"
                className="inline-flex cursor-pointer items-center justify-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {saving ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <Plus className="h-4 w-4" />
                )}
                Add copies
              </motion.button>
            </div>
          </Modal>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

/* ───────────────────────────  AUTHORS  ─────────────────────────── */

function AuthorsAdmin() {
  const authors = useLibraryStore((s) => s.authors)
  const books = useLibraryStore((s) => s.books)
  const authorsStatus = useLibraryStore((s) => s.authorsStatus)
  const authorsError = useLibraryStore((s) => s.authorsError)
  const createAuthor = useLibraryStore((s) => s.createAuthor)
  const deleteAuthor = useLibraryStore((s) => s.deleteAuthor)
  const fetchAuthors = useLibraryStore((s) => s.fetchAuthors)

  const [search, setSearch] = useState("")
  const [showAdd, setShowAdd] = useState(false)
  const [newName, setNewName] = useState("")
  const [newNationality, setNewNationality] = useState("")
  const [saving, setSaving] = useState(false)
  const [formError, setFormError] = useState("")

  const filtered = authors.filter(
    (a) =>
      a.name.toLowerCase().includes(search.toLowerCase()) ||
      (a.nationality ?? "").toLowerCase().includes(search.toLowerCase()),
  )

  function bookCount(authorId: number) {
    return books.filter((b) => b.authors.some((a) => a.id === authorId)).length
  }

  async function handleAddAuthor() {
    setFormError("")
    setSaving(true)
    try {
      await createAuthor({
        name: newName,
        nationality: newNationality || undefined,
      })
      setShowAdd(false)
      setNewName("")
      setNewNationality("")
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Failed to create author")
    } finally {
      setSaving(false)
    }
  }

  async function handleRemoveAuthor(authorId: number) {
    const count = bookCount(authorId)
    if (count > 0) {
      setFormError(`Cannot remove: this author has ${count} book(s) in the catalogue.`)
      return
    }
    if (!confirm(`Remove this author? This cannot be undone.`)) return
    setFormError("")
    setSaving(true)
    try {
      await deleteAuthor(authorId)
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Failed to remove author")
    } finally {
      setSaving(false)
    }
  }

  if (authorsStatus === "loading" && authors.length === 0) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
        <span className="ml-3 text-sm text-muted-foreground">Loading authors…</span>
      </div>
    )
  }

  if (authorsStatus === "error" && authors.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border py-16 text-center">
        <FileQuestion className="mb-3 h-10 w-10 text-rose-400" />
        <p className="text-sm font-medium">Failed to load authors</p>
        <p className="mt-1 text-xs text-muted-foreground">{authorsError}</p>
        <motion.button
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.96 }}
          transition={springSnappy}
          onClick={() => fetchAuthors()}
          className="mt-4 inline-flex cursor-pointer items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Retry
        </motion.button>
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8, transition: { duration: 0.15 } }}
      transition={springSoft}
    >
      <Toolbar
        search={search}
        onSearch={setSearch}
        placeholder="Search authors..."
        actionLabel="Add author"
        onAction={() => setShowAdd(true)}
        testId="authors-toolbar"
      />

      <motion.div layout className="overflow-hidden rounded-xl border border-border bg-card shadow-card">
        <div className="overflow-x-auto">
          <table
            className="w-full min-w-[400px] text-sm"
            data-testid="authors-table"
          >
            <thead className="bg-secondary/50 text-[11px] uppercase tracking-[0.1em] text-muted-foreground/80">
              <tr>
                <th className="px-4 py-3 text-left font-medium">Name</th>
                <th className="hidden px-4 py-3 text-left font-medium sm:table-cell">Nationality</th>
                <th className="px-4 py-3 text-left font-medium">Books</th>
                <th className="px-4 py-3 text-right font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filtered.map((author) => (
                <tr
                  key={author.id}
                  className="transition-colors hover:bg-accent/20"
                  data-testid={`author-row-${author.id}`}
                >
                  <td className="px-4 py-3.5 font-medium tracking-tight">{author.name}</td>
                  <td className="hidden px-4 py-3 text-muted-foreground sm:table-cell">
                    {author.nationality ?? "—"}
                  </td>
                  <td className="px-4 py-3">
                    <span className="rounded-md bg-secondary px-2 py-0.5 text-xs font-medium">
                      {bookCount(author.id)}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end">
                      <IconBtn
                        icon={Trash2}
                        label="Remove author"
                        destructive
                        disabled={bookCount(author.id) > 0}
                        onClick={() => handleRemoveAuthor(author.id)}
                        testId={`btn-remove-author-${author.id}`}
                      />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {filtered.length === 0 && authors.length > 0 && (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <Search className="mb-2 h-8 w-8 text-muted-foreground/40" />
            <p className="text-sm text-muted-foreground">
              {search ? "No authors match your search." : "No authors in the catalogue yet."}
            </p>
          </div>
        )}
        {authors.length === 0 && authorsStatus !== "loading" && authorsStatus !== "error" && (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <Inbox className="mb-2 h-8 w-8 text-muted-foreground/40" />
            <p className="text-sm font-medium">No authors yet</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Click "Add author" to register your first author.
            </p>
          </div>
        )}
      </motion.div>

      {/* Add author dialog */}
      <AnimatePresence>
        {showAdd && (
          <Modal title="Add new author" onClose={() => setShowAdd(false)}>
            <div className="space-y-3">
              <Field label="Name" full>
                <Input
                  value={newName}
                  onChange={setNewName}
                  placeholder="Author name"
                  testId="add-author-name"
                />
              </Field>
              <Field label="Nationality" full>
                <Input
                  value={newNationality}
                  onChange={setNewNationality}
                  placeholder="e.g. American"
                  testId="add-author-nationality"
                />
              </Field>
            </div>
            {formError && (
              <motion.div
                initial={{ opacity: 0, y: -6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={springSoft}
                className="mt-3 rounded-lg border border-rose-200 bg-rose-50 px-4 py-2.5 text-sm text-rose-700 dark:border-rose-800 dark:bg-rose-950/30 dark:text-rose-300"
                data-testid="form-error"
              >
                {formError}
              </motion.div>
            )}
            <div className="mt-5 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
              <button
                onClick={() => setShowAdd(false)}
                className="cursor-pointer rounded-lg border border-border px-4 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-accent"
              >
                Cancel
              </button>
              <motion.button
                whileHover={{ scale: saving ? 1 : 1.02 }}
                whileTap={{ scale: saving ? 1 : 0.97 }}
                transition={springSnappy}
                onClick={handleAddAuthor}
                disabled={saving || !newName.trim()}
                data-testid="btn-add-author-submit"
                className="inline-flex cursor-pointer items-center justify-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {saving ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <Save className="h-4 w-4" />
                )}
                Create author
              </motion.button>
            </div>
          </Modal>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

/* ───────────────────────────  MEMBERS  ─────────────────────────── */

function MembersAdmin() {
  const members = useLibraryStore((s) => s.members)
  const membersStatus = useLibraryStore((s) => s.membersStatus)
  const membersError = useLibraryStore((s) => s.membersError)
  const createMember = useLibraryStore((s) => s.createMember)
  const payFine = useLibraryStore((s) => s.payFine)
  const fetchMembers = useLibraryStore((s) => s.fetchMembers)

  const [search, setSearch] = useState("")
  const [showAdd, setShowAdd] = useState(false)
  const [saving, setSaving] = useState(false)

  const [newName, setNewName] = useState("")
  const [newEmail, setNewEmail] = useState("")
  const [newTierId, setNewTierId] = useState("2")

  const [payFineMemberId, setPayFineMemberId] = useState<number | null>(null)
  const [payAmount, setPayAmount] = useState("")

  const filtered = members.filter(
    (m) =>
      m.full_name.toLowerCase().includes(search.toLowerCase()) ||
      m.email.toLowerCase().includes(search.toLowerCase()),
  )

  async function handleAddMember() {
    setSaving(true)
    try {
      await createMember({
        full_name: newName,
        email: newEmail,
        membership_type_id: parseInt(newTierId),
      })
      setShowAdd(false)
      setNewName("")
      setNewEmail("")
    } finally {
      setSaving(false)
    }
  }

  async function handlePayFine() {
    if (payFineMemberId === null) return
    setSaving(true)
    try {
      await payFine(payFineMemberId, parseFloat(payAmount) || 0)
      setPayFineMemberId(null)
      setPayAmount("")
    } finally {
      setSaving(false)
    }
  }

  if (membersStatus === "loading" && members.length === 0) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
        <span className="ml-3 text-sm text-muted-foreground">Loading members…</span>
      </div>
    )
  }

  if (membersStatus === "error" && members.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border py-16 text-center">
        <FileQuestion className="mb-3 h-10 w-10 text-rose-400" />
        <p className="text-sm font-medium">Failed to load members</p>
        <p className="mt-1 text-xs text-muted-foreground">{membersError}</p>
        <motion.button
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.96 }}
          transition={springSnappy}
          onClick={() => fetchMembers()}
          className="mt-4 inline-flex cursor-pointer items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Retry
        </motion.button>
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8, transition: { duration: 0.15 } }}
      transition={springSoft}
    >
      <Toolbar
        search={search}
        onSearch={setSearch}
        placeholder="Search members..."
        actionLabel="Add member"
        onAction={() => setShowAdd(true)}
        testId="members-toolbar"
      />

      <motion.div layout className="overflow-hidden rounded-xl border border-border bg-card shadow-card">
        <div className="overflow-x-auto">
          <table
            className="w-full min-w-[520px] text-sm"
            data-testid="members-table"
          >
            <thead className="bg-secondary/50 text-[11px] uppercase tracking-[0.1em] text-muted-foreground/80">
              <tr>
                <th className="px-4 py-3 text-left font-medium">Name</th>
                <th className="hidden px-4 py-3 text-left font-medium sm:table-cell">Email</th>
                <th className="px-4 py-3 text-left font-medium">Status</th>
                <th className="hidden px-4 py-3 text-left font-medium md:table-cell">Tier</th>
                <th className="px-4 py-3 text-left font-medium">Fines</th>
                <th className="px-4 py-3 text-right font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filtered.map((member) => (
                <tr
                  key={member.id}
                  className="transition-colors hover:bg-accent/20"
                  data-testid={`member-row-${member.id}`}
                >
                  <td className="px-4 py-3.5 font-medium tracking-tight">{member.full_name}</td>
                  <td className="hidden px-4 py-3 text-muted-foreground sm:table-cell">
                    {member.email}
                  </td>
                  <td className="px-4 py-3">
                    <MemberStatusBadge isActive={member.is_active} />
                  </td>
                  <td className="hidden px-4 py-3 md:table-cell">
                    <span className="rounded-md bg-secondary px-2 py-0.5 text-xs font-medium">
                      {member.membership_type.name}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={cn(
                        "text-xs font-medium",
                        member.outstanding_fine > 0
                          ? "text-rose-600"
                          : "text-emerald-600",
                      )}
                      data-testid={`member-fines-${member.id}`}
                    >
                      ${member.outstanding_fine.toFixed(2)}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-1">
                      {member.outstanding_fine > 0 && (
                        <motion.button
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          transition={springSnappy}
                          onClick={() => setPayFineMemberId(member.id)}
                          className="inline-flex cursor-pointer items-center gap-1 rounded-md border border-amber-200 bg-amber-50 px-2 py-1 text-xs font-medium text-amber-800 transition-colors hover:bg-amber-100 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-300"
                          data-testid={`btn-pay-fine-${member.id}`}
                        >
                          Pay fine
                        </motion.button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {filtered.length === 0 && members.length > 0 && (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <Search className="mb-2 h-8 w-8 text-muted-foreground/40" />
            <p className="text-sm text-muted-foreground">
              {search ? "No members match your search." : "No members in the system yet."}
            </p>
          </div>
        )}
        {members.length === 0 && membersStatus !== "loading" && membersStatus !== "error" && (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <Inbox className="mb-2 h-8 w-8 text-muted-foreground/40" />
            <p className="text-sm font-medium">No members yet</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Click "Add member" to register your first member.
            </p>
          </div>
        )}
      </motion.div>

      {/* Add member dialog */}
      <AnimatePresence>
        {showAdd && (
          <Modal title="Add new member" onClose={() => setShowAdd(false)}>
            <div className="space-y-3">
              <Field label="Full name" full>
                <Input
                  value={newName}
                  onChange={setNewName}
                  placeholder="John Doe"
                  testId="add-member-name"
                />
              </Field>
              <Field label="Email" full>
                <Input
                  value={newEmail}
                  onChange={setNewEmail}
                  placeholder="john@example.com"
                  testId="add-member-email"
                />
              </Field>
              <Field label="Membership tier" full>
                <select
                  value={newTierId}
                  onChange={(e) => setNewTierId(e.target.value)}
                  data-testid="add-member-tier"
                  className="h-10 w-full cursor-pointer rounded-lg border border-border bg-background px-3 text-sm outline-none transition-smooth focus:border-primary"
                >
                  <option value="1">Student</option>
                  <option value="2">Regular</option>
                  <option value="3">Premium</option>
                </select>
              </Field>
            </div>
            <div className="mt-5 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
              <button
                onClick={() => setShowAdd(false)}
                className="cursor-pointer rounded-lg border border-border px-4 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-accent"
              >
                Cancel
              </button>
              <motion.button
                whileHover={{ scale: saving ? 1 : 1.02 }}
                whileTap={{ scale: saving ? 1 : 0.97 }}
                transition={springSnappy}
                onClick={handleAddMember}
                disabled={saving || !newName.trim() || !newEmail.trim()}
                data-testid="btn-add-member-submit"
                className="inline-flex cursor-pointer items-center justify-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {saving ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <Save className="h-4 w-4" />
                )}
                Create member
              </motion.button>
            </div>
          </Modal>
        )}
      </AnimatePresence>

      {/* Pay fine dialog */}
      <AnimatePresence>
        {payFineMemberId !== null && (
          <Modal title="Pay fine" onClose={() => setPayFineMemberId(null)}>
            <Field label="Amount ($)" full>
              <Input
                value={payAmount}
                onChange={setPayAmount}
                type="number"
                placeholder="10.00"
                testId="pay-fine-amount"
              />
            </Field>
            <div className="mt-5 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
              <button
                onClick={() => setPayFineMemberId(null)}
                className="cursor-pointer rounded-lg border border-border px-4 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-accent"
              >
                Cancel
              </button>
              <motion.button
                whileHover={{ scale: saving ? 1 : 1.02 }}
                whileTap={{ scale: saving ? 1 : 0.97 }}
                transition={springSnappy}
                onClick={handlePayFine}
                disabled={saving || !payAmount || parseFloat(payAmount) <= 0}
                data-testid="btn-pay-fine-submit"
                className="inline-flex cursor-pointer items-center justify-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {saving ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <Save className="h-4 w-4" />
                )}
                Pay
              </motion.button>
            </div>
          </Modal>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

/* ───────────────────────────  SHARED UI  ─────────────────────────── */

function KPI({
  icon: Icon,
  label,
  value,
  tone = "default",
}: {
  icon: React.ComponentType<{ className?: string }>
  label: string
  value: string
  tone?: "default" | "warning"
}) {
  return (
    <motion.div
      variants={{
        hidden: { opacity: 0, y: 10 },
        show: { opacity: 1, y: 0, transition: springSoft },
      }}
      className="flex items-center gap-3 bg-card px-4 py-4 transition-colors hover:bg-accent/20"
      data-testid={`kpi-${label.toLowerCase().replace(" ", "-")}`}
    >
      <Icon
        className={cn(
          "h-5 w-5",
          tone === "warning" ? "text-amber-500" : "text-primary/70",
        )}
      />
      <div>
        <p className="font-serif text-xl font-semibold leading-none tracking-tight">{value}</p>
        <p className="mt-1 text-[11px] text-muted-foreground/80">{label}</p>
      </div>
    </motion.div>
  )
}

function AdminTabButton({
  label,
  icon: Icon,
  count,
  active,
  onClick,
  testId,
}: {
  label: string
  icon: React.ComponentType<{ className?: string }>
  count: number
  active: boolean
  onClick: () => void
  testId?: string
}) {
  return (
    <button
      onClick={onClick}
      data-testid={testId}
      aria-selected={active}
      role="tab"
      className={cn(
        "flex cursor-pointer items-center gap-2 whitespace-nowrap border-b-2 px-4 py-2.5 text-sm font-medium transition-colors",
        active
          ? "border-primary text-primary"
          : "border-transparent text-muted-foreground hover:text-foreground",
      )}
    >
      <Icon className="h-4 w-4" />
      {label}
      <span
        className={cn(
          "rounded-full px-1.5 py-0.5 text-[10px] font-medium transition-colors",
          active
            ? "bg-primary/15 text-primary"
            : "bg-secondary/70 text-secondary-foreground",
        )}
      >
        {count}
      </span>
    </button>
  )
}

function Toolbar({
  search,
  onSearch,
  placeholder,
  actionLabel,
  onAction,
  testId,
}: {
  search: string
  onSearch: (v: string) => void
  placeholder: string
  actionLabel: string
  onAction: () => void
  testId?: string
}) {
  return (
      <div
      className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center"
      data-testid={testId}
    >
      <div className="relative flex-1">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          value={search}
          onChange={(e) => onSearch(e.target.value)}
          placeholder={placeholder}
          data-testid={`${testId}-search`}
          className="h-10 w-full rounded-lg border border-border bg-card pl-9 pr-3 text-sm shadow-card outline-none transition-smooth placeholder:text-muted-foreground/50 focus:border-primary/50 focus:ring-2 focus:ring-primary/15"
        />
      </div>
      <motion.button
        whileHover={{ y: -1 }}
        whileTap={{ scale: 0.97 }}
        transition={springSnappy}
        onClick={onAction}
        data-testid={`${testId}-add`}
        className="inline-flex cursor-pointer items-center justify-center gap-1.5 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground shadow-card transition-colors hover:bg-primary/90"
      >
        <Plus className="h-4 w-4" />
        {actionLabel}
      </motion.button>
    </div>
  )
}

function IconBtn({
  icon: Icon,
  label,
  destructive,
  disabled,
  onClick,
  testId,
}: {
  icon: React.ComponentType<{ className?: string }>
  label: string
  destructive?: boolean
  disabled?: boolean
  onClick: () => void
  testId?: string
}) {
  return (
    <motion.button
      whileHover={disabled ? undefined : { scale: 1.12 }}
      whileTap={disabled ? undefined : { scale: 0.9 }}
      transition={springSnappy}
      onClick={onClick}
      disabled={disabled}
      data-testid={testId}
      title={label}
      aria-label={label}
      className={cn(
        "inline-flex h-8 w-8 items-center justify-center rounded-lg transition-colors",
        disabled
          ? "cursor-not-allowed text-muted-foreground/40"
          : destructive
            ? "cursor-pointer text-rose-500 hover:bg-rose-50 hover:text-rose-700 dark:hover:bg-rose-950/40"
            : "cursor-pointer text-muted-foreground hover:bg-accent hover:text-foreground",
      )}
    >
      <Icon className="h-4 w-4" />
    </motion.button>
  )
}

function Modal({
  title,
  onClose,
  children,
}: {
  title: string
  onClose: () => void
  children: React.ReactNode
}) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, transition: { duration: 0.15 } }}
      className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 p-0 backdrop-blur-sm sm:items-center sm:p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
      data-testid="modal"
    >
      <motion.div
        initial={{ opacity: 0, y: 28, scale: 0.97 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 20, scale: 0.98, transition: { duration: 0.18 } }}
        transition={springSoft}
        className="max-h-[90vh] w-full overflow-y-auto rounded-t-2xl border border-border bg-card p-6 shadow-float sm:max-w-lg sm:rounded-2xl"
      >
        <div className="mb-5 flex items-center justify-between">
          <h2 className="font-serif text-lg font-semibold tracking-tight">{title}</h2>
          <motion.button
            whileHover={{ rotate: 90 }}
            transition={springSnappy}
            onClick={onClose}
            className="cursor-pointer rounded-md p-1 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
            data-testid="modal-close"
            aria-label="Close dialog"
          >
            <X className="h-5 w-5" />
          </motion.button>
        </div>
        {children}
      </motion.div>
    </motion.div>
  )
}

function Field({
  label,
  full,
  children,
}: {
  label: string
  full?: boolean
  children: React.ReactNode
}) {
  return (
    <div className={full ? "" : ""}>
      <label className="mb-1.5 block text-[11px] font-medium uppercase tracking-[0.1em] text-muted-foreground/80">
        {label}
      </label>
      {children}
    </div>
  )
}

function Input({
  value,
  onChange,
  type = "text",
  placeholder,
  testId,
}: {
  value: string
  onChange: (v: string) => void
  type?: string
  placeholder?: string
  testId?: string
}) {
  return (
    <input
      value={value}
      onChange={(e) => onChange(e.target.value)}
      type={type}
      placeholder={placeholder}
      data-testid={testId}
      className="h-10 w-full rounded-lg border border-border bg-background px-3.5 text-sm shadow-card outline-none transition-smooth placeholder:text-muted-foreground/50 focus:border-primary/50 focus:ring-2 focus:ring-primary/15"
    />
  )
}

function TextArea({
  value,
  onChange,
  testId,
}: {
  value: string
  onChange: (v: string) => void
  testId?: string
}) {
  return (
    <textarea
      value={value}
      onChange={(e) => onChange(e.target.value)}
      rows={3}
      data-testid={testId}
      className="w-full rounded-lg border border-border bg-background px-3.5 py-2 text-sm shadow-card outline-none transition-smooth placeholder:text-muted-foreground/50 focus:border-primary/50 focus:ring-2 focus:ring-primary/15"
    />
  )
}
