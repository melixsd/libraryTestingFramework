import type { Metadata } from "next";
import { Geist, Geist_Mono, Newsreader } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const newsreader = Newsreader({
  variable: "--font-serif",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  style: ["normal", "italic"],
});

export const metadata: Metadata = {
  title: "Aldenwood Library — Catalogue & Membership",
  description:
    "Browse the Aldenwood Library catalogue, manage your membership, follow your favourite authors, and discover your next read.",
  keywords: ["library", "catalogue", "books", "membership", "Aldenwood"],
  authors: [{ name: "Aldenwood Library" }],
  openGraph: {
    title: "Aldenwood Library",
    description: "Browse, borrow, and discover — your neighbourhood library, online.",
    siteName: "Aldenwood Library",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} ${newsreader.variable} antialiased bg-background text-foreground`}
      >
        {children}
        <Toaster />
      </body>
    </html>
  );
}
