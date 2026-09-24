export interface Source {
  provider_id: string;
  provider_name: string;
  brand_color: string;
  logo_url: string;
  external_url: string;
  deep_link: string | null;
  price: number | null;
  is_subscription: boolean;
  quality: string;
  connected: boolean;
  rank: number;
}

export interface ContentCardData {
  id: string;
  content_type: "movie" | "series" | "video";
  title: string;
  original_title: string;
  year: number | null;
  poster_url: string;
  backdrop_url: string;
  genres: string[];
  rating_kinopoisk: number | null;
  rating_imdb: number | null;
  runtime_minutes: number | null;
  providers: string[];
  best_source: Source | null;
  free: boolean;
}

export interface ContentDetailData extends ContentCardData {
  description: string;
  sources: Source[];
  short_link: string;
}

export interface Provider {
  id: string;
  name: string;
  logo_url: string;
  base_url: string;
  brand_color: string;
  requires_subscription: boolean;
  is_active: boolean;
  priority: number;
  connected: boolean;
}

export interface FeedSection {
  key: string;
  title: string;
  items: ContentCardData[];
}

export interface SuggestItem {
  kind: "history" | "content";
  text: string;
  content_id: string | null;
  poster_url: string;
  year: number | null;
}

export interface User {
  id: string;
  email: string;
  display_name: string;
  onboarding_completed: boolean;
  preferred_theme: string;
  preferred_language: string;
}

export interface Preferences {
  only_my_subscriptions: boolean;
  preferred_quality: string;
  hide_watched: boolean;
  auto_play_next: boolean;
  favorite_genres: string[];
}

export interface Filters {
  onlyMy: boolean;
  free: boolean;
  type: "" | "movie" | "series" | "video";
  quality: string;
  genres: string[];
  minRating: number;
  year: number | null;
}

export const DEFAULT_FILTERS: Filters = {
  onlyMy: false,
  free: false,
  type: "",
  quality: "any",
  genres: [],
  minRating: 0,
  year: null,
};
