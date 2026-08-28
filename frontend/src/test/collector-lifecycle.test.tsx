import { beforeEach, describe, expect, it } from "vitest";
import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderApp, storeValidSession } from "./test-utils";
import { resetPickupStore } from "./handlers";

describe("collector pickup lifecycle", () => {
  beforeEach(() => {
    resetPickupStore();
  });

  it("renders summary stats, available queue, and active pickups", async () => {
    storeValidSession("collector");
    await renderApp("/collector/overview");

    expect(
      await screen.findByRole("heading", { name: "Available Pickup Requests" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Available Now")).toBeInTheDocument();
    expect(screen.getByText("Total Assigned")).toBeInTheDocument();
    expect(screen.getByText("Active Jobs")).toBeInTheDocument();
    expect(screen.getByText("Completed Jobs")).toBeInTheDocument();

    const queue = screen.getByText("Collector Queue").closest("section") as HTMLElement;
    expect(within(queue).getByText("Cardboard")).toBeInTheDocument();
    expect(within(queue).getByText("Glass bottles")).toBeInTheDocument();
    expect(within(queue).getAllByRole("button", { name: "Accept Request" }).length).toBe(2);

    const active = screen.getByText("My Active Pickups").closest("section") as HTMLElement;
    expect(within(active).getByText("Paper")).toBeInTheDocument();
    expect(within(active).getByRole("button", { name: "Start Trip" })).toBeInTheDocument();
  });

  it("accepts a request and moves it to the active pickups list", async () => {
    const user = userEvent.setup();
    storeValidSession("collector");
    await renderApp("/collector/overview");

    const queue = (await screen.findByText("Collector Queue")).closest("section") as HTMLElement;
    const acceptButtons = within(queue).getAllByRole("button", { name: "Accept Request" });
    await user.click(acceptButtons[0]);

    const active = await screen.findByText("My Active Pickups");
    const activeSection = active.closest("section") as HTMLElement;
    expect(await within(activeSection).findByText("Cardboard")).toBeInTheDocument();
    expect(
      within(activeSection).getAllByRole("button", { name: "Start Trip" }).length,
    ).toBeGreaterThanOrEqual(2);
  });

  it("starts, collects, and records weight — then shows awaiting confirmation state", async () => {
    const user = userEvent.setup();
    storeValidSession("collector");
    await renderApp("/collector/pickups/5");

    expect(
      await screen.findByRole("heading", { name: "Pickup Request #5" }),
    ).toBeInTheDocument();
    expect(screen.getAllByText("Paper").length).toBeGreaterThan(0);
    expect(screen.getByText("Status Timeline")).toBeInTheDocument();
    expect(screen.getAllByText(/accepted/i).length).toBeGreaterThan(0);

    await user.click(screen.getByRole("button", { name: "Start Trip" }));
    await user.click(screen.getByRole("button", { name: "Mark as Collected" }));
    await user.click(screen.getByRole("button", { name: "Record Weight" }));

    const weightInput = screen.getByPlaceholderText(/e\.g\. 12\.5/i);
    await user.type(weightInput, "14.5");
    await user.click(screen.getByRole("button", { name: "Confirm Weight" }));

    await screen.findByText("14.5 kg");
    await screen.findByText(/awaiting citizen confirmation/i);
    expect(screen.queryByRole("button", { name: "Record Weight" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Mark as Completed" })).not.toBeInTheDocument();
  });

  it("releases an accepted request back to the available queue", async () => {
    const user = userEvent.setup();
    storeValidSession("collector");
    await renderApp("/collector/pickups/5");

    expect(
      await screen.findByRole("heading", { name: "Pickup Request #5" }),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Release Request" }));
    await user.click(screen.getByRole("button", { name: "Yes, Release" }));

    expect(await screen.findByText("Status Timeline")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Accept Request" })).toBeInTheDocument();
  });

  it("renders accept-only actions for a pending request", async () => {
    storeValidSession("collector");
    await renderApp("/collector/pickups/3");

    expect(
      await screen.findByRole("heading", { name: "Pickup Request #3" }),
    ).toBeInTheDocument();

    expect(screen.getByRole("button", { name: "Accept Request" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Start Trip" })).not.toBeInTheDocument();
  });
});
