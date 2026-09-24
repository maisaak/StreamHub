import { Mic, Search, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useSuggest } from "@/api/hooks";
import { useDebounce } from "@/hooks";
import { cn } from "@/lib/utils";

export default function SearchBar({
  initial = "",
  autoFocus = false,
  onQueryChange,
}: {
  initial?: string;
  autoFocus?: boolean;
  onQueryChange?: (q: string) => void;
}) {
  const [value, setValue] = useState(initial);
  const [open, setOpen] = useState(false);
  const [highlight, setHighlight] = useState(-1);
  const debounced = useDebounce(value, 250);
  const { data } = useSuggest(debounced, open && debounced.trim().length > 0);
  const items = data?.items ?? [];
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const boxRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setValue(initial);
  }, [initial]);

  useEffect(() => {
    onQueryChange?.(debounced);
  }, [debounced]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (autoFocus) inputRef.current?.focus();
  }, [autoFocus]);

  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (!boxRef.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  // "/" focuses search globally
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      const typing = target.tagName === "INPUT" || target.tagName === "TEXTAREA";
      if (e.key === "/" && !typing) {
        e.preventDefault();
        inputRef.current?.focus();
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, []);

  const go = (q: string) => {
    setOpen(false);
    navigate(q.trim() ? `/search?q=${encodeURIComponent(q.trim())}` : "/");
  };

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setOpen(true);
      setHighlight((h) => Math.min(h + 1, items.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlight((h) => Math.max(h - 1, -1));
    } else if (e.key === "Enter") {
      if (highlight >= 0 && items[highlight]) {
        const it = items[highlight];
        if (it.kind === "content" && it.content_id) {
          setOpen(false);
          navigate(`/content/${it.content_id}`);
          return;
        }
        setValue(it.text);
        go(it.text);
      } else {
        go(value);
      }
    } else if (e.key === "Escape") {
      setOpen(false);
      inputRef.current?.blur();
    }
  };

  const voiceSearch = () => {
    interface SpeechRecognitionLike {
      lang: string;
      onresult: ((e: { results?: { 0?: { 0?: { transcript?: string } } } }) => void) | null;
      start: () => void;
    }
    interface WindowWithSpeech {
      webkitSpeechRecognition?: new () => SpeechRecognitionLike;
      SpeechRecognition?: new () => SpeechRecognitionLike;
    }
    const w = window as unknown as WindowWithSpeech;
    const SR = w.webkitSpeechRecognition ?? w.SpeechRecognition;
    if (!SR) return;
    const rec = new SR();
    rec.lang = "ru-RU";
    rec.onresult = (e) => {
      const text = e.results?.[0]?.[0]?.transcript ?? "";
      if (text) {
        setValue(text);
        go(text);
      }
    };
    rec.start();
  };

  const supportsVoice =
    typeof window !== "undefined" &&
    ("webkitSpeechRecognition" in window || "SpeechRecognition" in window);

  return (
    <div ref={boxRef} className="relative w-full">
      <div className="flex items-center gap-2 rounded-2xl border border-neutral-300 bg-white px-4 py-3 shadow-sm focus-within:border-brand-500 dark:border-neutral-700 dark:bg-neutral-900">
        <Search size={20} className="shrink-0 text-neutral-400" aria-hidden />
        <input
          ref={inputRef}
          role="combobox"
          aria-expanded={open}
          aria-controls="search-suggest"
          aria-autocomplete="list"
          aria-label="Поиск фильмов и видео"
          value={value}
          onChange={(e) => {
            setValue(e.target.value);
            setOpen(true);
            setHighlight(-1);
          }}
          onFocus={() => setOpen(true)}
          onKeyDown={onKeyDown}
          placeholder="Что посмотрим сегодня?"
          className="w-full bg-transparent text-base outline-none placeholder:text-neutral-400"
        />
        {value && (
          <button
            onClick={() => {
              setValue("");
              inputRef.current?.focus();
            }}
            aria-label="Очистить поиск"
            className="rounded-full p-1 text-neutral-400 hover:text-neutral-600"
          >
            <X size={16} />
          </button>
        )}
        {supportsVoice && (
          <button
            onClick={voiceSearch}
            aria-label="Голосовой поиск"
            title="Голосовой поиск"
            className="rounded-full p-1 text-neutral-400 hover:text-brand-500"
          >
            <Mic size={18} />
          </button>
        )}
        <kbd className="hidden rounded border px-1.5 text-[11px] text-neutral-400 sm:block">/</kbd>
      </div>

      {open && items.length > 0 && (
        <ul
          id="search-suggest"
          role="listbox"
          aria-label="Подсказки"
          className="absolute z-30 mt-2 w-full overflow-hidden rounded-xl border border-neutral-200 bg-white shadow-xl dark:border-neutral-700 dark:bg-neutral-900"
        >
          {items.map((it, i) => (
            <li key={`${it.kind}-${i}-${it.text}`} role="option" aria-selected={i === highlight}>
              <button
                onMouseEnter={() => setHighlight(i)}
                onClick={() => {
                  if (it.kind === "content" && it.content_id) {
                    setOpen(false);
                    navigate(`/content/${it.content_id}`);
                  } else {
                    setValue(it.text);
                    go(it.text);
                  }
                }}
                className={cn(
                  "flex w-full items-center gap-3 px-3 py-2 text-left text-sm",
                  i === highlight && "bg-neutral-100 dark:bg-neutral-800",
                )}
              >
                {it.kind === "history" ? (
                  <span aria-hidden>🕓</span>
                ) : it.poster_url ? (
                  <img
                    src={it.poster_url}
                    alt=""
                    className="h-12 w-8 rounded object-cover"
                    loading="lazy"
                  />
                ) : (
                  <span aria-hidden>🎬</span>
                )}
                <span className="truncate">{it.text}</span>
                {it.year && <span className="ml-auto text-xs text-neutral-400">{it.year}</span>}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
