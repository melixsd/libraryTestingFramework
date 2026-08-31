"use client"

import type { Transition, Variants } from "framer-motion"

/* Shared spring vocabulary — soft, human, slightly imperfect. */

export const springSoft: Transition = {
  type: "spring",
  stiffness: 220,
  damping: 28,
  mass: 0.9,
}

export const springGentle: Transition = {
  type: "spring",
  stiffness: 140,
  damping: 24,
}

export const springSnappy: Transition = {
  type: "spring",
  stiffness: 400,
  damping: 32,
}

export const easeOutExpo: [number, number, number, number] = [0.16, 1, 0.3, 1]

export const fadeUp: Variants = {
  hidden: { opacity: 0, y: 16 },
  show: (i: number = 0) => ({
    opacity: 1,
    y: 0,
    transition: { ...springSoft, delay: Math.min(i * 0.06, 0.42) },
  }),
}

export const staggerContainer: Variants = {
  hidden: {},
  show: {
    transition: { staggerChildren: 0.07, delayChildren: 0.05 },
  },
}
