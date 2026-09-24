import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import ContentCard from "@/components/ContentCard";
import type { ContentCardData } from "@/types";

vi.mock("@/api/hooks", () => ({
  useWatchlistMutations: () => ({
    add: { mutate: vi.fn() },
    removeByContent: { mutate: vi.fn() },
  }),
}));

const item: ContentCardData = {
  id: "1",
  content_type: "movie",
  title: "Матрица",
  original_title: "The Matrix",
  year: 1999,
  poster_url: "poster.jpg",
  backdrop_url: "",
  genres: ["фантастика"],
  rating_kinopoisk: 8.5,
  rating_imdb: 8.7,
  runtime_minutes: 136,
  providers: ["ivi", "okko"],
  best_source: {
    provider_id: "ivi",
    provider_name: "Иви",
    brand_color: "#EB1537",
    logo_url: "",
    external_url: "https://ivi.ru/watch/1",
    deep_link: null,
    price: null,
    is_subscription: true,
    quality: "4K",
    connected: true,
    rank: 0,
  },
  free: false,
};

describe("ContentCard", () => {
  it("renders title, year, rating and best source", () => {
    const qc = new QueryClient();
    render(
      <QueryClientProvider client={qc}>
        <BrowserRouter>
          <ContentCard item={item} />
        </BrowserRouter>
      </QueryClientProvider>,
    );
    expect(screen.getByText("Матрица")).toBeInTheDocument();
    expect(screen.getByText("1999")).toBeInTheDocument();
    expect(screen.getByText("★ 8.5")).toBeInTheDocument();
    expect(screen.getByText("Иви")).toBeInTheDocument();
    expect(screen.getByAltText("Постер: Матрица")).toBeInTheDocument();
  });
});
