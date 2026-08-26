import { describe, expect, it } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderApp, router } from "./test-utils";

describe("forgot password flow", () => {
  it("sends a reset link and shows the generic confirmation", async () => {
    const user = userEvent.setup();
    await renderApp("/forgot-password");

    expect(
      await screen.findByRole("heading", { name: /forgot your password/i }),
    ).toBeInTheDocument();

    await user.type(screen.getByLabelText("Email address"), "citizen@example.com");
    await user.click(screen.getByRole("button", { name: /send reset link/i }));

    expect(
      await screen.findByText(/If the email is registered, a password reset link has been sent/i),
    ).toBeInTheDocument();
  });

  it("shows the same confirmation for an unregistered email", async () => {
    const user = userEvent.setup();
    await renderApp("/forgot-password");

    await user.type(screen.getByLabelText("Email address"), "nobody-else@example.com");
    await user.click(screen.getByRole("button", { name: /send reset link/i }));

    expect(
      await screen.findByText(/If the email is registered, a password reset link has been sent/i),
    ).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("rejects an invalid email address before submitting", async () => {
    const user = userEvent.setup();
    await renderApp("/forgot-password");

    await user.type(screen.getByLabelText("Email address"), "not-an-email");
    await user.click(screen.getByRole("button", { name: /send reset link/i }));

    expect(await screen.findByText("Please enter a valid email address")).toBeInTheDocument();
    expect(screen.queryByText(/password reset link has been sent/i)).not.toBeInTheDocument();
  });

  it("shows a rate-limit message when requesting too often", async () => {
    const user = userEvent.setup();
    await renderApp("/forgot-password");

    await user.type(screen.getByLabelText("Email address"), "rate-limited@example.com");
    await user.click(screen.getByRole("button", { name: /send reset link/i }));

    expect(
      await screen.findByText(/Too many attempts. Please try again in about 5 minutes/i),
    ).toBeInTheDocument();
  });

  it("shows an error when the API fails", async () => {
    const user = userEvent.setup();
    await renderApp("/forgot-password");

    await user.type(screen.getByLabelText("Email address"), "network-error@example.com");
    await user.click(screen.getByRole("button", { name: /send reset link/i }));

    expect(await screen.findByRole("alert")).toBeInTheDocument();
    expect(screen.queryByText(/password reset link has been sent/i)).not.toBeInTheDocument();
  });

  it("links back to sign in from the success state", async () => {
    const user = userEvent.setup();
    await renderApp("/forgot-password");

    await user.type(screen.getByLabelText("Email address"), "citizen@example.com");
    await user.click(screen.getByRole("button", { name: /send reset link/i }));
    expect(
      await screen.findByText(/If the email is registered, a password reset link has been sent/i),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("link", { name: /back to sign in/i }));
    expect(await screen.findByRole("heading", { name: /welcome back/i })).toBeInTheDocument();
  });
});

describe("reset password flow", () => {
  it("resets the password from a valid link and offers sign in", async () => {
    const user = userEvent.setup();
    await renderApp("/reset-password?token=reset-token-1");

    expect(
      await screen.findByRole("heading", { name: /set a new password/i }),
    ).toBeInTheDocument();

    await user.type(screen.getByLabelText("New password"), "NewSecure123");
    await user.type(screen.getByLabelText("Confirm new password"), "NewSecure123");
    await user.click(screen.getByRole("button", { name: /^reset password$/i }));

    expect(
      await screen.findByRole("heading", { name: /password reset/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/has been reset successfully/i)).toBeInTheDocument();
  });

  it("navigates to login after a successful reset", async () => {
    const user = userEvent.setup();
    await renderApp("/reset-password?token=reset-token-1");

    await user.type(screen.getByLabelText("New password"), "NewSecure123");
    await user.type(screen.getByLabelText("Confirm new password"), "NewSecure123");
    await user.click(screen.getByRole("button", { name: /^reset password$/i }));

    const signIn = await screen.findAllByRole("link", { name: /^sign in$/i });
    await user.click(signIn[signIn.length - 1]);

    await waitFor(() => {
      expect(router.state.location.pathname).toBe("/login");
    });
    expect(await screen.findByRole("heading", { name: /welcome back/i })).toBeInTheDocument();
  });

  it("shows a client-side error when passwords do not match", async () => {
    const user = userEvent.setup();
    await renderApp("/reset-password?token=reset-token-1");

    await user.type(screen.getByLabelText("New password"), "NewSecure123");
    await user.type(screen.getByLabelText("Confirm new password"), "Different123");
    await user.click(screen.getByRole("button", { name: /^reset password$/i }));

    expect(await screen.findByText("Passwords do not match")).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: /password reset/i })).not.toBeInTheDocument();
  });

  it("requires at least 8 characters", async () => {
    const user = userEvent.setup();
    await renderApp("/reset-password?token=reset-token-1");

    await user.type(screen.getByLabelText("New password"), "short");
    await user.type(screen.getByLabelText("Confirm new password"), "short");
    await user.click(screen.getByRole("button", { name: /^reset password$/i }));

    expect(
      await screen.findByText("Password must be at least 8 characters"),
    ).toBeInTheDocument();
  });

  it("shows an error for an invalid or expired token", async () => {
    const user = userEvent.setup();
    await renderApp("/reset-password?token=reset-token-expired");

    await user.type(screen.getByLabelText("New password"), "NewSecure123");
    await user.type(screen.getByLabelText("Confirm new password"), "NewSecure123");
    await user.click(screen.getByRole("button", { name: /^reset password$/i }));

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(/Invalid or expired reset token|Unable to reset/i);
    expect(
      screen.queryByRole("heading", { name: /^password reset$/i }),
    ).not.toBeInTheDocument();
  });

  it("asks for a new link when the token is missing", async () => {
    const user = userEvent.setup();
    await renderApp("/reset-password");

    expect(await screen.findByRole("alert")).toHaveTextContent(
      /missing its token/i,
    );
    expect(
      screen.getByRole("link", { name: /request a new reset link/i }),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("link", { name: /request a new reset link/i }));
    expect(
      await screen.findByRole("heading", { name: /forgot your password/i }),
    ).toBeInTheDocument();
  });
});

describe("login page entry point", () => {
  it("links to the forgot-password page", async () => {
    const user = userEvent.setup();
    await renderApp("/login");

    expect(await screen.findByRole("heading", { name: /welcome back/i })).toBeInTheDocument();
    await user.click(screen.getByRole("link", { name: /forgot password\?/i }));

    await waitFor(() => {
      expect(router.state.location.pathname).toBe("/forgot-password");
    });
    expect(
      await screen.findByRole("heading", { name: /forgot your password/i }),
    ).toBeInTheDocument();
  });
});
