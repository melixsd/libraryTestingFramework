export function Footer() {
  return (
    <footer className="mt-auto border-t border-border/60 bg-card/30">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-4 py-8 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-2">
              <span className="font-serif text-lg font-semibold text-foreground">
                Aldenwood Library
              </span>
              <span className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground/70">
                Est. 1894
              </span>
            </div>
            <p className="text-xs text-muted-foreground/80">
              A demonstration library management interface.
            </p>
          </div>
          <div className="flex flex-col gap-1 text-right text-xs text-muted-foreground">
            <span>Catalogue updated daily</span>
            <span className="text-muted-foreground/70">Open Mon–Sat, 9am – 7pm</span>
          </div>
        </div>
        <div className="flex items-center justify-between border-t border-border/40 py-4 text-[11px] text-muted-foreground/60">
          <span>Built with Next.js, Tailwind CSS &amp; shadcn/ui</span>
          <span className="hidden sm:inline">© {new Date().getFullYear()} Aldenwood Library</span>
        </div>
      </div>
    </footer>
  )
}
