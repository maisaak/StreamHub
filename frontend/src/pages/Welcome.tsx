import { useQueryClient } from "@tanstack/react-query";
import { Navigate } from "react-router-dom";
import { getToken } from "@/api/client";
import { useMe } from "@/api/hooks";
import Onboarding from "@/components/Onboarding";

export default function Welcome() {
  const qc = useQueryClient();
  const loggedIn = !!getToken();
  const { data: me, isLoading } = useMe(loggedIn);

  if (!loggedIn) return <Navigate to="/login" replace />;
  if (isLoading) return <p className="p-8 text-center text-sm text-neutral-500">Загружаем…</p>;
  if (me?.onboarding_completed) return <Navigate to="/" replace />;

  return (
    <Onboarding
      onDone={() => {
        qc.invalidateQueries({ queryKey: ["me"] });
        qc.invalidateQueries({ queryKey: ["feed"] });
        qc.invalidateQueries({ queryKey: ["providers"] });
      }}
    />
  );
}
