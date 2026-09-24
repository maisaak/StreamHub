import { toast } from "sonner";
import { del } from "@/api/client";
import { usePatchPreferences, usePreferences } from "@/api/hooks";
import { applyTheme, useThemeStore } from "@/store";

export default function Settings() {
  const { data: prefs, isLoading } = usePreferences();
  const patch = usePatchPreferences();
  const { theme, setTheme } = useThemeStore();

  const save = (data: Parameters<typeof patch.mutate>[0]) => {
    patch.mutate(data, {
      onSuccess: () => toast.success("Настройки сохранены"),
      onError: () => toast.error("Не получилось сохранить"),
    });
  };

  const setThemeAndSave = (t: "auto" | "light" | "dark") => {
    setTheme(t);
    applyTheme(t);
  };

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <h1 className="text-2xl font-extrabold">Настройки</h1>
      {isLoading ? (
        <p className="mt-4 text-sm text-neutral-500">Загружаем…</p>
      ) : (
        prefs && (
          <div className="mt-6 space-y-4">
            <Toggle
              label="Только мои подписки по умолчанию"
              hint="Фильтр применяется к ленте и поиску"
              value={prefs.only_my_subscriptions}
              onChange={(v) => save({ only_my_subscriptions: v })}
            />
            <Toggle
              label="Прятать просмотренное"
              hint="Карточки «Уже смотрел» уйдут из лент"
              value={prefs.hide_watched}
              onChange={(v) => save({ hide_watched: v })}
            />
            <Toggle
              label="Автовоспроизведение следующего"
              value={prefs.auto_play_next}
              onChange={(v) => save({ auto_play_next: v })}
            />
            <div className="rounded-2xl border p-4">
              <p className="font-semibold">Качество по умолчанию</p>
              <div className="mt-2 flex gap-2">
                {["any", "HD", "4K"].map((q) => (
                  <button
                    key={q}
                    onClick={() => save({ preferred_quality: q })}
                    aria-pressed={prefs.preferred_quality === q}
                    className={`rounded-xl border px-4 py-1.5 text-sm ${
                      prefs.preferred_quality === q
                        ? "border-brand-500 bg-brand-500 text-white"
                        : ""
                    }`}
                  >
                    {q === "any" ? "Любое" : q}
                  </button>
                ))}
              </div>
            </div>
            <div className="rounded-2xl border p-4">
              <p className="font-semibold">Тема оформления</p>
              <div className="mt-2 flex gap-2">
                {(["auto", "light", "dark"] as const).map((t) => (
                  <button
                    key={t}
                    onClick={() => setThemeAndSave(t)}
                    aria-pressed={theme === t}
                    className={`rounded-xl border px-4 py-1.5 text-sm ${
                      theme === t ? "border-brand-500 bg-brand-500 text-white" : ""
                    }`}
                  >
                    {t === "auto" ? "Авто" : t === "light" ? "Светлая" : "Тёмная"}
                  </button>
                ))}
              </div>
            </div>
            <div className="rounded-2xl border p-4">
              <p className="font-semibold">История поиска</p>
              <button
                onClick={() =>
                  del("/api/v1/search/history")
                    .then(() => toast.success("История поиска очищена"))
                    .catch(() => toast.error("Не получилось"))
                }
                className="mt-2 text-sm text-red-500 hover:underline"
              >
                Очистить историю поиска
              </button>
            </div>
          </div>
        )
      )}
    </div>
  );
}

function Toggle({
  label,
  hint,
  value,
  onChange,
}: {
  label: string;
  hint?: string;
  value: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <button
      role="switch"
      aria-checked={value}
      onClick={() => onChange(!value)}
      className="flex w-full items-center justify-between gap-4 rounded-2xl border p-4 text-left"
    >
      <span>
        <span className="block font-semibold">{label}</span>
        {hint && <span className="text-xs text-neutral-500">{hint}</span>}
      </span>
      <span
        className={`relative h-6 w-11 shrink-0 rounded-full transition-colors ${
          value ? "bg-brand-500" : "bg-neutral-300 dark:bg-neutral-700"
        }`}
      >
        <span
          className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-all ${
            value ? "left-[22px]" : "left-0.5"
          }`}
        />
      </span>
    </button>
  );
}
