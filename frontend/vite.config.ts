import react from "@vitejs/plugin-react";
import path from "path";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { "@": path.resolve(__dirname, "src") } },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ["react", "react-dom", "react-router-dom"],
          query: ["@tanstack/react-query", "zustand"],
          ui: ["framer-motion", "cmdk", "sonner", "lucide-react"],
        },
      },
    },
  },
  server: {
    host: "0.0.0.0",
    port: 5173,
    allowedHosts: true as unknown as string[],
    hmr: { clientPort: 443 },
    proxy: {
      "/api": { target: "http://localhost:8000", changeOrigin: true },
      "/s": { target: "http://localhost:8000", changeOrigin: true },
      "/health": { target: "http://localhost:8000", changeOrigin: true },
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test-setup.ts"],
    globals: true,
    include: ["src/**/*.{test,spec}.?(c|m)[jt]s?(x)"],
  },
});
