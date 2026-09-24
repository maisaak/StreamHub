import { useState } from "react";
import { toast } from "sonner";
import { useTrackWatch } from "@/api/hooks";
import { getToken } from "@/api/client";
import { resolveWatchUrl, tryOpen } from "@/lib/deepLinks";
import { accessLabel, cn, formatPrice } from "@/lib/utils";
import type { Source } from "@/types";
import ProviderBadge from "./ProviderBadge";

export default function AvailabilityList({
  contentId,
  contentTitle,
  sources,
  onWatch,
}: {
  contentId: string;
  contentTitle: string;
  sources: Source[];
  onWatch?: (s: Source) => void;
}) {
  const [confirm, setConfirm] = useState<Source | null>(null);
  const [failed, setFailed] = useState<Source | null>(null);
  const track = useTrackWatch();

  const openSource = (s: Source) => {
    if (!s.connected && s.is_subscription) {
      setConfirm(s);
      return;
    }
    launch(s);
  };

  const launch = (s: Source) => {
    setConfirm(null);
    const url = resolveWatchUrl({ deepLink: s.deep_link, webUrl: s.external_url });
    const ok = tryOpen(url);
    if (!ok) {
      setFailed(s);
      return;
    }
    onWatch?.(s);
    if (getToken()) {
      track.mutate(
        { id: contentId, provider_id: s.provider_id },
        {
          onSuccess: () => toast.success("Добавлено в историю просмотров"),
          onError: () => {},
        },
      );
    }
  };

  if (sources.length === 0) {
    return (
      <p className="text-sm text-neutral-500">
        Пока нет доступных источников. Попробуйте позже — мы уже ищем.
      </p>
    );
  }

  return (
    <div>
      <div className="overflow-hidden rounded-xl border border-neutral-200 dark:border-neutral-700">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-neutral-100 text-left text-xs uppercase tracking-wide text-neutral-500 dark:bg-neutral-800">
              <th className="px-3 py-2">Сервис</th>
              <th className="px-3 py-2">Доступ</th>
              <th className="px-3 py-2 hidden sm:table-cell">Качество</th>
              <th className="px-3 py-2 hidden sm:table-cell">Цена</th>
              <th className="px-3 py-2 text-right">Действие</th>
            </tr>
          </thead>
          <tbody>
            {sources.map((s) => {
              const dimmed = !s.connected && s.is_subscription;
              return (
                <tr
                  key={s.provider_id}
                  className="border-t border-neutral-200 dark:border-neutral-700"
                >
                  <td className="px-3 py-2">
                    <span className={cn("flex items-center gap-2", dimmed && "opacity-50")}>
                      <ProviderBadge
                        id={s.provider_id}
                        name={s.provider_name}
                        color={s.brand_color}
                        dimmed={dimmed}
                      />
                      <span className="font-medium">{s.provider_name}</span>
                    </span>
                  </td>
                  <td className="px-3 py-2">
                    <span className="inline-flex items-center gap-1">
                      {s.is_subscription ? "✅" : s.price != null ? "💳" : "🆓"}
                      {accessLabel(s)}
                    </span>
                    {dimmed && (
                      <span className="ml-1 text-xs text-neutral-400">(нужна подписка)</span>
                    )}
                  </td>
                  <td className="px-3 py-2 hidden sm:table-cell">{s.quality}</td>
                  <td className="px-3 py-2 hidden sm:table-cell">{formatPrice(s.price) || "—"}</td>
                  <td className="px-3 py-2 text-right">
                    <button
                      onClick={() => openSource(s)}
                      className="rounded-lg bg-brand-500 px-3 py-1.5 text-xs font-semibold text-white hover:bg-brand-600"
                    >
                      Смотреть
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {confirm && (
        <Modal title={`Нет подписки на ${confirm.provider_name}`} onClose={() => setConfirm(null)}>
          <p className="text-sm text-neutral-500">
            «{contentTitle}» доступен в {confirm.provider_name} по подписке. Открыть сайт сервиса?
          </p>
          <div className="mt-4 flex justify-end gap-2">
            <button
              onClick={() => setConfirm(null)}
              className="rounded-xl border px-4 py-2 text-sm"
            >
              Отмена
            </button>
            <button
              onClick={() => launch(confirm)}
              className="rounded-xl bg-brand-500 px-4 py-2 text-sm font-semibold text-white"
            >
              Открыть
            </button>
          </div>
        </Modal>
      )}

      {failed && (
        <Modal title={`Не удалось открыть ${failed.provider_name}`} onClose={() => setFailed(null)}>
          <p className="text-sm text-neutral-500">
            Попробуйте другой источник — остальные {sources.length - 1} доступны ниже.
          </p>
          <div className="mt-3 space-y-2">
            {sources
              .filter((s) => s.provider_id !== failed.provider_id)
              .slice(0, 4)
              .map((s) => (
                <button
                  key={s.provider_id}
                  onClick={() => {
                    setFailed(null);
                    launch(s);
                  }}
                  className="flex w-full items-center gap-2 rounded-xl border px-3 py-2 text-sm hover:bg-neutral-50 dark:hover:bg-neutral-800"
                >
                  <ProviderBadge
                    id={s.provider_id}
                    name={s.provider_name}
                    color={s.brand_color}
                    size="sm"
                  />
                  {s.provider_name} · {accessLabel(s)}
                </button>
              ))}
          </div>
        </Modal>
      )}
    </div>
  );
}

export function Modal({
  title,
  children,
  onClose,
}: {
  title: string;
  children: React.ReactNode;
  onClose: () => void;
}) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label={title}
    >
      <div
        className="w-full max-w-md rounded-2xl bg-white p-5 shadow-2xl dark:bg-neutral-900"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-base font-bold">{title}</h2>
        <div className="mt-2">{children}</div>
      </div>
    </div>
  );
}
