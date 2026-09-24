import { useEffect, useMemo } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { useVirtualizer } from "@tanstack/react-virtual";
import { useRef } from "react";
import { get } from "@/api/client";
import { usePopular, useProviders, useSearch } from "@/api/hooks";
import ContentCard from "@/components/ContentCard";
import SearchBar from "@/components/SearchBar";
import { ActiveFilterChips, MoreFiltersPopover, QuickChips } from "@/components/SmartFilters";
import { RowSkeleton } from "@/components/Skeletons";
import { useFilterStore } from "@/store";
import type { ContentDetailData } from "@/types";

export default function SearchResults() {
  const [params, setParams] = useSearchParams();
  const q = params.get("q") ?? "";
  const { filters } = useFilterStore();
  const qc = useQueryClient();
  const { data: providers } = useProviders();

  // URL <-> state sync (spec: /?q=матрица&year=1999 shareable)
  useEffect(() => {
    document.title = q ? `«${q}» — StreamHub` : "Поиск — StreamHub";
  }, [q]);

  const { data, isLoading, isFetching, isError, refetch } = useSearch(
    {
      q,
      type: filters.type || undefined,
      year: filters.year,
      onlyMy: filters.onlyMy,
      free: filters.free,
      quality: filters.quality,
      genres: filters.genres,
      minRating: filters.minRating || undefined,
    },
    true,
  );

  const providersMeta = useMemo(() => {
    const m: Record<string, { name: string; brand_color: string }> = {};
    providers?.forEach((p) => (m[p.id] = { name: p.name, brand_color: p.brand_color }));
    return m;
  }, [providers]);

  const items = data?.items ?? [];

  const prefetch = (id: string) => {
    qc.prefetchQuery({
      queryKey: ["content", id],
      queryFn: () => get<ContentDetailData>(`/api/v1/content/${id}`),
      staleTime: 5 * 60_000,
    });
  };

  return (
    <div className="mx-auto max-w-6xl px-4 pb-16">
      <div className="sticky top-[57px] z-20 -mx-4 bg-neutral-50/90 px-4 py-3 backdrop-blur dark:bg-[#0f0f14]/90 max-md:top-[97px]">
        <SearchBar
          key={q}
          initial={q}
          onQueryChange={(next) => {
            if (next !== q) {
              const sp = new URLSearchParams(params);
              if (next) sp.set("q", next);
              else sp.delete("q");
              setParams(sp, { replace: true });
            }
          }}
        />
        <div className="mt-2 flex flex-wrap items-center gap-2">
          <QuickChips />
          <MoreFiltersPopover />
        </div>
        <div className="mt-2">
          <ActiveFilterChips />
        </div>
      </div>

      {data?.partial && (
        <div
          className="mt-4 rounded-xl border border-amber-300 bg-amber-50 p-3 text-sm dark:border-amber-800 dark:bg-amber-950"
          role="status"
        >
          {(data.failed_providers ?? []).map((p) => (
            <span key={p}>
              {providerName(providers, p)} сейчас не отвечает. Мы уже разбираемся. Пока показываем
              результаты из других сервисов.
            </span>
          ))}
        </div>
      )}

      <div className="mt-4">
        {isLoading ? (
          <RowSkeleton count={12} />
        ) : isError ? (
          <div className="rounded-2xl border p-8 text-center">
            <p className="font-semibold">Что-то пошло не так. Мы уже чиним.</p>
            <button
              onClick={() => refetch()}
              className="mt-4 rounded-xl bg-brand-500 px-4 py-2 text-sm font-semibold text-white"
            >
              Попробовать снова
            </button>
          </div>
        ) : items.length === 0 ? (
          <NoResults query={q} suggestions={data?.suggestions ?? []} />
        ) : (
          <>
            <p className="mb-3 text-sm text-neutral-500" role="status">
              Найдено: {items.length}
              {data && data.took_ms > 0 ? ` за ${(data.took_ms / 1000).toFixed(2)} с` : ""}
              {isFetching ? " · обновляем…" : ""}
            </p>
            {items.length > 24 ? (
              <VirtualGrid items={items} providersMeta={providersMeta} prefetch={prefetch} />
            ) : (
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
                {items.map((item, i) => (
                  <ContentCard
                    key={item.id}
                    item={item}
                    index={i}
                    providersMeta={providersMeta}
                    onHoverPrefetch={prefetch}
                  />
                ))}
              </div>
            )}
            {isFetching && (
              <div className="mt-4">
                <RowSkeleton count={6} />
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function providerName(providers: { id: string; name: string }[] | undefined, id: string): string {
  return providers?.find((p) => p.id === id)?.name ?? id;
}

function NoResults({ query, suggestions }: { query: string; suggestions: string[] }) {
  const { data: popular } = usePopular();
  return (
    <div className="rounded-2xl border border-dashed p-8 text-center">
      <p className="text-lg font-semibold">Ничего не нашли по запросу «{query}»</p>
      {suggestions.length > 0 && (
        <p className="mt-2 text-sm text-neutral-500">
          Попробуйте:{" "}
          {suggestions.map((s, i) => (
            <span key={s}>
              <Link
                to={`/search?q=${encodeURIComponent(s)}`}
                className="text-brand-500 hover:underline"
              >
                {s}
              </Link>
              {i < suggestions.length - 1 ? " · " : ""}
            </span>
          ))}
        </p>
      )}
      {popular && popular.length > 0 && (
        <div className="mt-6 text-left">
          <p className="mb-3 text-sm font-semibold">А вот популярное за неделю:</p>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 lg:grid-cols-6">
            {popular.slice(0, 6).map((c, i) => (
              <ContentCard key={c.id} item={c} index={i} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function VirtualGrid({
  items,
  providersMeta,
  prefetch,
}: {
  items: Parameters<typeof ContentCard>[0]["item"][];
  providersMeta: Record<string, { name: string; brand_color: string }>;
  prefetch: (id: string) => void;
}) {
  const parentRef = useRef<HTMLDivElement>(null);
  const cols = 6;
  const rows = Math.ceil(items.length / cols);
  const virtualizer = useVirtualizer({
    count: rows,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 320,
    overscan: 2,
  });
  return (
    <div ref={parentRef} className="max-h-[80vh] overflow-auto">
      <div style={{ height: virtualizer.getTotalSize(), position: "relative" }}>
        {virtualizer.getVirtualItems().map((vi) => (
          <div
            key={vi.key}
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              width: "100%",
              transform: `translateY(${vi.start}px)`,
            }}
            className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6"
          >
            {items.slice(vi.index * cols, vi.index * cols + cols).map((item, i) => (
              <ContentCard
                key={item.id}
                item={item}
                index={i}
                providersMeta={providersMeta}
                onHoverPrefetch={prefetch}
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
