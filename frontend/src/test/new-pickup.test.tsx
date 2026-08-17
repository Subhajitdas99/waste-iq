import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { MemoryRouter } from "react-router-dom";
import { server } from "./server";
import { createTestQueryClient } from "./test-utils";
import { createPickupRequest } from "./factories";
import { AuthProvider } from "@/context/AuthContext";
import { NewPickupPage } from "@/pages/dashboard/NewPickupPage";

function renderWithProviders(client: QueryClient, ui: React.ReactElement) {
  return render(
    <QueryClientProvider client={client}>
      <AuthProvider>
        <MemoryRouter>{ui}</MemoryRouter>
      </AuthProvider>
    </QueryClientProvider>,
  );
}

function attachImage(file: File) {
  const input = document.querySelector('input[type="file"]');
  expect(input).not.toBeNull();
  fireEvent.change(input as HTMLInputElement, { target: { files: [file] } });
}

const VALID_IMAGE = new File(["fake-image-bytes"], "waste.jpg", {
  type: "image/jpeg",
});

beforeEach(() => {
  Object.defineProperty(URL, "createObjectURL", {
    writable: true,
    value: vi.fn(() => "blob:test-preview"),
  });
  Object.defineProperty(URL, "revokeObjectURL", {
    writable: true,
    value: vi.fn(),
  });
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("NewPickupPage", () => {
  it("validates the Sprint 5 fields: weight, preferred time, and notes", async () => {
    const user = userEvent.setup();
    renderWithProviders(createTestQueryClient(), <NewPickupPage />);

    await user.type(screen.getByLabelText("Waste Type"), "Plastic bottles");
    await user.click(screen.getByRole("button", { name: /Next Step/ }));

    await user.type(screen.getByLabelText("Estimated Weight (kg)"), "-5");
    await user.type(
      screen.getByLabelText("Preferred Pickup Time"),
      "2020-01-01T10:00",
    );
    fireEvent.change(screen.getByLabelText("Notes (optional)"), {
      target: { value: "x".repeat(2001) },
    });
    await user.type(screen.getByLabelText("Latitude"), "22.5726");
    await user.type(screen.getByLabelText("Longitude"), "88.3639");
    await user.click(screen.getByRole("button", { name: /Next Step/ }));

    expect(
      screen.getByText("Estimated weight must be at least 0.1 kg."),
    ).toBeInTheDocument();
    expect(screen.getByText("Preferred time must be in the future.")).toBeInTheDocument();
    expect(
      screen.getByText("Notes must be 2,000 characters or fewer."),
    ).toBeInTheDocument();
  });

  it("rejects images with an unsupported file type", async () => {
    const user = userEvent.setup();
    renderWithProviders(createTestQueryClient(), <NewPickupPage />);

    attachImage(new File(["x"], "notes.txt", { type: "text/plain" }));
    await user.type(screen.getByLabelText("Waste Type"), "Plastic bottles");
    await user.click(screen.getByRole("button", { name: /Next Step/ }));

    expect(
      screen.getByText("Accepted formats are JPG, JPEG, PNG, and WEBP."),
    ).toBeInTheDocument();
  });

  it("submits the full payload including weight, preferred time, notes, and image", async () => {
    let capturedBody: string | null = null;
    server.use(
      http.post("*/pickup-requests", async ({ request }) => {
        capturedBody = await request.text();
        return HttpResponse.json(
          createPickupRequest({
            id: 101,
            waste_type: "Plastic bottles",
            status: "pending",
            estimated_weight_kg: 4.5,
            preferred_time: "2099-01-01T10:00:00",
            notes: "Leave at the gate",
            image_url: "https://example.com/uploads/waste.jpg",
            category: "Unknown",
            confidence: 0,
          }),
          { status: 201 },
        );
      }),
    );

    const user = userEvent.setup();
    renderWithProviders(createTestQueryClient(), <NewPickupPage />);

    attachImage(VALID_IMAGE);
    await user.type(screen.getByLabelText("Waste Type"), "Plastic bottles");
    await user.click(screen.getByRole("button", { name: /Next Step/ }));
    await user.type(
      screen.getByLabelText("Pickup Address"),
      "12 Green Street, Kolkata, 700029",
    );
    await user.type(screen.getByLabelText("Estimated Weight (kg)"), "4.5");
    await user.type(screen.getByLabelText("Preferred Pickup Time"), "2099-01-01T10:00");
    await user.type(screen.getByLabelText("Notes (optional)"), "Leave at the gate");
    await user.type(screen.getByLabelText("Latitude"), "22.5726");
    await user.type(screen.getByLabelText("Longitude"), "88.3639");
    await user.click(screen.getByRole("button", { name: /Next Step/ }));
    await user.click(screen.getByRole("button", { name: "Create Pickup Request" }));

    await waitFor(() => {
      expect(capturedBody).not.toBeNull();
    });

    const body = capturedBody as unknown as string;
    expect(body).toContain('name="waste_type"');
    expect(body).toContain("Plastic bottles");
    expect(body).toContain('name="address"');
    expect(body).toContain("12 Green Street, Kolkata, 700029");
    expect(body).toContain('name="latitude"');
    expect(body).toContain("22.5726");
    expect(body).toContain('name="longitude"');
    expect(body).toContain("88.3639");
    expect(body).toContain('name="estimated_weight_kg"');
    expect(body).toContain("4.5");
    expect(body).toContain('name="preferred_time"');
    expect(body).toContain("2099-01-01T10:00");
    expect(body).toContain('name="notes"');
    expect(body).toContain("Leave at the gate");
    expect(body).toContain('name="image"');
    expect(body).toContain("image/jpeg");

    expect(
      await screen.findByText("Pickup request #101 was created successfully."),
    ).toBeInTheDocument();
    expect(screen.getByText("Request #101 created")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Photo stored with the request. Classification preview activates when the AI model is live.",
      ),
    ).toBeInTheDocument();
  });

  it("shows the AI preview result when the backend returns a classification", async () => {
    server.use(
      http.post("*/pickup-requests", () => {
        return HttpResponse.json(
          createPickupRequest({
            id: 202,
            status: "pending",
            image_url: "https://example.com/uploads/waste.jpg",
            category: "Plastic",
            confidence: 0.85,
          }),
          { status: 201 },
        );
      }),
    );

    const user = userEvent.setup();
    renderWithProviders(createTestQueryClient(), <NewPickupPage />);

    await user.type(screen.getByLabelText("Waste Type"), "Plastic bottles");
    await user.click(screen.getByRole("button", { name: /Next Step/ }));
    await user.type(
      screen.getByLabelText("Pickup Address"),
      "12 Green Street, Kolkata, 700029",
    );
    await user.type(screen.getByLabelText("Latitude"), "22.5726");
    await user.type(screen.getByLabelText("Longitude"), "88.3639");
    await user.click(screen.getByRole("button", { name: /Next Step/ }));
    await user.click(screen.getByRole("button", { name: "Create Pickup Request" }));

    expect(
      await screen.findByText("Detected material: Plastic (85% confidence)"),
    ).toBeInTheDocument();
  });

  it("walks through all three steps with the back button", async () => {
    const user = userEvent.setup();
    renderWithProviders(createTestQueryClient(), <NewPickupPage />);

    expect(
      screen.getByRole("heading", { name: "Material" }),
    ).toBeInTheDocument();
    await user.type(screen.getByLabelText("Waste Type"), "Glass bottles");
    await user.click(screen.getByRole("button", { name: /Next Step/ }));

    expect(
      screen.getByRole("heading", { name: "Location & Details" }),
    ).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Back" }));

    expect(screen.getByLabelText("Waste Type")).toHaveValue("Glass bottles");
    await user.click(screen.getByRole("button", { name: /Next Step/ }));

    await user.type(
      screen.getByLabelText("Pickup Address"),
      "12 Green Street, Kolkata, 700029",
    );
    await user.type(screen.getByLabelText("Latitude"), "22.5726");
    await user.type(screen.getByLabelText("Longitude"), "88.3639");
    await user.click(screen.getByRole("button", { name: /Next Step/ }));

    expect(screen.getByText("Backend Payload Preview")).toBeInTheDocument();
    expect(screen.getByText("Glass bottles")).toBeInTheDocument();
    expect(screen.getByText("No image selected")).toBeInTheDocument();
    expect(screen.getByText("No preferred time")).toBeInTheDocument();
  });
});
