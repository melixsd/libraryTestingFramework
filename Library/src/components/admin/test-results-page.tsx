"use client"

import { useEffect } from "react"
import { useLibraryStore } from "@/store/library-store"
import {
  TestTube,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Loader2,
  FlaskConical,
  ExternalLink,
  Clock,
} from "lucide-react"
import { motion } from "framer-motion"
import { cn } from "@/lib/utils"
import { springSoft, springSnappy, fadeUp, staggerContainer } from "@/lib/motion"

export function TestResultsPage() {
  const testResults = useLibraryStore((s) => s.testResults)
  const testResultsStatus = useLibraryStore((s) => s.testResultsStatus)
  const testResultsError = useLibraryStore((s) => s.testResultsError)
  const fetchTestResults = useLibraryStore((s) => s.fetchTestResults)
  const runTests = useLibraryStore((s) => s.runTests)

  useEffect(() => {
    fetchTestResults()
  }, [fetchTestResults])

  async function handleRunTests() {
    try {
      await runTests()
    } catch {
      // error is stored in the store
    }
  }

  const isRunning = testResultsStatus === "loading"

  return (
    <div
      className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8"
      data-testid="test-results-page"
    >
      {/* Header */}
      <motion.section
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={springSoft}
        className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"
      >
        <div className="flex items-center gap-4">
          <motion.div
            whileHover={{ rotate: -3, scale: 1.05 }}
            transition={springSoft}
            className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-card sm:h-14 sm:w-14"
          >
            <TestTube className="h-6 w-6 sm:h-7 sm:w-7" />
          </motion.div>
          <div>
            <h1 className="font-serif text-[1.75rem] font-semibold tracking-tight sm:text-[2rem]">Test Results</h1>
            <p className="mt-0.5 text-sm text-muted-foreground">
              View and trigger the test suite for the Library Management backend.
            </p>
          </div>
        </div>
        <motion.button
          onClick={handleRunTests}
          disabled={isRunning}
          whileHover={{ scale: isRunning ? 1 : 1.03 }}
          whileTap={{ scale: isRunning ? 1 : 0.96 }}
          transition={springSnappy}
          data-testid="btn-run-tests"
          className={cn(
            "inline-flex cursor-pointer items-center justify-center gap-2 rounded-lg px-5 py-2.5 text-sm font-medium shadow-card transition-colors",
            isRunning
              ? "bg-primary/80 text-primary-foreground opacity-70"
              : "bg-primary text-primary-foreground hover:bg-primary/90",
          )}
        >
          {isRunning ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Running…
            </>
          ) : (
            <>
              <FlaskConical className="h-4 w-4" />
              Run Tests
            </>
          )}
        </motion.button>
      </motion.section>

      {/* Error state */}
      {testResultsStatus === "error" && !isRunning && (
        <motion.div
          initial={{ opacity: 0, y: -6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={springSoft}
          className="mb-6 flex items-start gap-3 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 dark:border-rose-900 dark:bg-rose-950/30"
        >
          <XCircle className="mt-0.5 h-4 w-4 shrink-0 text-rose-600 dark:text-rose-400" />
          <div className="flex-1">
            <p className="text-sm font-medium text-rose-800 dark:text-rose-200">
              Failed to load test results
            </p>
            <p className="mt-0.5 text-xs text-rose-600 dark:text-rose-300">{testResultsError ?? "An unexpected error occurred."}</p>
          </div>
          <button
            onClick={() => fetchTestResults()}
            className="shrink-0 cursor-pointer rounded-md p-1 text-rose-600 transition-colors hover:bg-rose-100 dark:text-rose-400 dark:hover:bg-rose-900/40"
            aria-label="Retry"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </motion.div>
      )}

      {/* Loading state (initial fetch) */}
      {testResultsStatus === "loading" && !testResults && (
        <div className="flex flex-col items-center justify-center py-24">
          <Loader2 className="h-10 w-10 animate-spin text-primary" />
          <p className="mt-4 text-sm text-muted-foreground">Fetching test results…</p>
        </div>
      )}

      {/* Empty state (no test run yet) */}
      {testResultsStatus !== "loading" && !testResults && testResultsStatus !== "error" && (
        <motion.div
          variants={fadeUp}
          initial="hidden"
          animate="show"
          custom={2}
          className="flex flex-col items-center rounded-2xl border border-dashed border-border bg-card/40 px-6 py-20 text-center"
        >
          <motion.div
            animate={{ y: [0, -6, 0] }}
            transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
            className="mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-primary/10"
          >
            <TestTube className="h-10 w-10 text-primary/40" />
          </motion.div>
          <h2 className="font-serif text-xl font-semibold">No test results yet</h2>
          <p className="mt-2 max-w-sm text-sm text-muted-foreground">
            The test suite has not been run yet. Click the &quot;Run Tests&quot; button above to
            execute the full test suite and see results here.
          </p>
        </motion.div>
      )}

      {/* Running overlay */}
      {isRunning && testResults && (
        <motion.div
          initial={{ opacity: 0, y: -4 }}
          animate={{ opacity: 1, y: 0 }}
          transition={springSoft}
          className="mb-6 flex items-center gap-3 rounded-xl border border-primary/30 bg-primary/5 px-4 py-3"
        >
          <Loader2 className="h-4 w-4 animate-spin text-primary" />
          <p className="text-sm font-medium text-primary">Test suite is running…</p>
        </motion.div>
      )}

      {/* Results display */}
      {testResults && (
        <>
          {/* Last run info */}
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ...springSoft, delay: 0.05 }}
            className="mb-6 flex flex-wrap items-center gap-2 text-sm text-muted-foreground"
          >
            <Clock className="h-4 w-4" />
            <span>
              Last run:{" "}
              {testResults.last_run
                ? new Date(testResults.last_run * 1000).toLocaleString()
                : "Never"}
            </span>
            <span className="text-border">|</span>
            <span>{testResults.duration.toFixed(1)}s duration</span>
          </motion.div>

          {/* Stat cards */}
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate="show"
            className="grid grid-cols-2 gap-4 sm:grid-cols-4"
          >
            <StatCard
              testId="test-stat-passed"
              label="Passed"
              value={testResults.passed}
              total={testResults.total}
              color="emerald"
              icon={CheckCircle2}
            />
            <StatCard
              testId="test-stat-failed"
              label="Failed"
              value={testResults.failed}
              total={testResults.total}
              color="rose"
              icon={XCircle}
            />
            <StatCard
              testId="test-stat-skipped"
              label="Skipped"
              value={testResults.skipped}
              total={testResults.total}
              color="amber"
              icon={AlertTriangle}
            />
            <StatCard
              testId="test-stat-total"
              label="Total"
              value={testResults.total}
              total={testResults.total}
              color="primary"
              icon={TestTube}
            />
          </motion.div>

          {/* Coverage bar */}
          {testResults.coverage_percent !== null && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ ...springSoft, delay: 0.15 }}
              className="mt-6 rounded-xl border border-border bg-card p-6 shadow-card"
            >
              <div className="mb-3 flex items-center justify-between">
                <h3 className="font-serif text-base font-semibold tracking-tight">Test Coverage</h3>
                <span className="font-serif text-2xl font-semibold text-primary">
                  {testResults.coverage_percent.toFixed(1)}%
                </span>
              </div>
              <div
                className="h-3 w-full overflow-hidden rounded-full bg-muted"
                data-testid="test-coverage-bar"
              >
                <motion.div
                  className={cn(
                    "h-full rounded-full",
                    testResults.coverage_percent >= 80
                      ? "bg-emerald-500"
                      : testResults.coverage_percent >= 60
                        ? "bg-amber-500"
                        : "bg-rose-500",
                  )}
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.min(testResults.coverage_percent, 100)}%` }}
                  transition={{ duration: 0.9, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
                />
              </div>
            </motion.div>
          )}

          {/* Report link */}
          {testResults.report_path && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ ...springSoft, delay: 0.25 }}
              className="mt-6"
            >
              <motion.a
                href={`http://localhost:8000${testResults.report_path}`}
                target="_blank"
                rel="noopener noreferrer"
                whileHover={{ y: -2 }}
                whileTap={{ scale: 0.98 }}
                transition={springSnappy}
                className="inline-flex cursor-pointer items-center gap-2 rounded-xl border border-border bg-card px-5 py-3 text-sm font-medium shadow-card transition-colors hover:border-primary/30 hover:bg-accent"
              >
                <ExternalLink className="h-4 w-4" />
                View full HTML report
              </motion.a>
            </motion.div>
          )}
        </>
      )}
    </div>
  )
}

function StatCard({
  testId,
  label,
  value,
  total,
  color,
  icon: Icon,
}: {
  testId: string
  label: string
  value: number
  total: number
  color: "emerald" | "rose" | "amber" | "primary"
  icon: React.ComponentType<{ className?: string }>
}) {
  const colorClasses = {
    emerald: {
      border: "border-emerald-200 dark:border-emerald-900",
      icon: "text-emerald-600 dark:text-emerald-400",
      value: "text-emerald-700 dark:text-emerald-300",
    },
    rose: {
      border: "border-rose-200 dark:border-rose-900",
      icon: "text-rose-600 dark:text-rose-400",
      value: "text-rose-700 dark:text-rose-300",
    },
    amber: {
      border: "border-amber-200 dark:border-amber-900",
      icon: "text-amber-600 dark:text-amber-400",
      value: "text-amber-700 dark:text-amber-300",
    },
    primary: {
      border: "border-primary/30",
      icon: "text-primary",
      value: "text-primary",
    },
  }
  const cls = colorClasses[color]

  return (
    <motion.div
      variants={{
        hidden: { opacity: 0, y: 14 },
        show: { opacity: 1, y: 0, transition: springSoft },
      }}
      className={cn("rounded-xl border bg-card p-4 shadow-card", cls.border)}
      data-testid={testId}
    >
      <div className="mb-2.5 flex items-center justify-between">
        <span className="text-[11px] font-medium uppercase tracking-[0.15em] text-muted-foreground/80">
          {label}
        </span>
        <Icon className={cn("h-4 w-4", cls.icon)} />
      </div>
      <p className={cn("font-serif text-[2rem] font-semibold leading-none tracking-tight", cls.value)}>{value}</p>
      {total > 0 && (
        <p className="mt-1 text-xs text-muted-foreground/80">
          {((value / total) * 100).toFixed(1)}% of total
        </p>
      )}
    </motion.div>
  )
}
