import { describe, expect, it } from "vitest";
import { cleanup, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderApp, router, storeValidSession } from "./test-utils";

describe("email verification flow", () => {
  it("verifies an email from a valid link and shows the success message", async () => {
    await renderApp("/verify-email?token=verification-token-1");

    expect(await screen.findByRole("heading", { name: "Email verified" })).toBeInTheDocument();
    expect(screen.getByText("Email verified successfully")).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: /sign in/i }).length).toBeGreaterThan(0);
  });

  it("is idempotent when the email is already verified", async () => {
    storeValidSession("citizen");
    await renderApp("/verify-email?token=verification-token-1");

    expect(await screen.findByRole("heading", { name: "Email verified" })).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText("Email verified successfully")).toBeInTheDocument();
    });

    // Re-presenting the same token on a fresh page load must be idempotent.
    cleanup();
    await renderApp("/verify-email?token=verification-token-1");

    expect(
      await screen.findByRole("heading", { name: "Email already verified" }),
    ).toBeInTheDocument();
    expect(screen.getAllByText("Email already verified").length).toBeGreaterThan(1);
  });

  it("shows a resend form for an invalid or expired link", async () => {
    await renderApp("/verify-email?token=not-a-valid-token");

    expect(await screen.findByRole("heading", { name: "Verify your email" })).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent(
      "This verification link is invalid or expired",
    );
    expect(screen.getByLabelText("Email address")).toBeInTheDocument();
  });

  it("shows the resend form when no token is present", async () => {
    await renderApp("/verify-email");

    expect(await screen.findByRole("heading", { name: "Verify your email" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /resend verification email/i })).toBeInTheDocument();
  });

  it("resends a verification email and confirms the generic message", async () => {
    const user = userEvent.setup();
    await renderApp("/verify-email");

    await user.type(screen.getByLabelText("Email address"), "new@example.com");
    await user.click(screen.getByRole("button", { name: /resend verification email/i }));

    expect(await screen.findByText(/If the email is registered and unverified/i)).toBeInTheDocument();
  });

  it("shows a rate-limit message when resending too often", async () => {
    const user = userEvent.setup();
    await renderApp("/verify-email");

    await user.type(screen.getByLabelText("Email address"), "rate-limited@example.com");
    await user.click(screen.getByRole("button", { name: /resend verification email/i }));

    expect(
      await screen.findByText(/Too many attempts. Please try again in about 5 minutes/i),
    ).toBeInTheDocument();
  });

  it("shows the verification banner in the dashboard for unverified users", async () => {
    storeValidSession("citizen");
    await renderApp("/dashboard/overview");

    expect(
      await screen.findByText(/Your email address is not verified yet/i),
    ).toBeInTheDocument();
  });

  it("resends the verification email from the dashboard banner", async () => {
    const user = userEvent.setup();
    storeValidSession("citizen");
    await renderApp("/dashboard/overview");

    await user.click(
      screen.getByRole("button", { name: /resend verification email/i }),
    );

    expect(
      await screen.findByText(/If the email is registered and unverified/i),
    ).toBeInTheDocument();
  });

  it("removes the dashboard banner after verifying while logged in", async () => {
    storeValidSession("citizen");
    await renderApp("/dashboard/overview");

    expect(
      await screen.findByText(/Your email address is not verified yet/i),
    ).toBeInTheDocument();

    await router.navigate("/verify-email?token=verification-token-1");
    expect(await screen.findByRole("heading", { name: "Email verified" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /go to dashboard/i })).toBeInTheDocument();

    await router.navigate("/dashboard/overview");

    await waitFor(() => {
      expect(
        screen.queryByText(/Your email address is not verified yet/i),
      ).not.toBeInTheDocument();
    });
  });
});