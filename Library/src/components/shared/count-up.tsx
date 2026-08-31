"use client"

import { useEffect } from "react"
import {
  motion,
  useReducedMotion,
  useSpring,
  useTransform,
} from "framer-motion"

/** Gently counts a number up/down whenever it changes. */
export function CountUp({ value }: { value: number }) {
  const reduced = useReducedMotion()
  const spring = useSpring(0, { stiffness: 55, damping: 18 })
  const text = useTransform(spring, (v) => Math.round(v).toLocaleString("en-US"))

  useEffect(() => {
    if (reduced) {
      spring.jump(value)
    } else {
      spring.set(value)
    }
  }, [reduced, spring, value])

  return <motion.span>{text}</motion.span>
}
