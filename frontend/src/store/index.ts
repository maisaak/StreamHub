import { create } from "zustand";
import { persist } from "zustand/middleware";
import { DEFAULT_FILTERS, type Filters } from "@/types";

/* theme: auto | light | dark */
interface ThemeState {
  theme: "auto" | "light" | "dark";
  setTheme: (t: "auto" | "light" | "dark") => void;
}

export function applyTheme(theme: "auto" | "light" | "dark") {
  const root = document.documentElement;
  const dark =
    theme === "dark" ||
    (theme === "auto" && window.matchMedia("(prefers-color-scheme: dark)").matches);
  root.classList.toggle("dark", dark);
  root.style.colorScheme = dark ? "dark" : "light";
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      theme: "auto",
      setTheme: (theme) => {
        applyTheme(theme);
        set({ theme });
      },
    }),
    { name: "sh-theme" },
  ),
);

/* filters (persisted -> synced to user_preferences when logged in) */
interface FilterState {
  filters: Filters;
  setFilters: (f: Partial<Filters>) => void;
  resetFilters: () => void;
}

export const useFilterStore = create<FilterState>()(
  persist(
    (set) => ({
      filters: DEFAULT_FILTERS,
      setFilters: (f) => set((s) => ({ filters: { ...s.filters, ...f } })),
      resetFilters: () => set({ filters: DEFAULT_FILTERS }),
    }),
    { name: "sh-filters" },
  ),
);

/* command palette */
interface PaletteState {
  open: boolean;
  setOpen: (v: boolean) => void;
}

export const usePaletteStore = create<PaletteState>()((set) => ({
  open: false,
  setOpen: (open) => set({ open }),
}));

/* onboarding */
interface OnboardingState {
  step: number;
  providers: string[];
  genres: string[];
  setStep: (n: number) => void;
  toggleProvider: (id: string) => void;
  toggleGenre: (g: string) => void;
  reset: () => void;
}

export const useOnboardingStore = create<OnboardingState>()((set) => ({
  step: 1,
  providers: [],
  genres: [],
  setStep: (step) => set({ step }),
  toggleProvider: (id) =>
    set((s) => ({
      providers: s.providers.includes(id)
        ? s.providers.filter((p) => p !== id)
        : [...s.providers, id],
    })),
  toggleGenre: (g) =>
    set((s) => ({
      genres: s.genres.includes(g) ? s.genres.filter((x) => x !== g) : [...s.genres, g],
    })),
  reset: () => set({ step: 1, providers: [], genres: [] }),
}));

/* optimistic watchlist ids (for instant UI) */
interface WatchUIState {
  savedIds: string[];
  setSaved: (ids: string[]) => void;
  toggleSaved: (id: string) => void;
}

export const useWatchUIStore = create<WatchUIState>()((set) => ({
  savedIds: [],
  setSaved: (savedIds) => set({ savedIds }),
  toggleSaved: (id) =>
    set((s) => ({
      savedIds: s.savedIds.includes(id) ? s.savedIds.filter((x) => x !== id) : [...s.savedIds, id],
    })),
}));
