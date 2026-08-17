import { describe, expect, it, vi } from "vitest";
import { http, HttpResponse } from "msw";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Toast } from "@/components/Toast";
import { LoadingScreen, Spinner } from "@/components/ui/spinner";
import { server } from "./server";
import { renderApp, storeValidSession } from "./test-utils";

describe("loading states", () => {
  it("exposes the full-page loading screen with a status role and label", () => {
    render(<LoadingScreen />);

    expect(screen.getByRole("status", { name: "Loading Waste-IQ" })).toBeInTheDocument();
    expect(screen.getByText("Loading Waste-IQ...")).toBeInTheDocument();
  });

  it("exposes inline spinners with a status role and custom label", () => {
    render(<Spinner size={18} label="Signing in" />);

    expect(screen.getByRole("status", { name: "Signing in" })).toBeInTheDocument();
  });

  it("shows the loading spinner inside the login button while submitting", async () => {
    server.use(
      http.post("*/auth/login", async () => {
        await new Promise((resolve) => setTimeout(resolve, 50));
        return HttpResponse.json({
          access_token: "token",
          token_type: "bearer",
          user: { id: 1, name: "Test Citizen", email: "c@example.com", phone: "1", role: "citizen" },
        });
      }),
    );
    const user = userEvent.setup();
    await renderApp("/login");

    await user.type(screen.getByLabelText("Email address"), "citizen@example.com");
    await user.type(screen.getByLabelText("Password"), "correct-password");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    expect(screen.getByRole("status", { name: "Loading" })).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.queryByRole("status", { name: "Loading" })).not.toBeInTheDocument();
    });
  });
});

describe("error messages", () => {
  it("renders failed login errors with an alert role", async () => {
    const user = userEvent.setup();
    await renderApp("/login");

    await user.type(screen.getByLabelText("Email address"), "citizen@example.com");
    await user.type(screen.getByLabelText("Password"), "wrong-password");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("Invalid email or password");
  });

  it("renders dashboard query failures with an alert role and a retry action", async () => {
    server.use(
      http.get("*/pickup-requests", () =>
        HttpResponse.json({ detail: "Server exploded" }, { status: 500 }),
      ),
    );
    storeValidSession("citizen");
    await renderApp("/dashboard/overview");

    await screen.findByRole("button", { name: /try again/i });
    expect(screen.getAllByText("Server exploded").length).toBeGreaterThan(0);
  });
});

describe("toast notifications", () => {
  it("announces error toasts with an assertive live region", () => {
    render(<Toast message="Something went wrong" type="error" onDismiss={() => undefined} />);

    const toast = screen.getByRole("alert");
    expect(toast).toHaveAttribute("aria-live", "assertive");
    expect(toast).toHaveAttribute("aria-atomic", "true");
    expect(toast).toHaveTextContent("Something went wrong");
  });

  it("announces informational toasts with a polite live region", () => {
    render(<Toast message="Saved successfully" type="success" />);

    const toast = screen.getByRole("status");
    expect(toast).toHaveAttribute("aria-live", "polite");
  });

  it("dismisses the toast via its labelled close button", async () => {
    const onDismiss = vi.fn();
    const user = userEvent.setup();
    render(<Toast message="Dismiss me" type="error" onDismiss={onDismiss} />);

    await user.click(screen.getByRole("button", { name: "Dismiss notification" }));

    expect(onDismiss).toHaveBeenCalledTimes(1);
  });

  it("shows a global error toast when a query fails", async () => {
    server.use(
      http.get("*/admin/analytics", () =>
        HttpResponse.json({ detail: "Analytics unavailable" }, { status: 500 }),
      ),
    );
    storeValidSession("admin");
    await renderApp("/admin/overview");

    const dismissButton = await screen.findByRole("button", { name: "Dismiss notification" });
    expect(dismissButton).toBeInTheDocument();
    expect(screen.getAllByText("Analytics unavailable").length).toBeGreaterThan(0);
  });
});

describe("ARIA labels", () => {
  it("labels the password visibility toggle and toggles on click", async () => {
    const user = userEvent.setup();
    await renderApp("/login");

    const toggle = screen.getByRole("button", { name: "Show password" });
    expect(toggle).toBeInTheDocument();

    await user.click(toggle);

    expect(screen.getByRole("button", { name: "Hide password" })).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toHaveAttribute("type", "text");
  });

  it("labels the dashboard navigation landmark", async () => {
    storeValidSession("citizen");
    await renderApp("/dashboard/overview");

    expect(
      await screen.findByRole("navigation", { name: "Dashboard navigation" }),
    ).toBeInTheDocument();
  });

  it("labels the mobile dashboard navigation toggle", async () => {
    storeValidSession("citizen");
    await renderApp("/dashboard/overview");

    expect(
      await screen.findByRole("button", { name: "Open dashboard navigation" }),
    ).toBeInTheDocument();
  });

  it("labels the theme toggle with its current action", async () => {
    storeValidSession("citizen");
    await renderApp("/dashboard/overview");

    expect(
      await screen.findByRole("button", { name: "Switch to dark mode" }),
    ).toBeInTheDocument();
  });
});
