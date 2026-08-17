import { afterEach, describe, expect, it } from "vitest";
import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { server } from "./server";
import { renderApp, storeValidSession } from "./test-utils";
import { collectorLocationStore, resetCollectorMapStore } from "./handlers";

function stubGeolocation(success: { latitude: number; longitude: number }) {
  Object.defineProperty(navigator, "geolocation", {
    configurable: true,
    value: {
      getCurrentPosition: (onSuccess: PositionCallback) => {
        onSuccess({
          coords: { latitude: success.latitude, longitude: success.longitude },
          timestamp: Date.now(),
        } as GeolocationPosition);
      },
    },
  });
}

describe("collector live map & route tracking", () => {
  afterEach(() => {
    Reflect.deleteProperty(navigator, "geolocation");
    resetCollectorMapStore();
  });

  it("renders the map with collector, pickup markers, route, and nearby pickups", async () => {
    storeValidSession("collector");
    await renderApp("/collector/map");

    expect(
      await screen.findByRole("heading", { name: "Live Map & Route Tracking" }),
    ).toBeInTheDocument();

    expect(await screen.findByTestId("collector-map")).toBeInTheDocument();
    expect(screen.getByTestId("collector-marker")).toBeInTheDocument();
    expect(screen.getByTestId("pickup-marker-3")).toBeInTheDocument();
    expect(screen.getByTestId("pickup-marker-5")).toBeInTheDocument();

    const route = await screen.findByTestId("route-summary");
    expect(within(route).getAllByText(/min ETA/).length).toBeGreaterThan(0);
    expect(within(route).getByText(/km/)).toBeInTheDocument();

    const nearby = screen.getByTestId("nearby-pickups");
    expect(within(nearby).getByText("Cardboard")).toBeInTheDocument();
    expect(within(nearby).getByText("Glass bottles")).toBeInTheDocument();
  });

  it("reports a live position via the Use my location action", async () => {
    stubGeolocation({ latitude: 22.52, longitude: 88.35 });
    const user = userEvent.setup();
    storeValidSession("collector");
    await renderApp("/collector/map");

    const status = await screen.findByTestId("location-status");
    expect(within(status).getByText(/22.5726/)).toBeInTheDocument();

    await user.click(within(status).getByRole("button", { name: /Use my location/i }));

    expect(await within(status).findByText(/22.52000/)).toBeInTheDocument();
    expect(collectorLocationStore.latitude).toBeCloseTo(22.52, 2);
    expect(collectorLocationStore.longitude).toBeCloseTo(88.35, 2);
  });

  it("opens navigation for a nearby pickup", async () => {
    const user = userEvent.setup();
    storeValidSession("collector");
    await renderApp("/collector/map");

    const nearby = await screen.findByTestId("nearby-pickups");
    await user.click(within(nearby).getByTestId("nearby-navigate-3"));

    expect(await screen.findByTestId("navigation-panel")).toBeInTheDocument();
    expect(screen.getByTestId("navigation-polyline")).toBeInTheDocument();
    expect(screen.getByText(/Navigation to Cardboard/)).toBeInTheDocument();
    expect(screen.getByText(/2\.10 km/)).toBeInTheDocument();
  });

  it("shows a permission error when the map endpoint is forbidden", async () => {
    server.use(
      http.get("*/collector/map", () => HttpResponse.json({ detail: "Forbidden" }, { status: 403 })),
    );
    storeValidSession("collector");
    await renderApp("/collector/map");

    expect(await screen.findByText(/do not have permission/i)).toBeInTheDocument();
    expect(screen.queryByTestId("collector-map")).not.toBeInTheDocument();
  });
});