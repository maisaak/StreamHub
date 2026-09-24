import { Bookmark, Clock, Home, LogOut, Moon, Puzzle, Search, Settings, Sun } from "lucide-react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { clearTokens, getToken } from "@/api/client";
import { useMe } from "@/api/hooks";
import { usePaletteStore, useThemeStore } from "@/store";
import { cn } from "@/lib/utils";

export default function Header({ onLogoLongPress }: { onLogoLongPress?: () => void }) {
  const { theme, setTheme } = useThemeStore();
  const { setOpen } = usePaletteStore();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const loggedIn = !!getToken();
  const { data: me } = useMe(loggedIn);
  let pressTimer: number | null = null;

  const logout = () => {
    clearTokens();
    qc.clear();
    navigate("/");
  };

  const toggleTheme = () => setTheme(theme === "dark" ? "light" : "dark");
  const dark =
    theme === "dark" ||
    (theme === "auto" && window.matchMedia("(prefers-color-scheme: dark)").matches);

  const linkCls = ({ isActive }: { isActive: boolean }) =>
    cn(
      "flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium",
      isActive
        ? "bg-neutral-200 dark:bg-neutral-800"
        : "text-neutral-500 hover:text-neutral-900 dark:hover:text-white",
    );

  return (
    <header className="sticky top-0 z-40 border-b border-neutral-200 bg-white/80 backdrop-blur dark:border-neutral-800 dark:bg-[#0f0f14]/80">
      <div className="mx-auto flex max-w-6xl items-center gap-2 px-4 py-2.5">
        <Link
          to="/"
          aria-label="StreamHub — на главную"
          className="flex items-center gap-2 font-extrabold"
          onTouchStart={() => {
            pressTimer = window.setTimeout(() => onLogoLongPress?.() ?? setOpen(true), 600);
          }}
          onTouchEnd={() => pressTimer && window.clearTimeout(pressTimer)}
        >
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-500 text-white">
            ▶
          </span>
          <span className="hidden sm:inline">StreamHub</span>
        </Link>

        <nav className="ml-2 hidden items-center gap-1 md:flex" aria-label="Основная навигация">
          <NavLink to="/" className={linkCls}>
            <Home size={15} /> Главная
          </NavLink>
          <NavLink to="/services" className={linkCls}>
            <Puzzle size={15} /> Сервисы
          </NavLink>
          {loggedIn && (
            <>
              <NavLink to="/watchlist" className={linkCls}>
                <Bookmark size={15} /> Список
              </NavLink>
              <NavLink to="/history" className={linkCls}>
                <Clock size={15} /> История
              </NavLink>
            </>
          )}
        </nav>

        <div className="ml-auto flex items-center gap-1">
          <button
            onClick={() => setOpen(true)}
            aria-label="Командная палитра (Ctrl+K)"
            title="Команды (Ctrl+K)"
            className="hidden items-center gap-1 rounded-lg border border-neutral-300 px-2.5 py-1.5 text-xs text-neutral-500 sm:flex dark:border-neutral-700"
          >
            <Search size={13} /> ⌘K
          </button>
          <button
            onClick={toggleTheme}
            aria-label={dark ? "Светлая тема" : "Тёмная тема"}
            title="Сменить тему"
            className="rounded-lg p-2 text-neutral-500 hover:bg-neutral-100 dark:hover:bg-neutral-800"
          >
            {dark ? <Sun size={18} /> : <Moon size={18} />}
          </button>
          {loggedIn ? (
            <>
              <Link
                to="/settings"
                aria-label="Настройки"
                className="rounded-lg p-2 text-neutral-500 hover:bg-neutral-100 dark:hover:bg-neutral-800"
              >
                <Settings size={18} />
              </Link>
              <span className="hidden text-sm text-neutral-500 lg:inline">{me?.display_name}</span>
              <button
                onClick={logout}
                aria-label="Выйти"
                title="Выйти"
                className="rounded-lg p-2 text-neutral-500 hover:bg-neutral-100 dark:hover:bg-neutral-800"
              >
                <LogOut size={18} />
              </button>
            </>
          ) : (
            <>
              <Link
                to="/login"
                className="rounded-lg px-3 py-1.5 text-sm font-medium text-neutral-500 hover:text-neutral-900"
              >
                Войти
              </Link>
              <Link
                to="/register"
                className="rounded-lg bg-brand-500 px-3 py-1.5 text-sm font-semibold text-white"
              >
                Регистрация
              </Link>
            </>
          )}
        </div>
      </div>

      {/* mobile bottom nav */}
      <nav
        className="flex justify-around border-t border-neutral-200 py-1 md:hidden dark:border-neutral-800"
        aria-label="Мобильная навигация"
      >
        <NavLink to="/" className={linkCls} aria-label="Главная">
          <Home size={18} />
        </NavLink>
        <NavLink to="/services" className={linkCls} aria-label="Сервисы">
          <Puzzle size={18} />
        </NavLink>
        {loggedIn && (
          <>
            <NavLink to="/watchlist" className={linkCls} aria-label="Список">
              <Bookmark size={18} />
            </NavLink>
            <NavLink to="/history" className={linkCls} aria-label="История">
              <Clock size={18} />
            </NavLink>
          </>
        )}
      </nav>
    </header>
  );
}
