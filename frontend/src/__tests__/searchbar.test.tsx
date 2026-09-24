import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import SearchBar from "@/components/SearchBar";

vi.mock("@/api/hooks", () => ({
  useSuggest: () => ({
    data: {
      items: [
        { kind: "history", text: "матрица", content_id: null, poster_url: "", year: null },
        { kind: "content", text: "Матрица", content_id: "123", poster_url: "p.jpg", year: 1999 },
      ],
    },
  }),
}));

function renderBar() {
  const qc = new QueryClient();
  return render(
    <QueryClientProvider client={qc}>
      <BrowserRouter>
        <SearchBar />
      </BrowserRouter>
    </QueryClientProvider>,
  );
}

describe("SearchBar", () => {
  it("renders with placeholder and focuses", () => {
    renderBar();
    const input = screen.getByRole("combobox");
    expect(input).toHaveAttribute("placeholder", "Что посмотрим сегодня?");
  });

  it("debounces query changes (250ms)", async () => {
    const qc = new QueryClient();
    const onQueryChange = vi.fn();
    render(
      <QueryClientProvider client={qc}>
        <BrowserRouter>
          <SearchBar onQueryChange={onQueryChange} />
        </BrowserRouter>
      </QueryClientProvider>,
    );
    // initial mount fires once with ""
    await waitFor(() => expect(onQueryChange).toHaveBeenCalledWith(""));
    onQueryChange.mockClear();
    const input = screen.getByRole("combobox");
    await userEvent.type(input, "мат");
    // debounce: must not fire synchronously
    expect(onQueryChange).not.toHaveBeenCalled();
    await waitFor(() => expect(onQueryChange).toHaveBeenCalledWith("мат"), { timeout: 1000 });
  });

  it("shows history-first suggestions", async () => {
    renderBar();
    const input = screen.getByRole("combobox");
    await userEvent.type(input, "матр");
    await waitFor(() => {
      expect(screen.getByRole("listbox")).toBeInTheDocument();
    });
    const options = screen.getAllByRole("option");
    expect(options[0]).toHaveTextContent("матрица");
  });

  it("clears input with X button", async () => {
    renderBar();
    const input = screen.getByRole("combobox") as HTMLInputElement;
    await userEvent.type(input, "дюна");
    expect(input.value).toBe("дюна");
    await userEvent.click(screen.getByLabelText("Очистить поиск"));
    expect(input.value).toBe("");
  });
});
