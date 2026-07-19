import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],

  build: {
    modulePreload: false,
    rollupOptions: {
      output: {
        manualChunks: {
          react: ["react", "react-dom", "react-router-dom"],
          "react-query": ["@tanstack/react-query"],
          leaflet: ["leaflet", "react-leaflet", "leaflet.markercluster"],
          vendor: [
            "axios",
            "lucide-react",
            "react-hook-form",
            "@hookform/resolvers",
            "zod",
            "framer-motion",
            "radix-ui",
            "zustand",
            "class-variance-authority",
            "clsx",
            "tailwind-merge"
          ]
        },
      },
    },
  },

  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },

  server: {
    host: "0.0.0.0",
    port: 5173,
  },
});
