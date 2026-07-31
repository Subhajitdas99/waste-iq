import { describe, expect, it } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NotificationsPanel } from "@/components/dashboard/NotificationsPanel";
import {
  buildNotificationMessage,
  buildNotificationTitle,
  deriveNotifications,
  useCitizenNotifications,
} from "@/hooks/useCitizenNotifications";
import { createPickupRequest } from "./factories";

const baseRequest = createPickupRequest({ id: 1, status: "pending" });

describe("buildNotificationTitle", () => {
  it("maps every notification status to a title", () => {
    expect(buildNotificationTitle("created")).toBe("Pickup request submitted");
    expect(buildNotificationTitle("accepted")).toBe("Pickup accepted");
    expect(buildNotificationTitle("on_the_way")).toBe("Collector on the way");
    expect(buildNotificationTitle("collected")).toBe("Waste collected");
    expect(buildNotificationTitle("completed")).toBe("Pickup completed");
    expect(buildNotificationTitle("cancelled")).toBe("Pickup cancelled");
  });
});

describe("buildNotificationMessage", () => {
  it("names the collector when one is assigned", () => {
    const accepted = createPickupRequest({
      id: 1,
      status: "accepted",
      assigned_collector_name: "Raj",
    });
    expect(buildNotificationMessage(accepted, "accepted")).toContain("Raj");
    expect(buildNotificationMessage(accepted, "on_the_way")).toContain("Raj");
  });

  it("includes the reported weight for completed pickups", () => {
    const completed = createPickupRequest({
      id: 1,
      status: "completed",
      assignment: {
        id: 1,
        collector_id: 2,
        collector_name: "Raj",
        accepted_at: "2026-01-10T09:00:00Z",
        completed_at: "2026-01-10T10:00:00Z",
        weight_kg: 4.5,
      },
    });
    expect(buildNotificationMessage(completed, "completed")).toContain("4.5 kg");
  });
});

describe("deriveNotifications", () => {
  it("seeds silently on the first run", () => {
    const result = deriveNotifications(
      [baseRequest, createPickupRequest({ id: 2, status: "completed" })],
      {},
      [],
    );

    expect(result.notifications).toEqual([]);
    expect(result.nextStatusMap).toEqual({ "1": "pending", "2": "completed" });
  });

  it("does not notify when a request status is unchanged", () => {
    const result = deriveNotifications(
      [baseRequest],
      { "1": "pending" },
      [],
    );

    expect(result.notifications).toHaveLength(0);
  });

  it("notifies on status transitions", () => {
    const result = deriveNotifications(
      [{ ...baseRequest, status: "accepted", assigned_collector_name: "Raj" }],
      { "1": "pending" },
      [],
    );

    expect(result.notifications).toHaveLength(1);
    expect(result.notifications[0]).toMatchObject({
      id: "1:accepted",
      status: "accepted",
      title: "Pickup accepted",
      read: false,
    });
    expect(result.notifications[0].message).toContain("Raj");
    expect(result.nextStatusMap).toEqual({ "1": "accepted" });
  });

  it("does not duplicate notifications for an unchanged status", () => {
    const first = deriveNotifications(
      [{ ...baseRequest, status: "accepted" }],
      { "1": "pending" },
      [],
    );
    const second = deriveNotifications(
      [{ ...baseRequest, status: "accepted" }],
      first.nextStatusMap,
      first.notifications,
    );

    expect(second.notifications).toHaveLength(1);
    expect(second.notifications).toEqual(first.notifications);
  });

  it("handles new requests appearing after the baseline", () => {
    const baseline = deriveNotifications([baseRequest], {}, []);

    const result = deriveNotifications(
      [baseRequest, createPickupRequest({ id: 7, status: "pending" })],
      baseline.nextStatusMap,
      [],
    );

    expect(result.notifications).toHaveLength(1);
    expect(result.notifications[0]).toMatchObject({
      id: "7:created",
      status: "created",
      title: "Pickup request submitted",
    });
  });

  it("caps the notification list at 30 items", () => {
    const existing = Array.from({ length: 30 }, (_, index) => ({
      id: `old:${index}`,
      requestId: 99,
      status: "completed" as const,
      title: "Old",
      message: "Old notification",
      createdAt: "2026-01-01T00:00:00Z",
      read: true,
    }));

    const result = deriveNotifications(
      [{ ...baseRequest, status: "completed" }],
      { "1": "collected" },
      existing,
    );

    expect(result.notifications).toHaveLength(30);
    expect(result.notifications[0].id).toBe("1:completed");
  });
});

function NotificationHarness({ requests }: { requests: ReturnType<typeof createPickupRequest>[] }) {
  const { notifications, unreadCount, markAsRead, markAllRead } =
    useCitizenNotifications(requests);

  return (
    <div>
      <p data-testid="count">{unreadCount}</p>
      <NotificationsPanel
        notifications={notifications}
        unreadCount={unreadCount}
        onMarkAsRead={markAsRead}
        onMarkAllRead={markAllRead}
      />
    </div>
  );
}

describe("useCitizenNotifications + NotificationsPanel", () => {
  it("shows a notification for a detected transition and supports mark-as-read", async () => {
    const user = userEvent.setup();
    const { rerender } = render(
      <NotificationHarness requests={[baseRequest]} />,
    );

    expect(screen.getByTestId("count")).toHaveTextContent("0");
    expect(screen.getByText("No notifications yet")).toBeInTheDocument();

    rerender(
      <NotificationHarness
        requests={[{ ...baseRequest, status: "accepted", assigned_collector_name: "Raj" }]}
      />,
    );

    expect(await screen.findByText("Pickup accepted")).toBeInTheDocument();
    expect(screen.getByTestId("count")).toHaveTextContent("1");
    expect(screen.getByLabelText("1 unread notifications")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: 'Mark "Pickup accepted" as read' }));

    expect(screen.getByTestId("count")).toHaveTextContent("0");
  });

  it("marks all notifications as read", async () => {
    const user = userEvent.setup();
    const { rerender } = render(
      <NotificationHarness
        requests={[baseRequest, createPickupRequest({ id: 2, status: "pending" })]}
      />,
    );

    rerender(
      <NotificationHarness
        requests={[
          { ...baseRequest, status: "accepted", assigned_collector_name: "Raj" },
          createPickupRequest({ id: 2, status: "completed" }),
        ]}
      />,
    );

    expect(await screen.findByText("Pickup accepted")).toBeInTheDocument();
    await screen.findByText("Pickup completed");

    await user.click(screen.getByRole("button", { name: "Mark all read" }));

    expect(screen.getByTestId("count")).toHaveTextContent("0");
  });

  it("persists notifications and does not re-notify after a refresh", async () => {
    const { rerender } = render(
      <NotificationHarness requests={[baseRequest]} />,
    );

    rerender(
      <NotificationHarness requests={[{ ...baseRequest, status: "accepted" }]} />,
    );

    await screen.findByText("Pickup accepted");

    rerender(
      <NotificationHarness requests={[{ ...baseRequest, status: "accepted" }]} />,
    );

    await waitFor(() => {
      const stored = JSON.parse(
        window.localStorage.getItem("wasteiq_citizen_notifications_v1") ?? "[]",
      ) as { id: string }[];
      expect(stored.map((item) => item.id)).toEqual(["1:accepted"]);
    });

    expect(screen.getAllByText("Pickup accepted")).toHaveLength(1);
  });

  it("reports notifications for completed pickups with weights", async () => {
    const { rerender } = render(
      <NotificationHarness requests={[baseRequest]} />,
    );

    rerender(
      <NotificationHarness
        requests={[
          {
            ...baseRequest,
            status: "completed",
            assignment: {
              id: 1,
              collector_id: 2,
              collector_name: "Raj",
              accepted_at: "2026-01-10T09:00:00Z",
              completed_at: "2026-01-10T10:00:00Z",
              weight_kg: 6,
            },
          },
        ]}
      />,
    );

    expect(await screen.findByText("Pickup completed")).toBeInTheDocument();
    expect(screen.getByText(/6\.0 kg reported/)).toBeInTheDocument();
  });

  it("marks a notification as read when it is clicked", async () => {
    const user = userEvent.setup();
    const { rerender } = render(
      <NotificationHarness requests={[baseRequest]} />,
    );

    rerender(
      <NotificationHarness requests={[{ ...baseRequest, status: "cancelled" }]} />,
    );

    expect(await screen.findByText("Pickup cancelled")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: 'Mark "Pickup cancelled" as read' }));

    expect(screen.getByTestId("count")).toHaveTextContent("0");
  });
});
