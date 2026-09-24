import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";
import { post, setTokens } from "@/api/client";

const schema = z.object({
  email: z.string().email("Введите корректный email"),
  password: z.string().min(6, "Минимум 6 символов"),
  display_name: z.string().optional(),
});

type FormData = z.infer<typeof schema>;

export function Login() {
  return <AuthForm mode="login" />;
}

export function Register() {
  return <AuthForm mode="register" />;
}

function AuthForm({ mode }: { mode: "login" | "register" }) {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [busy, setBusy] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: FormData) => {
    setBusy(true);
    try {
      const res = await post<{ access_token: string; refresh_token: string }>(
        `/api/v1/auth/${mode}`,
        mode === "register"
          ? { email: data.email, password: data.password, display_name: data.display_name || "" }
          : { email: data.email, password: data.password },
      );
      setTokens(res.access_token, res.refresh_token);
      await qc.invalidateQueries({ queryKey: ["me"] });
      toast.success(mode === "register" ? "Добро пожаловать в StreamHub! 🎬" : "С возвращением!");
      navigate(mode === "register" ? "/welcome" : "/");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Не получилось войти");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto max-w-md px-4 py-12">
      <h1 className="text-2xl font-extrabold">
        {mode === "login" ? "С возвращением 👋" : "Создать аккаунт 🎬"}
      </h1>
      <p className="mt-1 text-sm text-neutral-500">
        {mode === "login" ? (
          <>
            Нет аккаунта?{" "}
            <Link to="/register" className="text-brand-500 hover:underline">
              Зарегистрируйтесь
            </Link>
          </>
        ) : (
          <>
            Уже есть аккаунт?{" "}
            <Link to="/login" className="text-brand-500 hover:underline">
              Войдите
            </Link>
          </>
        )}
      </p>
      <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-3">
        {mode === "register" && (
          <div>
            <label className="text-sm font-medium" htmlFor="display_name">
              Имя
            </label>
            <input
              id="display_name"
              {...register("display_name")}
              placeholder="Как вас называть?"
              className="mt-1 w-full rounded-xl border px-3 py-2.5 dark:bg-neutral-900"
            />
          </div>
        )}
        <div>
          <label className="text-sm font-medium" htmlFor="email">
            Email
          </label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            {...register("email")}
            className="mt-1 w-full rounded-xl border px-3 py-2.5 dark:bg-neutral-900"
          />
          {errors.email && <p className="mt-1 text-xs text-red-500">{errors.email.message}</p>}
        </div>
        <div>
          <label className="text-sm font-medium" htmlFor="password">
            Пароль
          </label>
          <input
            id="password"
            type="password"
            autoComplete={mode === "login" ? "current-password" : "new-password"}
            {...register("password")}
            className="mt-1 w-full rounded-xl border px-3 py-2.5 dark:bg-neutral-900"
          />
          {errors.password && (
            <p className="mt-1 text-xs text-red-500">{errors.password.message}</p>
          )}
        </div>
        <button
          type="submit"
          disabled={busy}
          className="w-full rounded-xl bg-brand-500 py-3 font-bold text-white disabled:opacity-50"
        >
          {busy ? "Подождите…" : mode === "login" ? "Войти" : "Создать аккаунт"}
        </button>
      </form>
    </div>
  );
}
