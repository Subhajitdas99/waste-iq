import { describe, expect, it } from "vitest";
import { http, HttpResponse } from "msw";
import { QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { server } from "./server";
import {
  createAnalyticsOverview,
  createCarbonSavings,
  createMaterialBreakdown,
  createMonthlyAnalytics,
} from "./factories";
import {
  createTestQueryClient,
  renderApp,
  storeValidSession,
} from "./test-utils";
import { useAnalyticsOverview } from "@/hooks/useAnalytics";

describe("AI analytics dashboard", () => {
  it("renders KPIs, trends, material, performance and carbon sections", async () => {
    storeValidSession("admin");
    await renderApp("/admin/analytics");

    expect(
      await screen.findByRole(
        "heading",
        { name: "AI Analytics Dashboard" },
        { timeout: 5000 },
      ),
    ).toBeInTheDocument();

    expect(
      await screen.findByText("Total Users", {}, { timeout: 5000 }),
    ).toBeInTheDocument();
    expect(screen.getByText("1,248")).toBeInTheDocument();
    expect(screen.getByText("Completion Rate")).toBeInTheDocument();
    expect(screen.getByText("87.2%")).toBeInTheDocument();
    expect(screen.getByText("18920.5 kg")).toBeInTheDocument();

    expect(
      screen.getByRole("heading", { name: "Monthly Pickup Trend" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Completed")).toBeInTheDocument();
    expect(screen.getAllByText("Total Pickups").length).toBeGreaterThan(0);

    expect(
      screen.getByRole("heading", { name: "Material Distribution" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Plastic")).toBeInTheDocument();

    expect(
      screen.getByRole("heading", { name: "Collector Performance" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Priya Sharma")).toBeInTheDocument();
    expect(screen.getByText("92.3%")).toBeInTheDocument();

    expect(
      screen.getByRole("heading", { name: "Dealer Performance" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Green Scrap Co")).toBeInTheDocument();
    expect(screen.getByText("2140.5 kg")).toBeInTheDocument();

    expect(
      screen.getByRole("heading", { name: "Carbon Savings" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Estimated CO₂ Saved")).toBeInTheDocument();
    expect(screen.getByText("7,946.6 kg")).toBeInTheDocument();
    expect(screen.getByText("Trees Equivalent")).toBeInTheDocument();

    expect(
      screen.getByRole("heading", { name: "Recent Analytics" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Most Recycled Material")).toBeInTheDocument();
    expect(
      screen.getByText(/Plastic is the most recycled material/),
    ).toBeInTheDocument();
    expect(screen.getByText("Pickup Completion Trend")).toBeInTheDocument();
  });

  it("shows empty states when there is no platform activity", async () => {
    server.use(
      http.get("*/admin/analytics/overview", () =>
        HttpResponse.json(createAnalyticsOverview()),
      ),
      http.get("*/admin/analytics/monthly", () =>
        HttpResponse.json(
          createMonthlyAnalytics().map((entry) => ({
            ...entry,
            pickup_count: 0,
            completed: 0,
            weight: 0,
          })),
        ),
      ),
      http.get("*/admin/analytics/materials", () =>
        HttpResponse.json(
          createMaterialBreakdown({
            plastic: 0,
            paper: 0,
            metal: 0,
            glass: 0,
            e_waste: 0,
            organic: 0,
            other: 0,
          }),
        ),
      ),
      http.get("*/admin/analytics/collectors", () => HttpResponse.json([])),
      http.get("*/admin/analytics/dealers", () => HttpResponse.json([])),
      http.get("*/admin/analytics/carbon", () =>
        HttpResponse.json(
          createCarbonSavings({
            estimated_co2_saved: 0,
            trees_equivalent: 0,
            plastic_recycled: 0,
            paper_recycled: 0,
          }),
        ),
      ),
      http.get("*/admin/analytics/insights", () => HttpResponse.json([])),
    );
    storeValidSession("admin");
    await renderApp("/admin/analytics");

    expect(
      await screen.findByText(
        "No pickup activity in the last 12 months.",
        {},
        { timeout: 5000 },
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Material distribution appears once completed pickups/),
    ).toBeInTheDocument();
    expect(screen.getByText("No collector activity")).toBeInTheDocument();
    expect(screen.getByText("No dealer activity")).toBeInTheDocument();
    expect(
      screen.getByText(/Carbon savings appear once completed pickups/),
    ).toBeInTheDocument();
    expect(screen.getByText("No insights yet")).toBeInTheDocument();
  });

  it("shows an error state when an analytics endpoint fails", async () => {
    server.use(
      http.get("*/admin/analytics/overview", () =>
        HttpResponse.json(
          { detail: "Analytics unavailable" },
          { status: 503 },
        ),
      ),
    );
    storeValidSession("admin");
    await renderApp("/admin/analytics");

    const alerts = await screen.findAllByRole("alert");
    expect(
      alerts.some((alert) => alert.textContent?.includes("Analytics unavailable")),
    ).toBe(true);
  });
});

describe("useAnalytics hooks", () => {
  it("loads the overview through useAnalyticsOverview", async () => {
    function OverviewHarness() {
      const query = useAnalyticsOverview();
      return (
        <p data-testid="overview">
          {query.data
            ? `${query.data.total_users}-${query.data.completed_rate}`
            : query.isPending
              ? "loading"
              : "error"}
        </p>
      );
    }

    render(
      <QueryClientProvider client={createTestQueryClient()}>
        <OverviewHarness />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("overview")).toHaveTextContent("1248-87.19");
    });
  });
});
