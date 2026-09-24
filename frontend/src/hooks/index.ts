import { useEffect, useRef, useState } from "react";

export function useDebounce<T>(value: T, delay = 250): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(t);
  }, [value, delay]);
  return debounced;
}

export function usePrefetchContent(prefetch: (id: string) => void, delay = 200) {
  const timer = useRef<number | null>(null);
  const onEnter = (id: string) => {
    timer.current = window.setTimeout(() => prefetch(id), delay);
  };
  const onLeave = () => {
    if (timer.current) window.clearTimeout(timer.current);
  };
  useEffect(() => () => onLeave(), []);
  return { onEnter, onLeave };
}

export function useVisitCount(key = "sh-visits"): number {
  const [count, setCount] = useState(0);
  useEffect(() => {
    const n = Number(localStorage.getItem(key) ?? 0) + 1;
    localStorage.setItem(key, String(n));
    setCount(n);
  }, [key]);
  return count;
}
