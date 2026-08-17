import { describe, expect, it } from "vitest";
import { http, HttpResponse } from "msw";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { server } from "./server";
import { renderApp, storeRawToken, storeValidSession } from "./test-utils";
import { EXPIRED_TOKEN, MALFORMED_TOKEN } from "./factories";
import { TOKEN_STORAGE_KEY } from "@/lib/constants";

async function fillLoginForm(
  user: ReturnType<typeof userEvent.setup>,
  email = "citizen@example.com",
  password = "correct-password",
) {
  await user.type(screen.getByLabelText("Email address"), email);
  await user.type(screen.getByLabelText("Password"), password);
  await user.click(screen.getByRole("button", { name: /sign in/i }));
}

describe("authentication flow", () => {
  it("logs in successfully and redirects to the citizen dashboard", async () => {
    const user = userEvent.setup();
    await renderApp("/login");

    await user.click(screen.getByRole("checkbox", { name: /remember me/i }));
    await fillLoginForm(user);

    expect(await screen.findByRole("heading", { name: "Dashboard Overview" })).toBeInTheDocument();
    expect(await screen.findByText(/Hello, Test Citizen/)).toBeInTheDocument();
    expect(window.localStorage.getItem(TOKEN_STORAGE_KEY)).not.toBeNull();
  });

  it("redirects a dealer login to the dealer portal", async () => {
    const user = userEvent.setup();
    await renderApp("/login");

    await fillLoginForm(user, "dealer@example.com");

    expect(await screen.findByRole("heading", { name: "Available Inventory" })).toBeInTheDocument();
  });

  it("shows an error alert on failed login and stays on the login page", async () => {
    const user = userEvent.setup();
    await renderApp("/login");

    await fillLoginForm(user, "citizen@example.com", "wrong-password");

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("Invalid email or password");
    expect(screen.getByRole("heading", { name: "Welcome back" })).toBeInTheDocument();
    expect(window.localStorage.getItem(TOKEN_STORAGE_KEY)).toBeNull();
  });

  it("registers an account and redirects to login with a success banner", async () => {
    const user = userEvent.setup();
    await renderApp("/register");

    await user.type(screen.getByLabelText("Full Name"), "New Citizen");
    await user.type(screen.getByLabelText("Email address"), "new@example.com");
    await user.type(screen.getByLabelText("Phone"), "+15551234567");
    await user.type(screen.getByLabelText("Password"), "strong-password");
    await user.type(screen.getByLabelText("Confirm Password"), "strong-password");
    await user.click(screen.getByText(/Accept terms and conditions/));
    await user.click(screen.getByRole("button", { name: /create account/i }));

    expect(
      await screen.findByText("Account created successfully. Please sign in."),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Welcome back" })).toBeInTheDocument();
  });

  it("shows inline validation errors when the registration form is invalid", async () => {
    const user = userEvent.setup();
    await renderApp("/register");

    await user.click(screen.getByRole("button", { name: /create account/i }));

    expect(await screen.findByText("Full name must be at least 2 characters")).toBeInTheDocument();
    expect(screen.getByText("Please enter a valid email address")).toBeInTheDocument();
    expect(screen.getByText("Phone must be at least 8 characters")).toBeInTheDocument();
    expect(screen.getByText("Password must be at least 8 characters")).toBeInTheDocument();
    expect(screen.getByText("You must accept the terms and conditions")).toBeInTheDocument();
    expect(window.localStorage.getItem(TOKEN_STORAGE_KEY)).toBeNull();
  });

  it("requires an admin registration code when the admin role is selected", async () => {
    const user = userEvent.setup();
    await renderApp("/register");

    await user.selectOptions(screen.getByLabelText("Account Type"), "admin");
    await user.click(screen.getByRole("button", { name: /create account/i }));

    expect(await screen.findByText("Admin registration code is required")).toBeInTheDocument();
  });

  it("logs out and clears the stored session", async () => {
    const user = userEvent.setup();
    storeValidSession("citizen");
    await renderApp("/dashboard/overview");

    expect(await screen.findByText(/Hello, Test Citizen/)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /logout/i }));

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Welcome back" })).toBeInTheDocument();
    });
    expect(window.localStorage.getItem(TOKEN_STORAGE_KEY)).toBeNull();
    expect(window.sessionStorage.getItem(TOKEN_STORAGE_KEY)).toBeNull();
  });

  it("restores the session from storage by fetching the profile", async () => {
    storeValidSession("citizen");
    await renderApp("/dashboard/overview");

    expect(await screen.findByText(/Hello, Test Citizen/)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Dashboard Overview" })).toBeInTheDocument();
  });

  it("treats an expired JWT as logged out and clears storage", async () => {
    storeRawToken(EXPIRED_TOKEN);
    await renderApp("/dashboard/overview");

    expect(await screen.findByRole("heading", { name: "Welcome back" })).toBeInTheDocument();
    expect(window.localStorage.getItem(TOKEN_STORAGE_KEY)).toBeNull();
  });

  it("treats a malformed JWT as logged out and clears storage", async () => {
    storeRawToken(MALFORMED_TOKEN);
    await renderApp("/dashboard/overview");

    expect(await screen.findByRole("heading", { name: "Welcome back" })).toBeInTheDocument();
    expect(window.localStorage.getItem(TOKEN_STORAGE_KEY)).toBeNull();
  });

  it("logs out and redirects when the profile request returns 401", async () => {
    server.use(
      http.get("*/auth/me", () =>
        HttpResponse.json({ detail: "Not authenticated" }, { status: 401 }),
      ),
    );
    storeValidSession("citizen");
    await renderApp("/dashboard/overview");

    expect(await screen.findByRole("heading", { name: "Welcome back" })).toBeInTheDocument();
    expect(window.localStorage.getItem(TOKEN_STORAGE_KEY)).toBeNull();
  });
});
