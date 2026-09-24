import { useMemo, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { get } from "@/api/client";
import { useFeed, useProviders } from "@/api/hooks";
import ContentCard from "@/components/ContentCard";
import SearchBar from "@/components/SearchBar";
import { MoreFiltersPopover, QuickChips } from "@/components/SmartFilters";
import { RowSkeleton } from "@/components/Skeletons";
import type { ContentCardData, ContentDetailData } from "@/types";

export default function Home() {
  const { data: feed, isLoading, isError, refetch } = useFeed();
  const { data: providers } = useProviders();
  const qc = useQueryClient();

  const providersMeta = useMemo(() => {
    const m: Record<string, { name: string; brand_color: string }> = {};
    providers?.forEach((p) => (m[p.id] = { name: p.name, brand_color: p.brand_color }));
    return m;
  }, [providers]);

  // frontend dedup across sections (spec §13)
  const sections = useMemo(() => {
    const seen = new Set<string>();
    return (feed?.sections ?? [])
      .map((s) => ({
        ...s,
        items: s.items.filter((i) => (seen.has(i.id) ? false : (seen.add(i.id), true))),
      }))
      .filter((s) => s.items.length > 0);
  }, [feed]);

  const prefetch = (id: string) => {
    qc.prefetchQuery({
      queryKey: ["content", id],
      queryFn: () => get<ContentDetailData>(`/api/v1/content/${id}`),
      staleTime: 5 * 60_000,
    });
  };

  return (
    <div className="mx-auto max-w-6xl px-4 pb-16">
      {/* zero screen */}
      <section className="mx-auto max-w-2xl pt-10 text-center sm:pt-16" aria-label="Поиск">
        <h1 className="text-2xl font-extrabold sm:text-3xl">Что посмотрим сегодня?</h1>
        <div className="mt-4">
          <SearchBar autoFocus />
        </div>
        <div className="mt-3 flex flex-wrap items-center justify-center gap-2">
          <QuickChips />
          <MoreFiltersPopover />
        </div>
      </section>

      <section className="mt-10 space-y-10" aria-label="Лента">
        {isLoading && (
          <>
            <RowSkeleton />
            <RowSkeleton />
          </>
        )}
        {isError && (
          <div className="rounded-2xl border p-8 text-center">
            <p className="font-semibold">Что-то пошло не так</p>
            <p className="mt-1 text-sm text-neutral-500">
              Мы уже чиним. Попробуйте обновить страницу.
            </p>
            <button
              onClick={() => refetch()}
              className="mt-4 rounded-xl bg-brand-500 px-4 py-2 text-sm font-semibold text-white"
            >
              Обновить
            </button>
          </div>
        )}
        {sections.map((s) => (
          <CarouselRow
            key={s.key}
            title={s.title}
            items={s.items}
            providersMeta={providersMeta}
            prefetch={prefetch}
          />
        ))}
      </section>
    </div>
  );
}

function CarouselRow({
  title,
  items,
  providersMeta,
  prefetch,
}: {
  title: string;
  items: ContentCardData[];
  providersMeta: Record<string, { name: string; brand_color: string }>;
  prefetch: (id: string) => void;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const scroll = (dir: number) => ref.current?.scrollBy({ left: dir * 480, behavior: "smooth" });

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
    const cards = ref.current?.querySelectorAll("a");
    if (!cards?.length) return;
    const idx = Array.from(cards).indexOf(document.activeElement as HTMLAnchorElement);
    const next =
      e.key === "ArrowRight" ? Math.min(idx + 1, cards.length - 1) : Math.max(idx - 1, 0);
    (cards[next] as HTMLElement).focus();
    e.preventDefault();
  };

  return (
    <section aria-label={title}>
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-lg font-bold">{title}</h2>
        <div className="flex gap-1">
          <button
            onClick={() => scroll(-1)}
            aria-label="Назад"
            className="rounded-full border p-1.5 hover:bg-neutral-100 dark:hover:bg-neutral-800"
          >
            <ChevronLeft size={16} />
          </button>
          <button
            onClick={() => scroll(1)}
            aria-label="Вперёд"
            className="rounded-full border p-1.5 hover:bg-neutral-100 dark:hover:bg-neutral-800"
          >
            <ChevronRight size={16} />
          </button>
        </div>
      </div>
      <div
        ref={ref}
        onKeyDown={onKeyDown}
        className="no-scrollbar -mx-4 flex gap-4 overflow-x-auto px-4 pb-2"
        role="list"
      >
        {items.map((item, i) => (
          <div key={item.id} className="w-36 shrink-0 sm:w-44" role="listitem">
            <ContentCard
              item={item}
              index={i}
              providersMeta={providersMeta}
              onHoverPrefetch={prefetch}
            />
          </div>
        ))}
      </div>
    </section>
  );
}
