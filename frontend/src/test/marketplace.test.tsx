import { describe, expect, it } from "vitest";
import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderApp, storeValidSession } from "./test-utils";

describe("marketplace page", () => {
  it("lists available inventory lots and hides sold lots", async () => {
    storeValidSession("dealer");
    await renderApp("/dealer/marketplace");

    expect(await screen.findByRole("heading", { name: "Marketplace Listings" })).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Mixed PET bottles")).toBeInTheDocument();
    });
    expect(screen.getByText("Cardboard boxes")).toBeInTheDocument();
    expect(screen.getByText("Glass bottles")).toBeInTheDocument();
    expect(screen.queryByText("Aluminum cans")).not.toBeInTheDocument();
    expect(screen.getByText("3 lots available")).toBeInTheDocument();
  });

  it("shows the reserved-by-me lot with a reservation countdown", async () => {
    storeValidSession("dealer");
    await renderApp("/dealer/marketplace");

    const reservedCard = await screen.findByText("Glass bottles");
    expect(reservedCard).toBeInTheDocument();
    expect(screen.getAllByText("Reserved by you").length).toBeGreaterThan(0);
    expect(screen.getByText(/Reservation:/)).toBeInTheDocument();
  });

  it("filters lots by city", async () => {
    const user = userEvent.setup();
    storeValidSession("dealer");
    await renderApp("/dealer/marketplace");

    await screen.findByText("Mixed PET bottles");

    await user.type(screen.getByLabelText(/City/i), "Howrah");
    await user.click(screen.getByRole("button", { name: /Apply filters/i }));

    await waitFor(() => {
      expect(screen.queryByText("Mixed PET bottles")).not.toBeInTheDocument();
    });
    expect(screen.getByText("Cardboard boxes")).toBeInTheDocument();
    expect(screen.getByText("1 lot available")).toBeInTheDocument();
  });

  it("filters lots by search term", async () => {
    const user = userEvent.setup();
    storeValidSession("dealer");
    await renderApp("/dealer/marketplace");

    await screen.findByText("Mixed PET bottles");

    await user.type(screen.getByLabelText(/Search/i), "cardboard");
    await user.click(screen.getByRole("button", { name: /Apply filters/i }));

    await waitFor(() => {
      expect(screen.getByText("Cardboard boxes")).toBeInTheDocument();
    });
    expect(screen.queryByText("Mixed PET bottles")).not.toBeInTheDocument();
  });

  it("reserves an available lot via the reservation dialog", async () => {
    const user = userEvent.setup();
    storeValidSession("dealer");
    await renderApp("/dealer/marketplace");

    const cardboardCard = await screen.findByText("Cardboard boxes");

    const card = cardboardCard.closest("article");
    expect(card).not.toBeNull();

    await user.click(within(card as HTMLElement).getByRole("button", { name: /Reserve/i }));

    expect(
      screen.getByRole("heading", { name: "Reserve this lot" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/expires automatically after 24 hours/i)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Confirm reservation/i }));

    expect(await screen.findByText("Lot reserved successfully for 24 hours.")).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getAllByText("Reserved by you").length).toBeGreaterThanOrEqual(2);
    });
  });

  it("cancels a reservation", async () => {
    const user = userEvent.setup();
    storeValidSession("dealer");
    await renderApp("/dealer/marketplace");

    await screen.findByText("Glass bottles");

    await user.click(screen.getByRole("button", { name: /Cancel reservation/i }));

    expect(await screen.findByText("Reservation cancelled successfully.")).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.queryByText("Reserved by you")).not.toBeInTheDocument();
    });
  });

  it("purchases a reserved lot and shows the order confirmation", async () => {
    const user = userEvent.setup();
    storeValidSession("dealer");
    await renderApp("/dealer/marketplace");

    await screen.findByText("Glass bottles");

    await user.click(screen.getByRole("button", { name: /Buy now/i }));

    expect(screen.getByRole("heading", { name: "Confirm purchase" })).toBeInTheDocument();
    expect(
      within(screen.getByRole("dialog")).getByText("₹100.00"),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Confirm purchase/i }));

    expect(await screen.findByRole("heading", { name: "Purchase complete" })).toBeInTheDocument();
    expect(screen.getByText(/was created successfully/i)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Done/i }));

    await waitFor(() => {
      expect(screen.getByText("2 lots available")).toBeInTheDocument();
    });
  });
});

describe("marketplace details page", () => {
  it("shows lot details and allows reservation", async () => {
    const user = userEvent.setup();
    storeValidSession("dealer");
    await renderApp("/dealer/marketplace/201");

    expect(await screen.findByRole("heading", { name: "Mixed PET bottles" })).toBeInTheDocument();
    expect(screen.getByText("LOT-2026-000201")).toBeInTheDocument();
    expect(screen.getByText("₹765.00")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Reserve this lot/i }));

    expect(await screen.findByText("Lot reserved successfully for 24 hours.")).toBeInTheDocument();
    expect(screen.getByText("Reserved by you")).toBeInTheDocument();
  });

  it("shows the not-found state for sold or unknown lots", async () => {
    storeValidSession("dealer");
    await renderApp("/dealer/marketplace/204");

    expect(
      await screen.findByRole("heading", { name: "Inventory lot not found" }),
    ).toBeInTheDocument();
  });
});

describe("order history page", () => {
  it("shows completed orders", async () => {
    storeValidSession("dealer");
    await renderApp("/dealer/orders");

    expect(
      await screen.findByRole("heading", { name: "Order History" }),
    ).toBeInTheDocument();
    expect(screen.getByText("ORD-2026-000301")).toBeInTheDocument();
    expect(screen.getByText("Aluminum cans")).toBeInTheDocument();
  });

  it("shows transaction history and filters by type", async () => {
    const user = userEvent.setup();
    storeValidSession("dealer");
    await renderApp("/dealer/orders");

    await screen.findByText("ORD-2026-000301");

    await user.click(screen.getByRole("button", { name: /Transactions/i }));

    expect(await screen.findByText("purchase")).toBeInTheDocument();
    expect(screen.getAllByText("reservation").length).toBeGreaterThan(0);

    await user.selectOptions(screen.getByLabelText(/Filter by type/i), "purchase");

    await waitFor(() => {
      expect(screen.getByText("purchase")).toBeInTheDocument();
    });
    expect(screen.queryAllByText("reservation")).toHaveLength(0);
  });
});

describe("marketplace access control", () => {
  it("blocks citizens from the marketplace", async () => {
    storeValidSession("citizen");
    await renderApp("/dealer/marketplace");

    expect(await screen.findByRole("heading", { name: "Access Denied" })).toBeInTheDocument();
  });
});
