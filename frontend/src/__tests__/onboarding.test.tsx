import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import Onboarding from "@/components/Onboarding";
import { useOnboardingStore } from "@/store";

vi.mock("@/api/hooks", () => ({
  useProviders: () => ({
    data: [
      { id: "ivi", name: "Иви", brand_color: "#EB1537" },
      { id: "okko", name: "Okko", brand_color: "#3B1D5E" },
    ],
    isLoading: false,
  }),
  usePopular: () => ({ data: [] }),
}));

function renderOb() {
  useOnboardingStore.setState({ step: 1, providers: [], genres: [] });
  const qc = new QueryClient();
  return render(
    <QueryClientProvider client={qc}>
      <BrowserRouter>
        <Onboarding onDone={() => {}} />
      </BrowserRouter>
    </QueryClientProvider>,
  );
}

describe("Onboarding", () => {
  it("step 1 shows providers and toggles them", () => {
    renderOb();
    expect(screen.getByText("Какие сервисы у вас уже есть?")).toBeInTheDocument();
    const ivi = screen.getByText("Иви");
    fireEvent.click(ivi);
    expect(useOnboardingStore.getState().providers).toContain("ivi");
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "1");
  });

  it("navigates to step 2", () => {
    renderOb();
    fireEvent.click(screen.getByText("Далее"));
    expect(screen.getByText("Что вы любите смотреть?")).toBeInTheDocument();
  });
});
