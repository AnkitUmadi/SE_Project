import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Send every /api request to the Flask backend, so the browser sees one origin.
    proxy: {
      "/api": "http://127.0.0.1:5000",
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/setupTests.js",
    coverage: {
      provider: "v8",
      include: ["src/**/*.{js,jsx}"],
      exclude: ["src/main.jsx", "src/setupTests.js", "src/**/*.test.{js,jsx}"],
      thresholds: { lines: 60 },
    },
  },
});
