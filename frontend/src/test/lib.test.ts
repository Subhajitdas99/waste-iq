import { describe, expect, it } from "vitest";
import { AxiosError, AxiosHeaders } from "axios";
import {
  buildPickupActivityText,
  filterTimelinePreview,
  formatDateTime,
  formatPickupStatus,
  formatWeight,
  getPickupProgress,
  matchesPickupQuery,
  sortPickupRequests,
} from "@/lib/pickup";
import { getApiErrorMessage } from "@/lib/api-error";
import { createPickupRequest, createUser } from "./factories";
import type { PickupTimelineEvent } from "@/types/pickup";

describe("formatPickupStatus", () => {
  it("maps known statuses to their display labels", () => {
    expect(formatPickupStatus("pending")).toBe("Pending");
    expect(formatPickupStatus("accepted")).toBe("Accepted");
    expect(formatPickupStatus("on_the_way")).toBe("On The Way");
    expect(formatPickupStatus("collected")).toBe("Collected");
    expect(formatPickupStatus("completed")).toBe("Completed");
    expect(formatPickupStatus("cancelled")).toBe("Cancelled");
  });

  it("falls back to a spaced label for unknown statuses", () => {
    expect(formatPickupStatus("on_route")).toBe("on route");
  });
});

describe("formatDateTime", () => {
  it("returns Not available for missing values", () => {
    expect(formatDateTime(null)).toBe("Not available");
    expect(formatDateTime(undefined)).toBe("Not available");
  });

  it("formats valid timestamps", () => {
    const formatted = formatDateTime("2026-01-10T08:00:00Z");

    expect(formatted).toContain("Jan");
    expect(formatted).toContain("2026");
    expect(formatted).not.toBe("Not available");
  });
});

describe("formatWeight", () => {
  it("returns Not reported for non-numeric weights", () => {
    expect(formatWeight(null)).toBe("Not reported");
    expect(formatWeight(undefined)).toBe("Not reported");
  });

  it("formats numeric weights with one decimal place", () => {
    expect(formatWeight(42.5)).toBe("42.5 kg");
    expect(formatWeight(0)).toBe("0.0 kg");
  });
});

describe("getPickupProgress", () => {
  it("returns 0 for cancelled and unknown statuses", () => {
    expect(getPickupProgress("cancelled")).toBe(0);
    expect(getPickupProgress("unknown" as never)).toBe(0);
  });

  it("returns progress for known statuses", () => {
    expect(getPickupProgress("pending")).toBe(20);
    expect(getPickupProgress("accepted")).toBe(40);
    expect(getPickupProgress("on_the_way")).toBe(60);
    expect(getPickupProgress("collected")).toBe(80);
    expect(getPickupProgress("completed")).toBe(100);
  });
});

describe("buildPickupActivityText", () => {
  it("describes every status", () => {
    const base = createPickupRequest();
    expect(buildPickupActivityText({ ...base, status: "completed" })).toBe(
      "Pickup completed for Plastic bottles.",
    );
    expect(buildPickupActivityText({ ...base, status: "collected" })).toBe(
      "Waste collected and awaiting final confirmation.",
    );
    expect(
      buildPickupActivityText({
        ...base,
        status: "on_the_way",
        assigned_collector_name: "Raj",
      }),
    ).toBe("Raj is on the way.");
    expect(buildPickupActivityText({ ...base, status: "on_the_way" })).toBe(
      "Your collector is on the way.",
    );
    expect(
      buildPickupActivityText({
        ...base,
        status: "accepted",
        assigned_collector_name: "Raj",
      }),
    ).toBe("Raj accepted your request.");
    expect(buildPickupActivityText({ ...base, status: "accepted" })).toBe(
      "A collector accepted your request.",
    );
    expect(buildPickupActivityText({ ...base, status: "cancelled" })).toBe(
      "Pickup request was cancelled.",
    );
    expect(buildPickupActivityText({ ...base, status: "pending" })).toBe(
      "Pickup request submitted for Plastic bottles.",
    );
  });
});

describe("sortPickupRequests", () => {
  const older = createPickupRequest({
    id: 1,
    created_at: "2026-01-01T08:00:00Z",
    status: "completed",
  });
  const newer = createPickupRequest({
    id: 2,
    created_at: "2026-01-10T08:00:00Z",
    status: "pending",
  });

  it("sorts newest first by default", () => {
    expect(sortPickupRequests([older, newer], "newest").map((r) => r.id)).toEqual([2, 1]);
  });

  it("sorts oldest first", () => {
    expect(sortPickupRequests([newer, older], "oldest").map((r) => r.id)).toEqual([1, 2]);
  });

  it("sorts by status label", () => {
    const sorted = sortPickupRequests([older, newer], "status");
    expect(sorted.map((r) => r.status)).toEqual(["completed", "pending"]);
  });
});

describe("matchesPickupQuery", () => {
  const request = createPickupRequest({
    id: 7,
    waste_type: "Cardboard",
    address: "12 Green Street",
    assigned_collector_name: "Raj",
  });

  it("matches everything for an empty query", () => {
    expect(matchesPickupQuery(request, "   ")).toBe(true);
  });

  it("matches against waste type, address, collector, and id", () => {
    expect(matchesPickupQuery(request, "card")).toBe(true);
    expect(matchesPickupQuery(request, "green street")).toBe(true);
    expect(matchesPickupQuery(request, "raj")).toBe(true);
    expect(matchesPickupQuery(request, "7")).toBe(true);
  });

  it("returns false when nothing matches", () => {
    expect(matchesPickupQuery(request, "aluminum")).toBe(false);
  });
});

describe("filterTimelinePreview", () => {
  const events: PickupTimelineEvent[] = [
    { id: 1, status: "pending", note: null, actor_name: null, actor_role: null, created_at: "2026-01-01T08:00:00Z" },
    { id: 2, status: "accepted", note: null, actor_name: null, actor_role: null, created_at: "2026-01-02T08:00:00Z" },
    { id: 3, status: "collected", note: null, actor_name: null, actor_role: null, created_at: "2026-01-03T08:00:00Z" },
    { id: 4, status: "completed", note: null, actor_name: null, actor_role: null, created_at: "2026-01-04T08:00:00Z" },
  ];

  it("sorts newest first and limits the preview", () => {
    const preview = filterTimelinePreview(events, 2);
    expect(preview.map((event) => event.id)).toEqual([4, 3]);
  });

  it("applies the default limit of three", () => {
    expect(filterTimelinePreview(events)).toHaveLength(3);
  });
});

describe("getApiErrorMessage", () => {
  function makeAxiosError(response?: { status: number; data: unknown }) {
    return new AxiosError("Request failed", "ERR_BAD_REQUEST", undefined, undefined, {
      data: response?.data,
      status: response?.status ?? 500,
      statusText: "Error",
      headers: {},
      config: { headers: new AxiosHeaders() },
    });
  }

  it("returns the fallback for non-axios errors", () => {
    expect(getApiErrorMessage(new Error("boom"), "fallback text")).toBe("fallback text");
    expect(getApiErrorMessage("boom", "fallback text")).toBe("fallback text");
  });

  it("returns a string detail from the response", () => {
    expect(getApiErrorMessage(makeAxiosError({ status: 401, data: { detail: "Invalid email or password" } }))).toBe(
      "Invalid email or password",
    );
  });

  it("joins array details", () => {
    const error = makeAxiosError({
      status: 422,
      data: { detail: [{ msg: "Field required" }, { msg: "Too short" }] },
    });
    expect(getApiErrorMessage(error)).toBe("Field required, Too short");
  });

  it("uses the fallback when the detail is missing or not stringifiable", () => {
    expect(getApiErrorMessage(makeAxiosError({ status: 500, data: { detail: { code: 1 } } }), "fb")).toBe("fb");
    expect(getApiErrorMessage(makeAxiosError({ status: 500, data: {} }), "fb")).toBe("fb");
  });
});

describe("auth fixtures", () => {
  it("provides a realistic user profile", () => {
    expect(createUser().email).toMatch(/@example\.com$/);
  });
});
