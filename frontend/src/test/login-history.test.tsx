import { describe, expect, it, vi } from "vitest";
import { http, HttpResponse, delay } from "msw";
import { screen, waitFor } from "@testing-library/react";
import { server } from "./server";
import { renderApp, storeValidSession } from "./test-utils";
import { getLoginHistory } from "@/api/auth";

const loginHistoryResponse = {
  items: [
    {
      id: 101,
      outcome: "success" as const,
      ip_address: "203.0.113.42",
      user_agent: "Mozilla/5.0 Chrome Waste-IQ",
      created_at: "2026-01-14T12:00:00Z",
    },
    {
      id: 102,
      outcome: "failure" as const,
      ip_address: "198.51.100.21",
      user_agent: "Safari on iPhone",
      created_at: "2026-01-13T09:30:00Z",
    },
  ],
  page: 1,
  page_size: 10,
  total_items: 2,
  total_pages: 1,
};

describe("login history API", () => {
  it("uses GET /auth/login-history without identity parameters", async () => {
    const requestSpy = vi.fn();

    server.use(
      http.get("*/auth/login-history", ({ request }) => {
        const url = new URL(request.url);
        requestSpy({
          method: request.method,
          pathname: url.pathname,
          page: url.searchParams.get("page"),
          pageSize: url.searchParams.get("page_size"),
          userId: url.searchParams.get("user_id"),
          actorUserId: url.searchParams.get("actor_user_id"),
        });

        return HttpResponse.json(loginHistoryResponse);
      }),
    );

    storeValidSession("citizen");
    const history = await getLoginHistory();

    expect(history.items).toHaveLength(2);
    expect(requestSpy).toHaveBeenCalledWith({
      method: "GET",
      pathname: "/auth/login-history",
      page: "1",
      pageSize: "10",
      userId: null,
      actorUserId: null,
    });
  });
});

describe("Recent logins settings card", () => {
  it("renders the card heading", async () => {
    storeValidSession("citizen");
    await renderApp("/dashboard/settings");

    expect(
      await screen.findByRole("heading", { name: "Recent logins" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Review recent sign-ins to your Waste-IQ account."),
    ).toBeInTheDocument();
  });

  it("renders the loading state", async () => {
    server.use(
      http.get("*/auth/login-history", async () => {
        await delay(100);
        return HttpResponse.json(loginHistoryResponse);
      }),
    );

    storeValidSession("citizen");
    await renderApp("/dashboard/settings");

    expect(screen.getByLabelText("Recent logins loading")).toBeInTheDocument();
  });

  it("renders successful and failed login entries with IP and device details", async () => {
    server.use(
      http.get("*/auth/login-history", () => HttpResponse.json(loginHistoryResponse)),
    );

    storeValidSession("citizen");
    await renderApp("/dashboard/settings");

    expect(await screen.findByText("Successful login")).toBeInTheDocument();
    expect(screen.getByText("Failed login")).toBeInTheDocument();
    expect(screen.getByText("203.0.113.42")).toBeInTheDocument();
    expect(screen.getByText("198.51.100.21")).toBeInTheDocument();
    expect(screen.getByText("Mozilla/5.0 Chrome Waste-IQ")).toBeInTheDocument();
    expect(screen.getByText("Safari on iPhone")).toBeInTheDocument();
  });

  it("renders an empty history state", async () => {
    server.use(
      http.get("*/auth/login-history", () =>
        HttpResponse.json({
          items: [],
          page: 1,
          page_size: 10,
          total_items: 0,
          total_pages: 0,
        }),
      ),
    );

    storeValidSession("citizen");
    await renderApp("/dashboard/settings");

    expect(await screen.findByText("No recent login activity.")).toBeInTheDocument();
  });

  it("renders a friendly API error state", async () => {
    server.use(
      http.get("*/auth/login-history", () =>
        HttpResponse.json({ detail: "Internal server error" }, { status: 500 }),
      ),
    );

    storeValidSession("citizen");
    await renderApp("/dashboard/settings");

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Recent logins unavailable",
    );
    expect(screen.getByText(/Please try again later/i)).toBeInTheDocument();
  });

  it("renders multiple login entries", async () => {
    server.use(
      http.get("*/auth/login-history", () =>
        HttpResponse.json({
          items: [
            ...loginHistoryResponse.items,
            {
              id: 103,
              outcome: "success",
              ip_address: null,
              user_agent: null,
              created_at: "2026-01-12T06:00:00Z",
            },
          ],
          page: 1,
          page_size: 10,
          total_items: 3,
          total_pages: 1,
        }),
      ),
    );

    storeValidSession("citizen");
    await renderApp("/dashboard/settings");

    await waitFor(() => {
      expect(screen.getAllByText("Successful login")).toHaveLength(2);
    });
    expect(screen.getByText("Failed login")).toBeInTheDocument();
    expect(screen.getByText("IP address unavailable")).toBeInTheDocument();
    expect(screen.getByText("Device information unavailable")).toBeInTheDocument();
  });
});
