import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { del, get, patch, post } from "./client";
import type {
  ContentCardData,
  ContentDetailData,
  FeedSection,
  Preferences,
  Provider,
  SuggestItem,
  User,
} from "@/types";

/* ---------- auth ---------- */
export function useMe(enabled = true) {
  return useQuery({
    queryKey: ["me"],
    queryFn: () => get<User>("/api/v1/auth/me"),
    enabled,
    retry: false,
    staleTime: 5 * 60_000,
  });
}

/* ---------- providers ---------- */
export function useProviders() {
  return useQuery({
    queryKey: ["providers"],
    queryFn: () => get<Provider[]>("/api/v1/providers"),
    staleTime: 60_60_000,
  });
}

export function useToggleProvider() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, connected }: { id: string; connected: boolean }) => {
      if (connected) return del<{ ok: boolean }>(`/api/v1/providers/disconnect/${id}`);
      return post<{ ok: boolean }>("/api/v1/providers/connect", { provider_id: id });
    },
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ["providers"] });
      qc.invalidateQueries({ queryKey: ["feed"] });
    },
  });
}

/* ---------- search ---------- */
export interface SearchParams {
  q: string;
  type?: string;
  year?: number | null;
  onlyMy?: boolean;
  free?: boolean;
  quality?: string;
  genres?: string[];
  minRating?: number;
}

export interface SearchResult {
  items: ContentCardData[];
  total: number;
  partial: boolean;
  failed_providers: string[];
  suggestions: string[];
  took_ms: number;
}

export function useSearch(params: SearchParams, enabled = true) {
  const key = ["search", params] as const;
  return useQuery({
    queryKey: key,
    queryFn: () => {
      const sp = new URLSearchParams();
      sp.set("q", params.q);
      if (params.type) sp.set("type", params.type);
      if (params.year) sp.set("year", String(params.year));
      if (params.onlyMy) sp.set("only_my", "true");
      if (params.free) sp.set("free", "true");
      if (params.quality && params.quality !== "any") sp.set("quality", params.quality);
      if (params.genres?.length) sp.set("genres", params.genres.join(","));
      if (params.minRating) sp.set("min_rating", String(params.minRating));
      return get<SearchResult>(`/api/v1/search?${sp.toString()}`);
    },
    enabled,
    staleTime: 60_000,
    placeholderData: (prev) => prev,
  });
}

export function useSuggest(q: string, enabled = true) {
  return useQuery({
    queryKey: ["suggest", q],
    queryFn: () =>
      get<{ items: SuggestItem[] }>(`/api/v1/search/suggest?q=${encodeURIComponent(q)}`),
    enabled: enabled && q.trim().length > 0,
    staleTime: 30_000,
  });
}

/* ---------- content ---------- */
export function useContent(id: string | undefined) {
  return useQuery({
    queryKey: ["content", id],
    queryFn: () => get<ContentDetailData>(`/api/v1/content/${id}`),
    enabled: !!id,
    staleTime: 5 * 60_000,
  });
}

export function useSimilar(id: string | undefined) {
  return useQuery({
    queryKey: ["similar", id],
    queryFn: () => get<{ items: ContentCardData[] }>(`/api/v1/content/${id}/similar`),
    enabled: !!id,
    staleTime: 5 * 60_000,
  });
}

export function useFeed() {
  return useQuery({
    queryKey: ["feed"],
    queryFn: () => get<{ sections: FeedSection[] }>("/api/v1/content/feed"),
    staleTime: 60_000,
  });
}

export function usePopular() {
  return useQuery({
    queryKey: ["popular"],
    queryFn: () => get<ContentCardData[]>("/api/v1/content/popular"),
    staleTime: 5 * 60_000,
  });
}

export function useTrackWatch() {
  return useMutation({
    mutationFn: ({ id, provider_id }: { id: string; provider_id?: string }) =>
      post<{ ok: boolean }>(`/api/v1/content/${id}/watch`, { provider_id }),
  });
}

export function useMarkWatched() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      watched,
      provider_id,
    }: {
      id: string;
      watched: boolean;
      provider_id?: string;
    }) => post<{ ok: boolean }>(`/api/v1/content/${id}/mark-watched`, { watched, provider_id }),
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ["feed"] });
      qc.invalidateQueries({ queryKey: ["history"] });
    },
  });
}

export function useShare() {
  return useMutation({
    mutationFn: (id: string) =>
      post<{ short_link: string; slug: string }>(`/api/v1/content/${id}/share`),
  });
}

/* ---------- watchlist ---------- */
export interface WatchlistItem {
  id: number;
  added_at: string;
  notify_on_release: boolean;
  content: ContentCardData;
}

export function useWatchlist() {
  return useQuery({
    queryKey: ["watchlist"],
    queryFn: () => get<WatchlistItem[]>("/api/v1/watchlist"),
    staleTime: 60_000,
  });
}

export function useWatchlistMutations() {
  const qc = useQueryClient();
  const invalidate = () => qc.invalidateQueries({ queryKey: ["watchlist"] });
  const add = useMutation({
    mutationFn: (content_id: string) => post("/api/v1/watchlist", { content_id }),
    onMutate: async (_content_id: string) => {
      await qc.cancelQueries({ queryKey: ["watchlist"] });
      const prev = qc.getQueryData<WatchlistItem[]>(["watchlist"]);
      return { prev };
    },
    onError: (_e, _v, ctx) => {
      if (ctx?.prev) qc.setQueryData(["watchlist"], ctx.prev);
    },
    onSettled: invalidate,
  });
  const removeByContent = useMutation({
    mutationFn: (content_id: string) => del(`/api/v1/watchlist/by-content/${content_id}`),
    onSettled: invalidate,
  });
  return { add, removeByContent };
}

/* ---------- history ---------- */
export interface ViewHistoryItem {
  id: number;
  viewed_at: string;
  provider_id: string | null;
  watched: boolean;
  content: ContentCardData;
}

export function useHistory() {
  return useQuery({
    queryKey: ["history"],
    queryFn: () => get<ViewHistoryItem[]>("/api/v1/history"),
    staleTime: 60_000,
  });
}

export function useClearHistory() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => del("/api/v1/history"),
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ["history"] });
      qc.invalidateQueries({ queryKey: ["feed"] });
    },
  });
}

/* ---------- preferences ---------- */
export function usePreferences() {
  return useQuery({
    queryKey: ["preferences"],
    queryFn: () => get<Preferences>("/api/v1/preferences"),
    staleTime: 5 * 60_000,
    retry: false,
  });
}

export function usePatchPreferences() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Preferences>) => patch<Preferences>("/api/v1/preferences", data),
    onSuccess: (data) => qc.setQueryData(["preferences"], data),
  });
}
