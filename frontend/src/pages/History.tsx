import { Link } from "react-router-dom";
import { toast } from "sonner";
import { useClearHistory, useHistory, useProviders } from "@/api/hooks";
import ContentCard from "@/components/ContentCard";
import { RowSkeleton } from "@/components/Skeletons";
import { useMemo } from "react";

export default function History() {
  const { data: items, isLoading } = useHistory();
  const { data: providers } = useProviders();
  const clear = useClearHistory();

  const providersMeta = useMemo(() => {
    const m: Record<string, { name: string; brand_color: string }> = {};
    providers?.forEach((p) => (m[p.id] = { name: p.name, brand_color: p.brand_color }));
    return m;
  }, [providers]);

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-extrabold">История просмотров</h1>
        {!!items?.length && (
          <button
            onClick={() =>
              clear.mutate(undefined, { onSuccess: () => toast.success("История очищена") })
            }
            className="text-sm text-neutral-500 hover:text-red-500"
          >
            Очистить
          </button>
        )}
      </div>
      {isLoading ? (
        <div className="mt-6">
          <RowSkeleton count={12} />
        </div>
      ) : !items?.length ? (
        <div className="mt-6 rounded-2xl border border-dashed p-8 text-center">
          <p className="text-lg font-semibold">Вы ещё ничего не смотрели через StreamHub</p>
          <Link
            to="/"
            className="mt-4 inline-flex rounded-xl bg-brand-500 px-4 py-2 text-sm font-semibold text-white"
          >
            Найти первый фильм →
          </Link>
        </div>
      ) : (
        <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
          {items.map((h, i) => (
            <ContentCard key={h.id} item={h.content} index={i} providersMeta={providersMeta} />
          ))}
        </div>
      )}
    </div>
  );
}
