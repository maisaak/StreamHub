import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { usePopular, useProviders } from "@/api/hooks";
import { patch, post } from "@/api/client";
import { useOnboardingStore } from "@/store";
import { cn } from "@/lib/utils";
import ContentCard from "./ContentCard";
import ProviderBadge from "./ProviderBadge";
import { RowSkeleton } from "./Skeletons";

const GENRES = ["комедии", "драмы", "фантастика", "документалки", "аниме", "стендап"];

export default function Onboarding({ onDone }: { onDone: () => void }) {
  const { step, setStep, providers, genres, toggleProvider, toggleGenre } = useOnboardingStore();
  const { data: allProviders, isLoading: pLoading } = useProviders();
  const { data: popular } = usePopular();
  const navigate = useNavigate();

  const finish = async () => {
    try {
      for (const pid of providers) {
        await post("/api/v1/providers/connect", { provider_id: pid }).catch(() => {});
      }
      await patch("/api/v1/preferences", { favorite_genres: genres }).catch(() => {});
      await patch("/api/v1/auth/me", { onboarding_completed: true });
      toast.success("Готово! Приятного просмотра 🍿");
      onDone();
      navigate("/");
    } catch {
      toast.error("Не получилось сохранить. Попробуйте ещё раз.");
    }
  };

  return (
    <div className="mx-auto max-w-3xl px-4 py-8" role="dialog" aria-label="Онбординг">
      <div
        className="mb-6 h-1.5 overflow-hidden rounded-full bg-neutral-200 dark:bg-neutral-800"
        role="progressbar"
        aria-valuenow={step}
        aria-valuemin={1}
        aria-valuemax={3}
      >
        <div
          className="h-full bg-brand-500 transition-all"
          style={{ width: `${(step / 3) * 100}%` }}
        />
      </div>

      {step === 1 && (
        <section>
          <h1 className="text-2xl font-bold">Какие сервисы у вас уже есть?</h1>
          <p className="mt-1 text-sm text-neutral-500">Мы подсветим, что доступно именно вам.</p>
          {pLoading ? (
            <div className="mt-6">
              <RowSkeleton count={4} />
            </div>
          ) : (
            <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
              {allProviders?.map((p) => {
                const active = providers.includes(p.id);
                return (
                  <button
                    key={p.id}
                    onClick={() => toggleProvider(p.id)}
                    aria-pressed={active}
                    className={cn(
                      "flex flex-col items-center gap-2 rounded-2xl border p-4 transition-all",
                      active
                        ? "border-brand-500 bg-brand-500/10 ring-2 ring-brand-500"
                        : "hover:border-brand-500",
                    )}
                  >
                    <ProviderBadge id={p.id} name={p.name} color={p.brand_color} size="lg" />
                    <span className="text-sm font-medium">{p.name}</span>
                  </button>
                );
              })}
            </div>
          )}
          <div className="mt-6 flex items-center justify-between">
            <button onClick={() => setStep(2)} className="text-xs text-neutral-400 hover:underline">
              Пропустить
            </button>
            <button
              onClick={() => setStep(2)}
              className="rounded-xl bg-brand-500 px-6 py-2.5 font-semibold text-white"
            >
              Далее
            </button>
          </div>
        </section>
      )}

      {step === 2 && (
        <section>
          <h1 className="text-2xl font-bold">Что вы любите смотреть?</h1>
          <p className="mt-1 text-sm text-neutral-500">Это повлияет на ленту «Рекомендуем».</p>
          <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-3">
            {GENRES.map((g) => {
              const active = genres.includes(g);
              return (
                <button
                  key={g}
                  onClick={() => toggleGenre(g)}
                  aria-pressed={active}
                  className={cn(
                    "rounded-2xl border p-5 text-lg font-semibold capitalize transition-all",
                    active
                      ? "border-brand-500 bg-brand-500/10 ring-2 ring-brand-500"
                      : "hover:border-brand-500",
                  )}
                >
                  {g}
                </button>
              );
            })}
          </div>
          <div className="mt-6 flex items-center justify-between">
            <button onClick={() => setStep(1)} className="text-sm text-neutral-500 hover:underline">
              Назад
            </button>
            <button
              onClick={() => setStep(3)}
              className="rounded-xl bg-brand-500 px-6 py-2.5 font-semibold text-white"
            >
              Далее
            </button>
          </div>
        </section>
      )}

      {step === 3 && (
        <section>
          <h1 className="text-2xl font-bold">Готово! Вот что можно посмотреть прямо сейчас</h1>
          <p className="mt-1 text-sm text-neutral-500">В ваших подписках — в один клик.</p>
          <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
            {popular?.slice(0, 8).map((c, i) => <ContentCard key={c.id} item={c} index={i} />) ?? (
              <RowSkeleton count={4} />
            )}
          </div>
          <button
            onClick={finish}
            className="mt-6 w-full rounded-xl bg-brand-500 px-6 py-3 font-semibold text-white"
          >
            Начать смотреть 🍿
          </button>
        </section>
      )}
    </div>
  );
}
