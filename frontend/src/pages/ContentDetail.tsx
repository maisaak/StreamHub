import { motion } from "framer-motion";
import { Bookmark, BookmarkCheck, Check, ChevronDown, Play, Share2 } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { QRCodeSVG } from "qrcode.react";
import { toast } from "sonner";
import { getToken } from "@/api/client";
import {
  useContent,
  useMarkWatched,
  useProviders,
  useShare,
  useSimilar,
  useTrackWatch,
  useWatchlistMutations,
} from "@/api/hooks";
import AvailabilityList from "@/components/AvailabilityList";
import ContentCard from "@/components/ContentCard";
import { DetailSkeleton, RowSkeleton } from "@/components/Skeletons";
import { resolveWatchUrl, tryOpen } from "@/lib/deepLinks";
import { shareContent } from "@/lib/shortLinks";
import { cn } from "@/lib/utils";
import { useWatchUIStore } from "@/store";
import type { Source } from "@/types";

const TYPE_LABEL: Record<string, string> = { movie: "Фильм", series: "Сериал", video: "Видео" };

export function chooseBestSource(sources: Source[]): Source | null {
  return sources.length ? sources[0] : null; // backend already ranked
}

export default function ContentDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: item, isLoading, isError, refetch } = useContent(id);
  const { data: similar } = useSimilar(id);
  const { data: providers } = useProviders();
  const { savedIds, toggleSaved } = useWatchUIStore();
  const { add, removeByContent } = useWatchlistMutations();
  const markWatched = useMarkWatched();
  const track = useTrackWatch();
  const share = useShare();
  const [sourcesOpen, setSourcesOpen] = useState(true);
  const [watched, setWatched] = useState(false);

  useEffect(() => {
    if (item) document.title = `${item.title} — StreamHub`;
  }, [item]);

  if (isLoading)
    return (
      <div className="mx-auto max-w-6xl px-4 py-8">
        <DetailSkeleton />
      </div>
    );
  if (isError || !item) {
    return (
      <div className="mx-auto max-w-lg px-4 py-16 text-center">
        <p className="text-lg font-bold">Контент не найден</p>
        <p className="mt-1 text-sm text-neutral-500">
          Возможно, он был удалён. Загляните в популярное.
        </p>
        <div className="mt-4 flex justify-center gap-2">
          <button
            onClick={() => refetch()}
            className="rounded-xl bg-brand-500 px-4 py-2 text-sm font-semibold text-white"
          >
            Повторить
          </button>
          <Link to="/" className="rounded-xl border px-4 py-2 text-sm font-semibold">
            На главную
          </Link>
        </div>
      </div>
    );
  }

  const best = chooseBestSource(item.sources);
  const saved = savedIds.includes(item.id);

  const watch = (s: Source) => {
    const url = resolveWatchUrl({ deepLink: s.deep_link, webUrl: s.external_url });
    if (!tryOpen(url)) {
      toast.error(`Не удалось открыть ${s.provider_name}. Попробуйте другой источник ниже.`);
      setSourcesOpen(true);
      return;
    }
    if (getToken()) {
      track.mutate(
        { id: item.id, provider_id: s.provider_id },
        { onSuccess: () => toast.success("Добавлено в историю просмотров") },
      );
    }
  };

  const toggleList = () => {
    if (!getToken()) {
      toast.info("Войдите, чтобы сохранять в список");
      navigate("/login");
      return;
    }
    toggleSaved(item.id);
    (saved ? removeByContent.mutate : add.mutate)(item.id, {
      onSuccess: () => toast.success(saved ? "Убрано из списка" : "Сохранено в список"),
      onError: () => {
        toggleSaved(item.id);
        toast.error("Не получилось. Попробуйте ещё раз.");
      },
    });
  };

  const doShare = async () => {
    try {
      const { short_link } = await share.mutateAsync(item.id);
      const res = await shareContent({
        title: item.title,
        text: `Смотрим «${item.title}» в StreamHub`,
        url: short_link,
      });
      toast.success(res === "copied" ? "Ссылка скопирована" : "Отправлено");
    } catch {
      toast.error("Не получилось поделиться");
    }
  };

  const doWatched = () => {
    if (!getToken()) {
      toast.info("Войдите, чтобы отмечать просмотренное");
      navigate("/login");
      return;
    }
    setWatched(true); // optimistic
    markWatched.mutate(
      { id: item.id, watched: true },
      {
        onSuccess: () => toast.success("Отмечено как просмотренное"),
        onError: () => {
          setWatched(false);
          toast.error("Не получилось сохранить");
        },
      },
    );
  };

  const providersMeta = Object.fromEntries(
    (providers ?? []).map((p) => [p.id, { name: p.name, brand_color: p.brand_color }]),
  );

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="mx-auto max-w-6xl px-4 pb-24 pt-6 md:pb-16"
    >
      <div className="grid gap-6 md:grid-cols-[240px_1fr]">
        <motion.img
          layoutId={item.id}
          src={item.poster_url}
          alt={`Постер: ${item.title}`}
          className="aspect-[2/3] w-40 rounded-xl object-cover shadow-lg md:w-full"
        />
        <div>
          <p className="text-xs uppercase tracking-wide text-neutral-500">
            {TYPE_LABEL[item.content_type] ?? item.content_type}
          </p>
          <h1 className="mt-1 text-2xl font-extrabold sm:text-3xl">{item.title}</h1>
          {(item.original_title || item.year) && (
            <p className="mt-1 text-neutral-500">
              {[item.original_title, item.year].filter(Boolean).join(" · ")}
            </p>
          )}
          <div className="mt-2 flex flex-wrap items-center gap-2 text-sm">
            {item.rating_kinopoisk != null && (
              <span className="rounded-lg bg-amber-100 px-2 py-0.5 font-bold text-amber-700 dark:bg-amber-950 dark:text-amber-300">
                КП {item.rating_kinopoisk.toFixed(1)}
              </span>
            )}
            {item.rating_imdb != null && (
              <span className="rounded-lg bg-neutral-200 px-2 py-0.5 font-bold dark:bg-neutral-800">
                IMDb {item.rating_imdb.toFixed(1)}
              </span>
            )}
            {item.runtime_minutes != null && (
              <span className="text-neutral-500">{item.runtime_minutes} мин</span>
            )}
            {item.genres.map((g) => (
              <Link
                key={g}
                to={`/search?q=&genres=${encodeURIComponent(g)}`}
                className="rounded-full border px-2.5 py-0.5 text-xs hover:border-brand-500"
              >
                {g}
              </Link>
            ))}
          </div>
          {item.description && (
            <p className="mt-3 max-w-2xl text-sm leading-relaxed text-neutral-600 dark:text-neutral-300">
              {item.description}
            </p>
          )}

          {/* Main CTA */}
          <div className="mt-5 flex flex-wrap items-center gap-2">
            {best ? (
              <div className="flex">
                <button
                  onClick={() => watch(best)}
                  className="flex items-center gap-2 rounded-l-xl bg-brand-500 px-6 py-3 font-bold text-white hover:bg-brand-600"
                >
                  <Play size={18} /> Смотреть · {best.provider_name}
                </button>
                <button
                  onClick={() => setSourcesOpen((o) => !o)}
                  aria-expanded={sourcesOpen}
                  aria-label="Выбрать другой источник"
                  className="rounded-r-xl border-l border-white/30 bg-brand-500 px-3 text-white hover:bg-brand-600"
                >
                  <ChevronDown
                    size={18}
                    className={cn("transition-transform", sourcesOpen && "rotate-180")}
                  />
                </button>
              </div>
            ) : (
              <p className="text-sm text-neutral-500">Источники скоро появятся.</p>
            )}
            <div className="flex gap-1" data-testid="detail-actions">
              <IconBtn label={saved ? "Убрать из списка" : "В список"} onClick={toggleList}>
                {saved ? <BookmarkCheck size={18} /> : <Bookmark size={18} />}
              </IconBtn>
              <IconBtn label="Поделиться" onClick={doShare}>
                <Share2 size={18} />
              </IconBtn>
              <IconBtn label="Уже смотрел" onClick={doWatched} active={watched}>
                <Check size={18} />
              </IconBtn>
            </div>
          </div>
          {best && !best.connected && best.is_subscription && (
            <p className="mt-2 text-xs text-neutral-500">Нужна подписка на {best.provider_name}</p>
          )}
        </div>
      </div>

      {/* Sources */}
      <section className="mt-8" aria-label="Где смотреть">
        <button
          onClick={() => setSourcesOpen((o) => !o)}
          className="mb-3 flex items-center gap-2 text-lg font-bold"
          aria-expanded={sourcesOpen}
        >
          Где смотреть
          <ChevronDown
            size={18}
            className={cn("transition-transform", sourcesOpen && "rotate-180")}
          />
        </button>
        {sourcesOpen && (
          <AvailabilityList contentId={item.id} contentTitle={item.title} sources={item.sources} />
        )}
      </section>

      {/* Share + QR */}
      <section
        className="mt-8 flex flex-wrap items-center gap-4 rounded-2xl border p-4"
        aria-label="Поделиться"
      >
        <div className="rounded-xl bg-white p-2">
          <QRCodeSVG
            value={item.short_link || window.location.href}
            size={96}
            aria-label="QR-код для открытия на телефоне"
          />
        </div>
        <div className="text-sm">
          <p className="font-semibold">Смотреть на телефоне</p>
          <p className="text-neutral-500">Наведите камеру — откроется приложение провайдера.</p>
          <p className="mt-1 font-mono text-xs text-brand-500">{item.short_link}</p>
        </div>
      </section>

      {/* Similar */}
      <section className="mt-10" aria-label="Похожие">
        <h2 className="mb-3 text-lg font-bold">Похожие</h2>
        {!similar ? (
          <RowSkeleton count={6} />
        ) : (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
            {similar.items.map((c, i) => (
              <ContentCard key={c.id} item={c} index={i} providersMeta={providersMeta} />
            ))}
          </div>
        )}
      </section>

      {/* Sticky mobile CTA */}
      {best && (
        <div className="fixed inset-x-0 bottom-0 z-30 border-t bg-white/95 p-3 backdrop-blur md:hidden dark:bg-[#0f0f14]/95">
          <button
            onClick={() => watch(best)}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-brand-500 py-3 font-bold text-white"
          >
            <Play size={18} /> Смотреть · {best.provider_name}
          </button>
        </div>
      )}
    </motion.div>
  );
}

function IconBtn({
  label,
  onClick,
  children,
  active,
}: {
  label: string;
  onClick: () => void;
  children: React.ReactNode;
  active?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      title={label}
      aria-label={label}
      aria-pressed={!!active}
      className={cn(
        "rounded-xl border p-2.5 hover:border-brand-500",
        active && "border-brand-500 bg-brand-500/10 text-brand-500",
      )}
    >
      {children}
    </button>
  );
}
