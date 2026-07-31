import path from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv, type UserConfig } from "vite";

function buildContentSecurityPolicy(apiUrl: string): string {
  const normalizedApiUrl = apiUrl.trim().replace(/\/+$/, "");

  return [
    "default-src 'self'",
    "script-src 'self'",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: blob: https:",
    "font-src 'self' data:",
    `connect-src 'self' ${normalizedApiUrl}`,
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
  ].join("; ");
}

function buildConfig(mode: string): UserConfig & {
  test: {
    environment: string;
    setupFiles: string[];
    include: string[];
    hookTimeout: number;
    coverage: {
      provider: string;
      reporter: string[];
      reportsDirectory: string;
      include: string[];
      thresholds: Record<string, number>;
    };
  };
} {
  const env = loadEnv(mode, process.cwd(), "");
  const apiUrl = env.VITE_API_URL ?? "http://localhost:8000";

  const config = {
    plugins: [
      react(),
      {
        name: "inject-content-security-policy",
        apply: "build" as const,
        transformIndexHtml: () => [
          {
            tag: "meta",
            attrs: {
              "http-equiv": "Content-Security-Policy",
              content: buildContentSecurityPolicy(apiUrl),
            },
            injectTo: "head-prepend" as const,
          },
        ],
      },
    ],
    build: {
      rollupOptions: {
        output: {
          manualChunks: {
            react: ["react", "react-dom", "react-router-dom"],
            forms: ["react-hook-form", "@hookform/resolvers", "zod"],
            data: ["axios", "@tanstack/react-query", "react-helmet-async"],
            motion: ["framer-motion", "lucide-react"],
            radix: [
              "@radix-ui/react-accordion",
              "@radix-ui/react-checkbox",
              "@radix-ui/react-dialog",
              "@radix-ui/react-label",
              "@radix-ui/react-select",
              "@radix-ui/react-slot",
              "@radix-ui/react-toast",
            ],
          },
        },
      },
    },
    resolve: {
      alias: {
        "@": path.resolve(import.meta.dirname, "./src"),
      },
    },
    test: {
      environment: "./src/test/environments/jsdom-compat.ts",
      setupFiles: ["./src/test/setup.ts"],
      include: ["src/**/*.test.{ts,tsx}"],
      hookTimeout: 30_000,
      coverage: {
        provider: "v8",
        reporter: ["text", "html", "lcov", "json-summary"],
        reportsDirectory: "coverage",
        include: [
          "src/api/**/*.ts",
          "src/context/**/*.tsx",
          "src/hooks/*.ts",
          "src/lib/*.ts",
          "src/routes/**/*.tsx",
          "src/pages/dashboard/DashboardOverviewPage.tsx",
          "src/pages/dashboard/CollectorOverviewPage.tsx",
          "src/pages/dashboard/DealerOverviewPage.tsx",
          "src/pages/dashboard/AdminOverviewPage.tsx",
        ],
        thresholds: {
          lines: 80,
          functions: 80,
          statements: 80,
          branches: 80,
        },
      },
    },
  } satisfies UserConfig & {
    test: {
      environment: string;
      setupFiles: string[];
      include: string[];
      hookTimeout: number;
      coverage: {
        provider: string;
        reporter: string[];
        reportsDirectory: string;
        include: string[];
        thresholds: Record<string, number>;
      };
    };
  };

  return config;
}

export default defineConfig(({ mode }) => buildConfig(mode));
