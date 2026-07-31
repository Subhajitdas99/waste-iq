import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import { renderApp, storeValidSession } from "./test-utils";

describe("protected routes", () => {
  it("redirects a guest away from the citizen dashboard to the login page", async () => {
    await renderApp("/dashboard/overview");

    expect(await screen.findByRole("heading", { name: "Welcome back" })).toBeInTheDocument();
    expect(window.location.pathname).toBe("/login");
  });

  it("redirects a guest away from the admin dashboard to the login page", async () => {
    await renderApp("/admin/overview");

    expect(await screen.findByRole("heading", { name: "Welcome back" })).toBeInTheDocument();
    expect(window.location.pathname).toBe("/login");
  });

  it("allows a citizen into the citizen dashboard", async () => {
    storeValidSession("citizen");
    await renderApp("/dashboard/overview");

    expect(await screen.findByRole("heading", { name: "Dashboard Overview" })).toBeInTheDocument();
  });

  it("allows a collector into the collector dashboard", async () => {
    storeValidSession("collector");
    await renderApp("/collector/overview");

    expect(
      await screen.findByRole("heading", { name: "Available Pickup Requests" }),
    ).toBeInTheDocument();
  });

  it("allows a dealer into the dealer dashboard", async () => {
    storeValidSession("dealer");
    await renderApp("/dealer/overview");

    expect(await screen.findByRole("heading", { name: "Available Inventory" })).toBeInTheDocument();
  });

  it("allows an admin into the admin dashboard", async () => {
    storeValidSession("admin");
    await renderApp("/admin/overview");

    expect(await screen.findByRole("heading", { name: "Platform Overview" })).toBeInTheDocument();
  });

  it("sends a citizen trying to access the admin portal to the unauthorized page", async () => {
    storeValidSession("citizen");
    await renderApp("/admin/overview");

    expect(await screen.findByRole("heading", { name: "Access Denied" })).toBeInTheDocument();
    expect(window.location.pathname).toBe("/unauthorized");
  });

  it("sends a dealer trying to access the citizen portal to the unauthorized page", async () => {
    storeValidSession("dealer");
    await renderApp("/dashboard/overview");

    expect(await screen.findByRole("heading", { name: "Access Denied" })).toBeInTheDocument();
  });

  it("lets an authenticated user reach the unauthorized page directly", async () => {
    storeValidSession("admin");
    await renderApp("/unauthorized");

    expect(await screen.findByRole("heading", { name: "Access Denied" })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Open Admin Portal/i }),
    ).toBeInTheDocument();
  });

  it("shows the login page to guests on /login", async () => {
    await renderApp("/login");

    expect(await screen.findByRole("heading", { name: "Welcome back" })).toBeInTheDocument();
    expect(window.location.pathname).toBe("/login");
  });

  it("redirects an authenticated citizen away from /login to their dashboard", async () => {
    storeValidSession("citizen");
    await renderApp("/login");

    expect(await screen.findByRole("heading", { name: "Dashboard Overview" })).toBeInTheDocument();
  });

  it("shows the 404 page for unknown routes to guests", async () => {
    await renderApp("/this-route-does-not-exist");

    expect(await screen.findByRole("heading", { name: "Page Not Found" })).toBeInTheDocument();
  });
});
