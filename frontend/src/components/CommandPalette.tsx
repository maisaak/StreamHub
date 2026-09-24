import { Command } from "cmdk";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { get } from "@/api/client";
import { getToken } from "@/api/client";
import { usePaletteStore, useThemeStore } from "@/store";

export default function CommandPalette() {
  const { open, setOpen } = usePaletteStore();
  const { theme, setTheme } = useThemeStore();
  const [history, setHistory] = useState<{ query: string }[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen(!usePaletteStore.getState().open);
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [setOpen]);

  useEffect(() => {
    if (open && getToken()) {
      get<{ query: string }[]>("/api/v1/search/history")
        .then((h) => setHistory(h.slice(0, 5)))
        .catch(() => setHistory([]));
    }
  }, [open]);

  const go = (to: string) => {
    setOpen(false);
    navigate(to);
  };

  const cycleTheme = () => {
    const next = theme === "light" ? "dark" : theme === "dark" ? "auto" : "light";
    setTheme(next);
    setOpen(false);
  };

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center bg-black/50 p-4 pt-[15vh]"
      onClick={() => setOpen(false)}
      role="dialog"
      aria-modal="true"
      aria-label="Командная палитра"
    >
      <div onClick={(e) => e.stopPropagation()} className="w-full max-w-lg">
        <Command
          label="Команды"
          className="overflow-hidden rounded-2xl border border-neutral-200 bg-white shadow-2xl dark:border-neutral-700 dark:bg-neutral-900"
        >
          <Command.Input
            placeholder="Найти или перейти…"
            className="w-full border-b border-neutral-200 bg-transparent px-4 py-3 outline-none dark:border-neutral-700"
            autoFocus
          />
          <Command.List className="max-h-80 overflow-auto p-2">
            <Command.Empty className="p-4 text-sm text-neutral-500">
              Ничего не найдено. Введите запрос и нажмите Enter для поиска.
            </Command.Empty>
            <Command.Group heading="Навигация">
              <CmdItem onSelect={() => go("/watchlist")}>📑 Перейти в список</CmdItem>
              <CmdItem onSelect={() => go("/history")}>🕓 Перейти в историю</CmdItem>
              <CmdItem onSelect={() => go("/services")}>🧩 Мои сервисы</CmdItem>
              <CmdItem onSelect={() => go("/settings")}>⚙️ Настройки</CmdItem>
              <CmdItem onSelect={cycleTheme}>🌓 Сменить тему (сейчас: {theme})</CmdItem>
            </Command.Group>
            {history.length > 0 && (
              <Command.Group heading="Недавние поиски">
                {history.map((h, i) => (
                  <CmdItem key={i} onSelect={() => go(`/search?q=${encodeURIComponent(h.query)}`)}>
                    🔎 {h.query}
                  </CmdItem>
                ))}
              </Command.Group>
            )}
          </Command.List>
        </Command>
      </div>
    </div>
  );
}

function CmdItem({ children, onSelect }: { children: React.ReactNode; onSelect: () => void }) {
  return (
    <Command.Item
      onSelect={onSelect}
      className="cursor-pointer rounded-lg px-3 py-2 text-sm aria-selected:bg-neutral-100 dark:aria-selected:bg-neutral-800"
    >
      {children}
    </Command.Item>
  );
}
