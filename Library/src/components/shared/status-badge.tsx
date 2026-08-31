"use client"

import { cn } from "@/lib/utils"
import { CheckCircle2, XCircle } from "lucide-react"

/** Badge showing member active/inactive status */
export function MemberStatusBadge({
  isActive,
  className,
}: {
  isActive: boolean
  className?: string
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium",
        isActive
          ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300 border-emerald-200 dark:border-emerald-900"
          : "bg-rose-100 text-rose-800 dark:bg-rose-950/40 dark:text-rose-300 border-rose-200 dark:border-rose-900",
        className,
      )}
      data-testid={isActive ? "status-active" : "status-inactive"}
    >
      {isActive ? (
        <CheckCircle2 className="h-3 w-3" />
      ) : (
        <XCircle className="h-3 w-3" />
      )}
      {isActive ? "Active" : "Inactive"}
    </span>
  )
}

/** Badge showing membership tier name */
export function MembershipTierBadge({
  tierName,
  className,
}: {
  tierName: string
  className?: string
}) {
  const isPremium = tierName.toLowerCase() === "premium"
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium",
        isPremium
          ? "bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300 border-amber-200 dark:border-amber-900"
          : "bg-secondary text-secondary-foreground border-border",
        className,
      )}
      data-testid="membership-tier"
    >
      {tierName}
    </span>
  )
}
