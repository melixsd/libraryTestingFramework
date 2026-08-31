"use client"

import { cn } from "@/lib/utils"

interface InitialAvatarProps {
  initials: string
  size?: "sm" | "md" | "lg" | "xl"
  className?: string
  // Optional color override; if not supplied we hash the initials
  color?: string
}

const sizeMap = {
  sm: "h-8 w-8 text-xs",
  md: "h-10 w-10 text-sm",
  lg: "h-16 w-16 text-lg",
  xl: "h-28 w-28 text-3xl",
}

// Deterministic warm palette based on initials
const palette = [
  "oklch(0.55 0.12 155)",
  "oklch(0.6 0.13 35)",
  "oklch(0.5 0.1 60)",
  "oklch(0.55 0.13 290)",
  "oklch(0.6 0.12 200)",
  "oklch(0.5 0.13 20)",
  "oklch(0.55 0.11 130)",
]

function pickColor(seed: string) {
  let hash = 0
  for (let i = 0; i < seed.length; i++) {
    hash = (hash * 31 + seed.charCodeAt(i)) >>> 0
  }
  return palette[hash % palette.length]
}

export function InitialAvatar({
  initials,
  size = "md",
  className,
  color,
}: InitialAvatarProps) {
  const bg = color ?? pickColor(initials)
  return (
    <div
      className={cn(
        "flex shrink-0 items-center justify-center rounded-full font-semibold text-white ring-2 ring-background/80 transition-smooth",
        sizeMap[size],
        className,
      )}
      style={{ background: bg }}
      aria-hidden
    >
      {initials}
    </div>
  )
}
