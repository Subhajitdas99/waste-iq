import { describe, expect, it } from "vitest";
import {
  CO2_SAVED_PER_KG,
  computeRecyclingImpact,
  formatImpactNumber,
} from "@/lib/recycling";
import { createPickupRequest } from "./factories";

describe("computeRecyclingImpact", () => {
  it("returns zeros when there are no completed pickups", () => {
    const metrics = computeRecyclingImpact([
      createPickupRequest({ id: 1, status: "pending" }),
      createPickupRequest({ id: 2, status: "accepted" }),
    ]);

    expect(metrics).toEqual({
      totalWeightKg: 0,
      totalPickups: 0,
      co2SavedKg: 0,
      ecoPoints: 0,
    });
  });

  it("sums verified weights of completed pickups only", () => {
    const metrics = computeRecyclingImpact([
      createPickupRequest({
        id: 1,
        status: "completed",
        assignment: {
          id: 1,
          collector_id: 2,
          collector_name: "Test Collector",
          accepted_at: "2026-01-10T09:00:00Z",
          completed_at: "2026-01-10T10:00:00Z",
          weight_kg: 12.5,
        },
      }),
      createPickupRequest({
        id: 2,
        status: "completed",
        assignment: {
          id: 2,
          collector_id: 2,
          collector_name: "Test Collector",
          accepted_at: "2026-01-11T09:00:00Z",
          completed_at: "2026-01-11T10:00:00Z",
          weight_kg: 3.25,
        },
      }),
      createPickupRequest({ id: 3, status: "cancelled" }),
    ]);

    expect(metrics.totalWeightKg).toBe(15.8);
    expect(metrics.totalPickups).toBe(2);
    expect(metrics.co2SavedKg).toBeCloseTo(Math.round(15.8 * CO2_SAVED_PER_KG * 10) / 10);
    expect(metrics.ecoPoints).toBe(Math.round(15.8 * 10));
  });

  it("ignores completed pickups without a reported weight", () => {
    const metrics = computeRecyclingImpact([
      createPickupRequest({
        id: 1,
        status: "completed",
        assignment: {
          id: 1,
          collector_id: 2,
          collector_name: "Test Collector",
          accepted_at: "2026-01-10T09:00:00Z",
          completed_at: "2026-01-10T10:00:00Z",
          weight_kg: null,
        },
      }),
      createPickupRequest({
        id: 2,
        status: "completed",
        assignment: {
          id: 2,
          collector_id: 2,
          collector_name: "Test Collector",
          accepted_at: "2026-01-11T09:00:00Z",
          completed_at: "2026-01-11T10:00:00Z",
          weight_kg: 7,
        },
      }),
    ]);

    expect(metrics.totalWeightKg).toBe(7);
    expect(metrics.totalPickups).toBe(2);
  });

  it("rounds weights to one decimal place", () => {
    const metrics = computeRecyclingImpact([
      createPickupRequest({
        id: 1,
        status: "completed",
        assignment: {
          id: 1,
          collector_id: 2,
          collector_name: "Test Collector",
          accepted_at: "2026-01-10T09:00:00Z",
          completed_at: "2026-01-10T10:00:00Z",
          weight_kg: 1.234,
        },
      }),
    ]);

    expect(metrics.totalWeightKg).toBe(1.2);
  });
});

describe("formatImpactNumber", () => {
  it("formats with at most one decimal place", () => {
    expect(formatImpactNumber(12.5)).toBe("12.5");
    expect(formatImpactNumber(0)).toBe("0");
  });
});
