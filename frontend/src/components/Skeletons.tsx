export function CardSkeleton() {
  return (
    <div className="animate-pulse" aria-hidden>
      <div className="aspect-[2/3] rounded-xl bg-neutral-200 dark:bg-neutral-800" />
      <div className="mt-2 h-4 w-3/4 rounded bg-neutral-200 dark:bg-neutral-800" />
      <div className="mt-1 h-3 w-1/2 rounded bg-neutral-200 dark:bg-neutral-800" />
    </div>
  );
}

export function RowSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div
      className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4"
      aria-label="Загрузка"
    >
      {Array.from({ length: count }).map((_, i) => (
        <CardSkeleton key={i} />
      ))}
    </div>
  );
}

export function DetailSkeleton() {
  return (
    <div className="animate-pulse grid gap-6 md:grid-cols-[240px_1fr]" aria-label="Загрузка">
      <div className="aspect-[2/3] rounded-xl bg-neutral-200 dark:bg-neutral-800" />
      <div>
        <div className="h-8 w-2/3 rounded bg-neutral-200 dark:bg-neutral-800" />
        <div className="mt-3 h-4 w-1/3 rounded bg-neutral-200 dark:bg-neutral-800" />
        <div className="mt-6 h-12 w-64 rounded-xl bg-neutral-200 dark:bg-neutral-800" />
        <div className="mt-6 space-y-2">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-14 rounded-xl bg-neutral-200 dark:bg-neutral-800" />
          ))}
        </div>
      </div>
    </div>
  );
}
