import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { getToken } from "@/api/client";
import { useProviders, useToggleProvider } from "@/api/hooks";
import ProviderBadge from "@/components/ProviderBadge";
import { RowSkeleton } from "@/components/Skeletons";
import { cn } from "@/lib/utils";

export default function MyServices() {
  const { data: providers, isLoading } = useProviders();
  const toggle = useToggleProvider();
  const navigate = useNavigate();
  const loggedIn = !!getToken();

  const onToggle = (id: string, connected: boolean, name: string) => {
    if (!loggedIn) {
      toast.info("Войдите, чтобы подключать сервисы");
      navigate("/login");
      return;
    }
    toggle.mutate(
      { id, connected },
      {
        onSuccess: () => toast.success(connected ? `${name} отключён` : `${name} подключён`),
        onError: () => toast.error("Не получилось. Попробуйте ещё раз."),
      },
    );
  };

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="text-2xl font-extrabold">Мои сервисы</h1>
      <p className="mt-1 text-sm text-neutral-500">
        Подключите подписки — и мы подсветим, что доступно именно вам.
      </p>
      {isLoading ? (
        <div className="mt-6">
          <RowSkeleton count={4} />
        </div>
      ) : (
        <div className="mt-6 space-y-2">
          {providers?.map((p) => (
            <div
              key={p.id}
              className={cn(
                "flex items-center gap-3 rounded-2xl border p-3",
                p.connected && "border-brand-500 bg-brand-500/5",
              )}
            >
              <ProviderBadge id={p.id} name={p.name} color={p.brand_color} size="lg" />
              <div className="min-w-0 flex-1">
                <p className="font-semibold">{p.name}</p>
                <p className="truncate text-xs text-neutral-500">
                  {p.requires_subscription ? "По подписке" : "Бесплатно"} ·{" "}
                  {p.base_url.replace("https://", "")}
                </p>
              </div>
              <button
                onClick={() => onToggle(p.id, p.connected, p.name)}
                aria-pressed={p.connected}
                className={cn(
                  "shrink-0 rounded-xl px-4 py-2 text-sm font-semibold",
                  p.connected ? "border" : "bg-brand-500 text-white",
                )}
              >
                {p.connected ? "Отключить" : "Подключить"}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
