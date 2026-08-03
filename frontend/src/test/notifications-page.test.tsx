import { beforeEach, describe, expect, it } from "vitest";
import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import { renderApp, storeValidSession } from "./test-utils";
import { notificationStore, resetNotificationStore } from "./handlers";
import { createNotification } from "./factories";

describe("notifications page", () => {
  beforeEach(() => {
    resetNotificationStore();
  });

  it("renders the notification list with unread and read items", async () => {
    storeValidSession("citizen");
    await renderApp("/dashboard/notifications");

    expect(
      await screen.findByText(
        "Stay up to date with your pickup requests, dealer status, and inventory activity.",
      ),
    ).toBeInTheDocument();

    expect(await screen.findByText("Pickup request created")).toBeInTheDocument();
    expect(screen.getByText("Pickup accepted")).toBeInTheDocument();
    expect(screen.getByText("Pickup completed")).toBeInTheDocument();
    expect(screen.getByText(/\(3 total\)/)).toBeInTheDocument();
  });

  it("shows the empty state when the user has no notifications", async () => {
    storeValidSession("collector");
    await renderApp("/collector/notifications");

    expect(await screen.findByText("No notifications yet")).toBeInTheDocument();
  });

  it("filters notifications by status", async () => {
    storeValidSession("citizen");
    await renderApp("/dashboard/notifications");

    expect(await screen.findByText("Pickup request created")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Unread" }));

    expect(await screen.findByText("Pickup request created")).toBeInTheDocument();
    expect(screen.getByText("Pickup accepted")).toBeInTheDocument();
    expect(screen.queryByText("Pickup completed")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Read" }));

    expect(await screen.findByText("Pickup completed")).toBeInTheDocument();
    expect(screen.queryByText("Pickup request created")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "All" }));

    expect(await screen.findByText("Pickup accepted")).toBeInTheDocument();
    expect(screen.getByText("Pickup completed")).toBeInTheDocument();
  });

  it("marks all notifications as read", async () => {
    storeValidSession("citizen");
    await renderApp("/dashboard/notifications");

    expect(await screen.findByText("Pickup request created")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Mark all read" }));

    await waitFor(() => {
      expect(screen.queryByText("Mark all read")).toBeDisabled();
    });

    fireEvent.click(screen.getByRole("button", { name: "Read" }));

    expect(await screen.findByText("Pickup request created")).toBeInTheDocument();
    expect(screen.getByText("Pickup accepted")).toBeInTheDocument();
    expect(screen.getByText("Pickup completed")).toBeInTheDocument();
  });

  it("marks a single notification as read when clicked and follows its link", async () => {
    storeValidSession("citizen");
    await renderApp("/dashboard/notifications");

    const pickupNotification = await screen.findByText("Pickup request created");
    fireEvent.click(pickupNotification);

    await waitFor(() => {
      expect(window.location.pathname).toBe("/dashboard/pickups/3");
    });
  });

  it("deletes a notification from the list", async () => {
    storeValidSession("citizen");
    await renderApp("/dashboard/notifications");

    expect(await screen.findByText("Pickup request created")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Delete notification: Pickup completed" }));

    await waitFor(() => {
      expect(screen.queryByText("Pickup completed")).not.toBeInTheDocument();
    });

    expect(
      notificationStore.some((notification) => notification.id === 703),
    ).toBe(false);
  });

  it("clears all read notifications", async () => {
    storeValidSession("citizen");
    await renderApp("/dashboard/notifications");

    expect(await screen.findByText("Pickup completed")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Clear read" }));

    await waitFor(() => {
      expect(screen.queryByText("Pickup completed")).not.toBeInTheDocument();
    });

    expect(
      notificationStore.some((notification) => notification.id === 703),
    ).toBe(false);
  });

  it("paginates when there are more notifications than the page size", async () => {
    for (let index = 0; index < 12; index += 1) {
      notificationStore.push(
        createNotification({
          id: 1000 + index,
          user_id: 1,
          title: `Bulk notification ${index + 1}`,
          message: "Test message",
          type: "system",
          link: null,
          created_at: `2026-01-0${(index % 9) + 1}T09:00:00Z`,
        }),
      );
    }

    storeValidSession("citizen");
    await renderApp("/dashboard/notifications");

    expect(await screen.findByText("Page 1 of 2")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Next" }));

    expect(await screen.findByText("Page 2 of 2")).toBeInTheDocument();
    expect(screen.getAllByTestId(/^notification-(link|item)-/).length).toBeGreaterThan(0);
  });
});

describe("notification header bell", () => {
  beforeEach(() => {
    resetNotificationStore();
  });

  it("shows the unread count on the bell", async () => {
    storeValidSession("citizen");
    await renderApp("/dashboard/overview");

    const bell = await screen.findByLabelText("Open notifications");
    expect(bell).toBeInTheDocument();
    expect(within(bell).getByText("2")).toBeInTheDocument();
  });

  it("opens the dropdown and shows recent unread notifications", async () => {
    storeValidSession("citizen");
    await renderApp("/dashboard/overview");

    fireEvent.click(await screen.findByLabelText("Open notifications"));

    const dropdown = await screen.findByTestId("notification-dropdown");
    expect(within(dropdown).getByText("Unread notifications")).toBeInTheDocument();
    expect(within(dropdown).getByText("Pickup request created")).toBeInTheDocument();
    expect(within(dropdown).getByText("Pickup accepted")).toBeInTheDocument();
  });

  it("marks all read from the dropdown and updates the bell", async () => {
    storeValidSession("citizen");
    await renderApp("/dashboard/overview");

    const bell = await screen.findByLabelText("Open notifications");
    fireEvent.click(bell);

    const dropdown = await screen.findByTestId("notification-dropdown");
    fireEvent.click(within(dropdown).getByRole("button", { name: "Mark all read" }));

    await waitFor(() => {
      expect(within(bell).queryByText("2")).not.toBeInTheDocument();
    });
  });

  it("navigates to the notifications page from the dropdown", async () => {
    storeValidSession("citizen");
    await renderApp("/dashboard/overview");

    fireEvent.click(await screen.findByLabelText("Open notifications"));

    const dropdown = await screen.findByTestId("notification-dropdown");
    fireEvent.click(within(dropdown).getByText("View all notifications"));

    await waitFor(() => {
      expect(window.location.pathname).toBe("/dashboard/notifications");
    });
  });
});