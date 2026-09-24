import { motion } from "framer-motion";
import { Bookmark, BookmarkCheck, Play } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { useWatchlistMutations } from "@/api/hooks";
import { getToken } from "@/api/client";
import { useWatchUIStore } from "@/store";
import type { ContentCardData } from "@/types";
import ProviderBadge from "./ProviderBadge";

const TYPE_LABEL: Record<string, string> = { movie: "Фильм", series: "Сериал", video: "Видео" };

export function pickBestSource(c: ContentCardData) {
  return c.best_source;
}

export default function ContentCard({
  item,
  index = 0,
  providersMeta,
  onHoverPrefetch,
}: {
  item: ContentCardData;
  index?: number;
  providersMeta?: Record<string, { name: string; brand_color: string }>;
  onHoverPrefetch?: (id: string) => void;
}) {
  const navigate = useNavigate();
  const { savedIds, toggleSaved } = useWatchUIStore();
  const { add, removeByContent } = useWatchlistMutations();
  const saved = savedIds.includes(item.id);
  const best = pickBestSource(item);
  const reduceMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

  const toggleList = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!getToken()) {
      toast.info("Войдите, чтобы сохранять в список");
      navigate("/login");
      return;
    }
    toggleSaved(item.id); // optimistic
    if (saved) {
      removeByContent.mutate(item.id, {
        onSuccess: () => toast.success("Убрано из списка"),
        onError: () => {
          toggleSaved(item.id);
          toast.error("Не получилось убрать. Попробуйте ещё раз.");
        },
      });
    } else {
      add.mutate(item.id, {
        onSuccess: () => toast.success("Сохранено в список"),
        onError: () => {
          toggleSaved(item.id);
          toast.error("Не получилось сохранить. Попробуйте ещё раз.");
        },
      });
    }
  };

  return (
    <motion.div
      initial={reduceMotion ? false : { opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: Math.min(index * 0.03, 0.3), duration: 0.25 }}
    >
      <Link
        to={`/content/${item.id}`}
        onMouseEnter={() => onHoverPrefetch?.(item.id)}
        className="group block rounded-xl focus-visible:outline-none"
        aria-label={`${item.title}${item.year ? `, ${item.year}` : ""}`}
      >
        <div className="relative overflow-hidden rounded-xl bg-neutral-200 dark:bg-neutral-800">
          <img
            src={item.poster_url || "/offline.html"}
            alt={`Постер: ${item.title}`}
            loading="lazy"
            className="aspect-[2/3] w-full object-cover transition-transform duration-200 group-hover:scale-[1.03]"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
          <button
            onClick={toggleList}
            aria-label={saved ? "Убрать из списка" : "В список"}
            title={saved ? "Убрать из списка" : "В список"}
            className="absolute right-2 top-2 rounded-full bg-black/60 p-1.5 text-white opacity-0 backdrop-blur transition-opacity group-hover:opacity-100 focus:opacity-100"
          >
            {saved ? <BookmarkCheck size={16} /> : <Bookmark size={16} />}
          </button>
          {best && (
            <div className="absolute bottom-2 left-2 flex items-center gap-1 rounded-full bg-black/70 py-1 pl-1 pr-2 text-[11px] font-medium text-white backdrop-blur">
              <Play size={12} />
              <span className="max-w-[120px] truncate">{best.provider_name}</span>
              {best.price != null && <span>· {Math.round(best.price)} ₽</span>}
              {best.price == null && !best.is_subscription && <span>· бесплатно</span>}
            </div>
          )}
        </div>
        <div className="mt-2 px-0.5">
          <p className="line-clamp-2 text-sm font-semibold leading-tight">{item.title}</p>
          <div className="mt-1 flex items-center gap-1.5 text-xs text-neutral-500 dark:text-neutral-400">
            {item.year && <span>{item.year}</span>}
            <span>{TYPE_LABEL[item.content_type] ?? item.content_type}</span>
            {item.rating_kinopoisk != null && (
              <span className="font-semibold text-amber-600 dark:text-amber-400">
                ★ {item.rating_kinopoisk.toFixed(1)}
              </span>
            )}
          </div>
          {item.providers.length > 0 && (
            <div className="mt-1.5 flex gap-1">
              {item.providers.slice(0, 5).map((pid) => (
                <ProviderBadge
                  key={pid}
                  id={pid}
                  size="sm"
                  name={providersMeta?.[pid]?.name ?? pid}
                  color={providersMeta?.[pid]?.brand_color ?? "#666"}
                />
              ))}
            </div>
          )}
        </div>
      </Link>
    </motion.div>
  );
}
