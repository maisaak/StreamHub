import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import CommandPalette from "@/components/CommandPalette";
import { usePaletteStore } from "@/store";

describe("CommandPalette", () => {
  it("renders navigation commands when open", () => {
    usePaletteStore.setState({ open: true });
    const qc = new QueryClient();
    render(
      <QueryClientProvider client={qc}>
        <BrowserRouter>
          <CommandPalette />
        </BrowserRouter>
      </QueryClientProvider>,
    );
    expect(screen.getByText("📑 Перейти в список")).toBeInTheDocument();
    expect(screen.getByText("🌓 Сменить тему (сейчас: auto)")).toBeInTheDocument();
    usePaletteStore.setState({ open: false });
  });

  it("hidden when closed", () => {
    usePaletteStore.setState({ open: false });
    const qc = new QueryClient();
    const { container } = render(
      <QueryClientProvider client={qc}>
        <BrowserRouter>
          <CommandPalette />
        </BrowserRouter>
      </QueryClientProvider>,
    );
    expect(container).toBeEmptyDOMElement();
  });
});
