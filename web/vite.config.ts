import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  build: {
    // maplibre-gl alone is ~1 MB minified; it is split into its own cached chunk.
    chunkSizeWarningLimit: 1100,
    rolldownOptions: {
      output: {
        advancedChunks: {
          groups: [
            { name: "maplibre", test: /maplibre-gl/ },
            { name: "charts", test: /recharts|d3-|victory/ },
          ],
        },
      },
    },
  },
  server: {
    proxy: { "/api": "http://127.0.0.1:8000" },
  },
});
