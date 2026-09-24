import { useState } from "react";
import { X } from "lucide-react";
import { useFilterStore } from "@/store";
import { cn } from "@/lib/utils";

const GENRES = [
  "комедия",
  "драма",
  "фантастика",
  "боевик",
  "триллер",
  "криминал",
  "фэнтези",
  "приключения",
  "мультфильм",
  "семейный",
  "документалки",
  "аниме",
  "стендап",
  "история",
];

export function QuickChips({ onSearch }: { onSearch?: () => void }) {
  const { filters, setFilters } = useFilterStore();
  const chips: { key: string; label: string; active: boolean; toggle: () => void }[] = [
    {
      key: "my",
      label: "Только мои подписки",
      active: filters.onlyMy,
      toggle: () => setFilters({ onlyMy: !filters.onlyMy }),
    },
    {
      key: "movie",
      label: "Фильмы",
      active: filters.type === "movie",
      toggle: () => setFilters({ type: filters.type === "movie" ? "" : "movie" }),
    },
    {
      key: "series",
      label: "Сериалы",
      active: filters.type === "series",
      toggle: () => setFilters({ type: filters.type === "series" ? "" : "series" }),
    },
    {
      key: "free",
      label: "Бесплатно",
      active: filters.free,
      toggle: () => setFilters({ free: !filters.free }),
    },
    {
      key: "4k",
      label: "В 4K",
      active: filters.quality === "4K",
      toggle: () => setFilters({ quality: filters.quality === "4K" ? "any" : "4K" }),
    },
  ];
  return (
    <div className="flex flex-wrap gap-2" role="group" aria-label="Быстрые фильтры">
      {chips.map((c) => (
        <button
          key={c.key}
          onClick={() => {
            c.toggle();
            onSearch?.();
          }}
          aria-pressed={c.active}
          className={cn(
            "rounded-full border px-3 py-1.5 text-sm transition-colors",
            c.active
              ? "border-brand-500 bg-brand-500 text-white"
              : "border-neutral-300 dark:border-neutral-700 hover:border-brand-500",
          )}
        >
          {c.label}
        </button>
      ))}
    </div>
  );
}

export function MoreFiltersPopover() {
  const [open, setOpen] = useState(false);
  const { filters, setFilters, resetFilters } = useFilterStore();
  const [genreQuery, setGenreQuery] = useState("");
  const activeCount =
    (filters.genres.length ? 1 : 0) + (filters.minRating ? 1 : 0) + (filters.year ? 1 : 0);

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className="rounded-full border border-neutral-300 px-3 py-1.5 text-sm dark:border-neutral-700 hover:border-brand-500"
      >
        Ещё фильтры{activeCount ? ` (${activeCount})` : ""}
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute z-20 mt-2 w-72 rounded-2xl border border-neutral-200 bg-white p-4 shadow-xl dark:border-neutral-700 dark:bg-neutral-900 max-sm:fixed max-sm:inset-x-4 max-sm:bottom-4 max-sm:w-auto">
            <div>
              <label className="text-xs font-semibold uppercase text-neutral-500">
                Год (1950–2026)
              </label>
              <input
                type="number"
                min={1950}
                max={2026}
                value={filters.year ?? ""}
                onChange={(e) =>
                  setFilters({ year: e.target.value ? Number(e.target.value) : null })
                }
                placeholder="Например, 1999"
                className="mt-1 w-full rounded-lg border px-2 py-1.5 text-sm dark:bg-neutral-800"
              />
            </div>
            <div className="mt-3">
              <label className="text-xs font-semibold uppercase text-neutral-500">Жанры</label>
              <input
                value={genreQuery}
                onChange={(e) => setGenreQuery(e.target.value)}
                placeholder="Найти жанр…"
                className="mt-1 w-full rounded-lg border px-2 py-1.5 text-sm dark:bg-neutral-800"
                aria-label="Поиск по жанрам"
              />
              <div className="mt-2 max-h-32 space-y-1 overflow-auto">
                {GENRES.filter((g) => g.includes(genreQuery.toLowerCase())).map((g) => (
                  <label key={g} className="flex cursor-pointer items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={filters.genres.includes(g)}
                      onChange={() =>
                        setFilters({
                          genres: filters.genres.includes(g)
                            ? filters.genres.filter((x) => x !== g)
                            : [...filters.genres, g],
                        })
                      }
                    />
                    {g}
                  </label>
                ))}
              </div>
            </div>
            <div className="mt-3">
              <label className="text-xs font-semibold uppercase text-neutral-500">
                Рейтинг от {filters.minRating || 0}
              </label>
              <input
                type="range"
                min={0}
                max={10}
                step={0.5}
                value={filters.minRating}
                onChange={(e) => setFilters({ minRating: Number(e.target.value) })}
                className="w-full"
                aria-label="Минимальный рейтинг"
              />
            </div>
            <div className="mt-3">
              <label className="text-xs font-semibold uppercase text-neutral-500">Качество</label>
              <div className="mt-1 flex gap-1">
                {["any", "SD", "HD", "4K"].map((q) => (
                  <button
                    key={q}
                    onClick={() => setFilters({ quality: q })}
                    aria-pressed={filters.quality === q}
                    className={cn(
                      "rounded-lg border px-2.5 py-1 text-xs",
                      filters.quality === q ? "border-brand-500 bg-brand-500 text-white" : "",
                    )}
                  >
                    {q === "any" ? "Любое" : q}
                  </button>
                ))}
              </div>
            </div>
            <button onClick={resetFilters} className="mt-4 text-sm text-brand-500 hover:underline">
              Сбросить все фильтры
            </button>
          </div>
        </>
      )}
    </div>
  );
}

export function ActiveFilterChips() {
  const { filters, setFilters, resetFilters } = useFilterStore();
  const active: { label: string; clear: () => void }[] = [];
  if (filters.onlyMy)
    active.push({ label: "Мои подписки", clear: () => setFilters({ onlyMy: false }) });
  if (filters.free) active.push({ label: "Бесплатно", clear: () => setFilters({ free: false }) });
  if (filters.type)
    active.push({
      label: filters.type === "movie" ? "Фильмы" : "Сериалы",
      clear: () => setFilters({ type: "" }),
    });
  if (filters.quality !== "any")
    active.push({
      label: `Качество ${filters.quality}`,
      clear: () => setFilters({ quality: "any" }),
    });
  if (filters.year)
    active.push({ label: `Год ${filters.year}`, clear: () => setFilters({ year: null }) });
  if (filters.minRating)
    active.push({ label: `★ от ${filters.minRating}`, clear: () => setFilters({ minRating: 0 }) });
  filters.genres.forEach((g) =>
    active.push({
      label: g,
      clear: () => setFilters({ genres: filters.genres.filter((x) => x !== g) }),
    }),
  );
  if (!active.length) return null;
  return (
    <div className="flex flex-wrap items-center gap-2" aria-label="Активные фильтры">
      {active.map((a, i) => (
        <span
          key={i}
          className="inline-flex items-center gap-1 rounded-full bg-neutral-200 px-2.5 py-1 text-xs dark:bg-neutral-800"
        >
          {a.label}
          <button
            onClick={a.clear}
            aria-label={`Убрать фильтр ${a.label}`}
            className="hover:text-red-500"
          >
            <X size={12} />
          </button>
        </span>
      ))}
      <button onClick={resetFilters} className="text-xs text-brand-500 hover:underline">
        Сбросить
      </button>
    </div>
  );
}
