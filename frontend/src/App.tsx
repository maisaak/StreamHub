import { useEffect } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "sonner";
import { getToken } from "@/api/client";
import { useMe } from "@/api/hooks";
import CommandPalette from "@/components/CommandPalette";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import Header from "@/components/Header";
import { applyTheme, usePaletteStore, useThemeStore, useWatchUIStore } from "@/store";
import { useVisitCount } from "@/hooks";
import ContentDetail from "@/pages/ContentDetail";
import History from "@/pages/History";
import Home from "@/pages/Home";
import MyServices from "@/pages/MyServices";
import SearchResults from "@/pages/SearchResults";
import Settings from "@/pages/Settings";
import Watchlist from "@/pages/Watchlist";
import Welcome from "@/pages/Welcome";
import { Login, Register } from "@/pages/Auth";
import { get } from "@/api/client";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false },
  },
});

function ThemeInit() {
  const { theme } = useThemeStore();
  useEffect(() => {
    applyTheme(theme);
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => theme === "auto" && applyTheme("auto");
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, [theme]);
  return null;
}

function WatchlistSync() {
  const { setSaved } = useWatchUIStore();
  useEffect(() => {
    if (!getToken()) return;
    get<{ content: { id: string } }[]>("/api/v1/watchlist")
      .then((items) => setSaved(items.map((i) => i.content.id)))
      .catch(() => {});
  }, [setSaved]);
  return null;
}

function ServiceWorkerInit() {
  const visits = useVisitCount();
  useEffect(() => {
    if ("serviceWorker" in navigator && import.meta.env.PROD) {
      navigator.serviceWorker.register("/sw.js").catch(() => {});
    }
  }, []);
  useEffect(() => {
    // install prompt hint after 3rd visit (spec §12 PWA)
    if (visits === 3) console.info("[StreamHub] PWA install prompt eligible");
  }, [visits]);
  return null;
}

function RequireAuth({ children }: { children: JSX.Element }) {
  const loggedIn = !!getToken();
  const { isLoading, isError } = useMe(loggedIn);
  if (!loggedIn) return <Navigate to="/login" replace />;
  if (isLoading) return <p className="p-8 text-center text-sm text-neutral-500">Загружаем…</p>;
  if (isError) return <Navigate to="/login" replace />;
  return children;
}

function RequireOnboarding({ children }: { children: JSX.Element }) {
  const loggedIn = !!getToken();
  const { data: me, isLoading } = useMe(loggedIn);
  if (loggedIn && !isLoading && me && !me.onboarding_completed) {
    return <Navigate to="/welcome" replace />;
  }
  return children;
}

function Shell({ children }: { children: React.ReactNode }) {
  const { setOpen } = usePaletteStore();
  return (
    <div className="min-h-screen">
      <Header onLogoLongPress={() => setOpen(true)} />
      <main>{children}</main>
      <CommandPalette />
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ThemeInit />
        <WatchlistSync />
        <ServiceWorkerInit />
        <Toaster position="bottom-center" richColors closeButton />
        <ErrorBoundary>
          <Shell>
            <Routes>
              <Route
                path="/"
                element={
                  <RequireOnboarding>
                    <Home />
                  </RequireOnboarding>
                }
              />
              <Route path="/search" element={<SearchResults />} />
              <Route path="/content/:id" element={<ContentDetail />} />
              <Route path="/services" element={<MyServices />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/welcome" element={<Welcome />} />
              <Route
                path="/watchlist"
                element={
                  <RequireAuth>
                    <Watchlist />
                  </RequireAuth>
                }
              />
              <Route
                path="/history"
                element={
                  <RequireAuth>
                    <History />
                  </RequireAuth>
                }
              />
              <Route
                path="/settings"
                element={
                  <RequireAuth>
                    <Settings />
                  </RequireAuth>
                }
              />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Shell>
        </ErrorBoundary>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
