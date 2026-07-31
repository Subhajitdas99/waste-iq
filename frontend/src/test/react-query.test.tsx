import { describe, expect, it } from "vitest";
import { http, HttpResponse } from "msw";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { server } from "./server";
import { createTestQueryClient } from "./test-utils";
import {
  useCitizenPickups,
  useCreateCitizenPickup,
} from "@/hooks/useCitizenPickups";
import { getApiErrorMessage } from "@/lib/api-error";

function renderWithQueryClient(client: QueryClient, ui: React.ReactElement) {
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

function PickupListHarness() {
  const query = useCitizenPickups();
  return (
    <div>
      {query.isPending ? <p data-testid="loading">loading pickups</p> : null}
      {query.isError ? (
        <p data-testid="error">{getApiErrorMessage(query.error, "fallback error")}</p>
      ) : null}
      {query.data ? (
        <ul data-testid="pickup-list">
          {query.data.map((request) => (
            <li key={request.id}>{request.waste_type}</li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

function MutationHarness() {
  const listQuery = useCitizenPickups();
  const createMutation = useCreateCitizenPickup();
  return (
    <div>
      {listQuery.data ? (
        <ul data-testid="pickup-list">
          {listQuery.data.map((request) => (
            <li key={request.id}>{request.waste_type}</li>
          ))}
        </ul>
      ) : null}
      <button
        type="button"
        onClick={() =>
          createMutation.mutate({
            payload: {
              waste_type: "Metal cans",
              address: "5 New Lane, Kolkata",
              latitude: 22.5,
              longitude: 88.3,
            },
          })
        }
      >
        Create pickup
      </button>
    </div>
  );
}

describe("react query data fetching", () => {
  it("shows a loading state while the query is pending", async () => {
    server.use(
      http.get("*/pickup-requests", async () => {
        await new Promise((resolve) => setTimeout(resolve, 50));
        return HttpResponse.json([]);
      }),
    );
    const client = createTestQueryClient();
    renderWithQueryClient(
      client,
      <PickupListHarness />,
    );

    expect(screen.getByTestId("loading")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByTestId("pickup-list")).toBeInTheDocument();
    });
  });

  it("renders data from the API on success", async () => {
    renderWithQueryClient(
      createTestQueryClient(),
      <PickupListHarness />,
    );

    const list = await screen.findByTestId("pickup-list");
    expect(list).toHaveTextContent("Plastic bottles");
    expect(list).toHaveTextContent("Cardboard");
    expect(screen.queryByTestId("loading")).not.toBeInTheDocument();
    expect(screen.queryByTestId("error")).not.toBeInTheDocument();
  });

  it("surfaces the API error message on failure", async () => {
    server.use(
      http.get("*/pickup-requests", () =>
        HttpResponse.json({ detail: "Server exploded" }, { status: 500 }),
      ),
    );
    renderWithQueryClient(
      createTestQueryClient(),
      <PickupListHarness />,
    );

    const error = await screen.findByTestId("error");
    expect(error).toHaveTextContent("Server exploded");
    expect(screen.queryByTestId("pickup-list")).not.toBeInTheDocument();
  });

  it("invalidates the list query after a successful mutation", async () => {
    let listCallCount = 0;
    server.use(
      http.get("*/pickup-requests", () => {
        listCallCount += 1;
        return HttpResponse.json([
          { id: 1, waste_type: listCallCount > 1 ? "Fresh item" : "Plastic bottles" },
        ]);
      }),
      http.post("*/pickup-requests", () =>
        HttpResponse.json({ id: 2, waste_type: "Fresh item" }, { status: 201 }),
      ),
      http.get("*/pickup-requests/citizen/summary", () =>
        HttpResponse.json({
          total_requests: 1,
          pending_requests: 1,
          accepted_requests: 0,
          completed_requests: 0,
        }),
      ),
    );
    const user = userEvent.setup();
    renderWithQueryClient(
      createTestQueryClient(),
      <MutationHarness />,
    );

    expect(await screen.findByText("Plastic bottles")).toBeInTheDocument();
    expect(listCallCount).toBe(1);

    await user.click(screen.getByRole("button", { name: "Create pickup" }));

    await waitFor(() => {
      expect(screen.getByTestId("pickup-list")).toHaveTextContent("Fresh item");
    });
    expect(listCallCount).toBeGreaterThanOrEqual(2);
  });

  it("refetches the query when refetch is triggered", async () => {
    let callCount = 0;
    server.use(
      http.get("*/pickup-requests", () => {
        callCount += 1;
        return HttpResponse.json([
          { id: 1, waste_type: `Item ${callCount}` },
        ]);
      }),
    );

    function RefetchHarness() {
      const query = useCitizenPickups();
      return (
        <div>
          <ul data-testid="pickup-list">
            {query.data?.map((request) => (
              <li key={request.id}>{request.waste_type}</li>
            ))}
          </ul>
          <button type="button" onClick={() => void query.refetch()}>
            Refetch
          </button>
        </div>
      );
    }

    const user = userEvent.setup();
    renderWithQueryClient(
      createTestQueryClient(),
      <RefetchHarness />,
    );

    expect(await screen.findByText("Item 1")).toBeInTheDocument();
    expect(callCount).toBe(1);

    await user.click(screen.getByRole("button", { name: "Refetch" }));

    await waitFor(() => {
      expect(screen.getByTestId("pickup-list")).toHaveTextContent("Item 2");
    });
    expect(callCount).toBe(2);
  });
});
