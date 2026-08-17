import { describe, expect, it } from "vitest";
import { http, HttpResponse } from "msw";
import { fireEvent, screen, waitFor } from "@testing-library/react";
import { server } from "./server";
import { renderApp, storeValidSession } from "./test-utils";
import { createAdminDealer, createDealerProfile } from "./factories";

describe("dealer profile page", () => {
  it("shows the create form when no profile exists yet", async () => {
    server.use(
      http.get("*/dealer/profile", () =>
        HttpResponse.json({ detail: "Dealer profile not found" }, { status: 404 }),
      ),
      http.get("*/dealer/profile/timeline", () =>
        HttpResponse.json({ detail: "Dealer profile not found" }, { status: 404 }),
      ),
    );
    storeValidSession("dealer");
    await renderApp("/dealer/profile");

    expect(
      await screen.findByRole("heading", { name: "Create your dealer profile" }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText(/Business name/i)).toBeInTheDocument();
  });

  it("creates a profile and switches to the status view", async () => {
    server.use(
      http.get("*/dealer/profile", () =>
        HttpResponse.json({ detail: "Dealer profile not found" }, { status: 404 }),
      ),
      http.get("*/dealer/profile/timeline", () =>
        HttpResponse.json({ detail: "Dealer profile not found" }, { status: 404 }),
      ),
    );
    storeValidSession("dealer");
    await renderApp("/dealer/profile");

    expect(
      await screen.findByRole("heading", { name: "Create your dealer profile" }),
    ).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText(/Business name/i), {
      target: { value: "Green Scrap Co" },
    });
    fireEvent.change(screen.getByLabelText(/Owner name/i), {
      target: { value: "Test Dealer" },
    });
    fireEvent.change(screen.getByLabelText(/Phone/i), {
      target: { value: "+15550000003" },
    });
    fireEvent.change(screen.getByLabelText(/Address/i), {
      target: { value: "12 Green Street, Kolkata" },
    });
    fireEvent.change(screen.getByLabelText(/City/i), {
      target: { value: "Kolkata" },
    });
    fireEvent.change(screen.getByLabelText(/Postal code/i), {
      target: { value: "700001" },
    });
    fireEvent.change(screen.getByLabelText(/Accepted materials/i), {
      target: { value: "plastic, paper" },
    });

    fireEvent.click(screen.getByRole("button", { name: /Create profile/i }));

    expect(
      await screen.findByRole("heading", { name: "Green Scrap Co" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Draft")).toBeInTheDocument();
  });

  it("shows the approval status and timeline for an existing profile", async () => {
    storeValidSession("dealer");
    await renderApp("/dealer/profile");

    expect(
      await screen.findByRole("heading", { name: "Green Scrap Co" }),
    ).toBeInTheDocument();
    expect(screen.getAllByText("Approved").length).toBeGreaterThan(0);
    expect(screen.getByText("Approval timeline")).toBeInTheDocument();
    expect(screen.getByText(/Profile submitted for review/i)).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /Submit for approval/i }),
    ).not.toBeInTheDocument();
  });

  it("submits a draft profile for approval", async () => {
    server.use(
      http.get("*/dealer/profile", () =>
        HttpResponse.json(
          createDealerProfile({ approval_status: "draft", is_verified: false, approved_at: null }),
        ),
      ),
      http.get("*/dealer/profile/timeline", () => HttpResponse.json([])),
    );
    storeValidSession("dealer");
    await renderApp("/dealer/profile");

    expect(
      await screen.findByRole("button", { name: /Submit for approval/i }),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Submit for approval/i }));

    await waitFor(() => {
      expect(screen.getByText("Pending Review")).toBeInTheDocument();
    });
  });

  it("shows the rejection reason on a rejected profile", async () => {
    server.use(
      http.get("*/dealer/profile", () =>
        HttpResponse.json(
          createDealerProfile({
            approval_status: "rejected",
            rejection_reason: "Incorrect GST number",
            is_verified: false,
            approved_at: null,
          }),
        ),
      ),
      http.get("*/dealer/profile/timeline", () => HttpResponse.json([])),
    );
    storeValidSession("dealer");
    await renderApp("/dealer/profile");

    expect(await screen.findByText(/Your application was rejected/i)).toBeInTheDocument();
    expect(screen.getByText("Incorrect GST number")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Submit for approval/i }),
    ).toBeInTheDocument();
  });
});

describe("dealer approval gate", () => {
  it("blocks inventory browsing when the profile is not approved", async () => {
    server.use(
      http.get("*/dealer/profile", () =>
        HttpResponse.json(
          createDealerProfile({ approval_status: "submitted", is_verified: false, approved_at: null }),
        ),
      ),
      http.get("*/dealer/inventory-lots", () =>
        HttpResponse.json({ detail: "Forbidden" }, { status: 403 }),
      ),
    );
    storeValidSession("dealer");
    await renderApp("/dealer/overview");

    expect(await screen.findByRole("heading", { name: "Approval required" })).toBeInTheDocument();
    expect(screen.getByText(/Pending Review/i)).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /View my dealer profile/i }),
    ).toBeInTheDocument();
  });

  it("asks dealers without a profile to create one", async () => {
    server.use(
      http.get("*/dealer/profile", () =>
        HttpResponse.json({ detail: "Dealer profile not found" }, { status: 404 }),
      ),
    );
    storeValidSession("dealer");
    await renderApp("/dealer/overview");

    expect(
      await screen.findByRole("heading", { name: "Dealer profile required" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /Set up your dealer profile/i }),
    ).toBeInTheDocument();
  });
});

describe("admin dealer review queue", () => {
  it("approves a pending dealer from the review queue", async () => {
    storeValidSession("admin");
    await renderApp("/admin/overview");

    const approveButtons = await screen.findAllByRole("button", {
      name: "Approve",
    });
    expect(screen.getAllByText("submitted").length).toBeGreaterThan(0);

    fireEvent.click(approveButtons[0]);
    expect(
      await screen.findByRole("heading", { name: "Approve dealer application" }),
    ).toBeInTheDocument();

    const dialogApprove = screen.getAllByRole("button", {
      name: "Approve",
    });
    fireEvent.click(dialogApprove[dialogApprove.length - 1]);
  });

  it("rejects a pending dealer with a required reason", async () => {
    storeValidSession("admin");
    await renderApp("/admin/overview");

    fireEvent.click(await screen.findByRole("button", { name: "Reject" }));
    expect(
      await screen.findByRole("heading", { name: "Reject dealer application" }),
    ).toBeInTheDocument();

    const rejectButtons = screen.getAllByRole("button", {
      name: "Reject",
    });
    const dialogReject = rejectButtons[rejectButtons.length - 1];
    expect(dialogReject).toBeDisabled();

    fireEvent.change(screen.getByLabelText(/Rejection reason/i), {
      target: { value: "Incorrect GST number" },
    });
    expect(dialogReject).toBeEnabled();
    fireEvent.click(dialogReject);
  });

  it("shows a dealer with no profile in the queue without review actions", async () => {
    server.use(
      http.get("*/admin/dealers/pending", () =>
        HttpResponse.json({
          items: [createAdminDealer({ has_profile: false, approval_status: "submitted" })],
          page: 1,
          page_size: 20,
          total_items: 1,
          total_pages: 1,
        }),
      ),
    );
    storeValidSession("admin");
    await renderApp("/admin/overview");

    expect(await screen.findByText("Profile missing")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Approve" })).toBeDisabled();
  });
});
