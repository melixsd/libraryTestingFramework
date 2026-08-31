"use client"

import { useEffect } from "react"
import { useLibraryStore } from "@/store/library-store"
import { Header } from "@/components/layout/header"
import { Footer } from "@/components/layout/footer"
import { HomePage } from "@/components/home/home-page"
import { BookDetailPage } from "@/components/book/book-detail-page"
import { MemberProfilePage } from "@/components/member/member-profile-page"
import { AuthorProfilePage } from "@/components/author/author-profile-page"
import { AdminProfilePage } from "@/components/admin/admin-profile-page"
import { TestResultsPage } from "@/components/admin/test-results-page"
import { LoginPage } from "@/components/auth/login-page"
import { AnimatePresence, motion } from "framer-motion"
import { springSoft } from "@/lib/motion"

export default function Home() {
  const currentView = useLibraryStore((s) => s.currentView)
  const token = useLibraryStore((s) => s.token)
  const currentUser = useLibraryStore((s) => s.currentUser)
  const fetchCurrentUser = useLibraryStore((s) => s.fetchCurrentUser)
  const fetchBooks = useLibraryStore((s) => s.fetchBooks)
  const fetchAuthors = useLibraryStore((s) => s.fetchAuthors)
  const fetchMemberSummary = useLibraryStore((s) => s.fetchMemberSummary)
  const isAdmin = useLibraryStore((s) => s.isAdmin)
  const logout = useLibraryStore((s) => s.logout)

  // On mount, if token exists but no user, try to restore session
  useEffect(() => {
    if (token && !currentUser) {
      fetchCurrentUser().then(() => {
        // After restoring user, fetch data
      })
    }
  }, [token, currentUser, fetchCurrentUser])

  // Fetch core data once we have a user
  useEffect(() => {
    if (currentUser) {
      fetchBooks()
      fetchAuthors()
      if (currentUser.member_id) {
        fetchMemberSummary()
      }
    }
  }, [currentUser, fetchBooks, fetchAuthors, fetchMemberSummary])

  // If not logged in, show login page
  if (!token || !currentUser) {
    return (
      <div className="flex min-h-screen flex-col bg-background paper-texture">
        <Header />
        <main className="flex-1">
          <AnimatePresence mode="wait">
            <motion.div
              key="login"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8, transition: { duration: 0.15 } }}
              transition={springSoft}
            >
              <LoginPage />
            </motion.div>
          </AnimatePresence>
        </main>
        <Footer />
      </div>
    )
  }

  // Gate admin view to admin/librarian roles
  const canViewAdmin = isAdmin()
  const effectiveView = currentView === "login" ? "home" : currentView

  return (
    <div className="flex min-h-screen flex-col bg-background paper-texture">
      <Header />
      <main className="flex-1">
        <AnimatePresence mode="wait">
          <motion.div
            key={effectiveView}
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10, transition: { duration: 0.16 } }}
            transition={springSoft}
          >
            {effectiveView === "home" && <HomePage />}
            {effectiveView === "book-detail" && <BookDetailPage />}
            {effectiveView === "member-profile" && currentUser.member_id && (
              <MemberProfilePage />
            )}
            {effectiveView === "author-profile" && <AuthorProfilePage />}
            {effectiveView === "admin" && canViewAdmin && <AdminProfilePage />}
            {effectiveView === "test-results" && canViewAdmin && <TestResultsPage />}
          </motion.div>
        </AnimatePresence>
      </main>
      <Footer />
    </div>
  )
}
