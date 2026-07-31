import { describe, expect, it } from "vitest";
import { http, HttpResponse } from "msw";
import { screen, within } from "@testing-library/react";
import { server } from "./server";
import { renderApp, storeValidSession } from "./test-utils";

describe("citizen dashboard", () => {
  it("renders the greeting, summary stats, and pickup cards from mocked data", async () => {
    storeValidSession("citizen");
    await renderApp("/dashboard/overview");

    expect(await screen.findByText(/Hello, Test Citizen/)).toBeInTheDocument();

    const stats = screen.getByText("Total Requests").closest("div") as HTMLElement;
    expect(within(stats.parentElement as HTMLElement).getByText("5")).toBeInTheDocument();
    expect(screen.getAllByText("Pending").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Completed").length).toBeGreaterThan(0);

    expect(screen.getAllByText("Plastic bottles").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Request #1").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Request #2").length).toBeGreaterThan(0);
    expect(screen.getByRole("link", { name: /view details/i })).toBeInTheDocument();
  });
});

describe("collector dashboard", () => {
  it("renders available request stats and queue from mocked data", async () => {
    storeValidSession("collector");
    await renderApp("/collector/overview");

    expect(
      await screen.findByRole("heading", { name: "Available Pickup Requests" }),
    ).toBeInTheDocument();

    expect(screen.getByText("Available Now")).toBeInTheDocument();
    expect(screen.getByText("Cardboard")).toBeInTheDocument();
    expect(screen.getByText("Glass bottles")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /refresh/i })).toBeInTheDocument();
  });

  it("shows the empty state when no requests are available", async () => {
    server.use(
      http.get("*/collector/pickups/available", () => HttpResponse.json([])),
    );
    storeValidSession("collector");
    await renderApp("/collector/overview");

    expect(
      await screen.findByText("No pickup requests are available"),
    ).toBeInTheDocument();
  });
});

describe("dealer dashboard", () => {
  it("renders marketplace lots and stats from mocked data", async () => {
    storeValidSession("dealer");
    await renderApp("/dealer/overview");

    expect(
      await screen.findByRole("heading", { name: "Available Inventory" }),
    ).toBeInTheDocument();

    expect(screen.getByText("Available Lots")).toBeInTheDocument();
    expect(screen.getByText("Plastic")).toBeInTheDocument();
    expect(screen.getByText("Kolkata")).toBeInTheDocument();
    expect(screen.getAllByText("42.5 kg").length).toBeGreaterThan(0);
    expect(screen.getByText(/Showing 1 lots across 1 city/i)).toBeInTheDocument();
  });
});

describe("admin dashboard", () => {
  it("renders analytics, newest users, and dealer review queue from mocked data", async () => {
    storeValidSession("admin");
    await renderApp("/admin/overview");

    expect(
      await screen.findByRole("heading", { name: "Platform Overview" }),
    ).toBeInTheDocument();

    expect(screen.getByText("Total Users")).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument();
    expect(screen.getByText("150")).toBeInTheDocument();

    expect(screen.getByText("Green Scrap Co")).toBeInTheDocument();
    expect(screen.getAllByText("pending").length).toBeGreaterThan(0);

    expect(screen.getByText("Test Citizen")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /refresh/i })).toBeInTheDocument();
  });
});
