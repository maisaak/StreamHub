import { Link } from "react-router-dom";
import { usePopular, useProviders, useWatchlist } from "@/api/hooks";
import ContentCard from "@/components/ContentCard";
import { RowSkeleton } from "@/components/Skeletons";
import { useMemo } from "react";

export default function Watchlist() {
  const { data: items, isLoading } = useWatchlist();
  const { data: providers } = useProviders();
  const { data: popular } = usePopular();

  const providersMeta = useMemo(() => {
    const m: Record<string, { name: string; brand_color: string }> = {};
    providers?.forEach((p) => (m[p.id] = { name: p.name, brand_color: p.brand_color }));
    return m;
  }, [providers]);

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <h1 className="text-2xl font-extrabold">Мой список</h1>
      {isLoading ? (
        <div className="mt-6">
          <RowSkeleton count={12} />
        </div>
      ) : !items?.length ? (
        <div className="mt-6 rounded-2xl border border-dashed p-8 text-center">
          <p className="text-lg font-semibold">Вы пока ничего не отложили</p>
          <p className="mt-1 text-sm text-neutral-500">
            Вот фильмы из ваших подписок — может, что-то заинтересует?
          </p>
          <div className="mt-6 grid grid-cols-2 gap-4 text-left sm:grid-cols-4 lg:grid-cols-6">
            {popular?.slice(0, 6).map((c, i) => (
              <ContentCard key={c.id} item={c} index={i} providersMeta={providersMeta} />
            ))}
          </div>
        </div>
      ) : (
        <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
          {items.map((w, i) => (
            <ContentCard key={w.id} item={w.content} index={i} providersMeta={providersMeta} />
          ))}
        </div>
      )}
      <p className="mt-6 text-sm text-neutral-500">
        <Link to="/" className="text-brand-500 hover:underline">
          ← На главную
        </Link>
      </p>
    </div>
  );
}
