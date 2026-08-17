import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import { renderApp } from "./test-utils";

describe("public routes", () => {
  it("renders the landing page", async () => {
    await renderApp("/");

    expect(
      await screen.findByRole("heading", { name: /Smarter Waste Management/i }),
    ).toBeInTheDocument();
  });

  it("renders the features page", async () => {
    await renderApp("/features");

    expect(
      await screen.findByRole("heading", { name: "Platform Features" }),
    ).toBeInTheDocument();
  });

  it("renders the about page", async () => {
    await renderApp("/about");

    expect(
      await screen.findByRole("heading", { name: "About Waste-IQ" }),
    ).toBeInTheDocument();
  });

  it("renders the contact page", async () => {
    await renderApp("/contact");

    expect(
      await screen.findByRole("heading", { name: "Contact Us" }),
    ).toBeInTheDocument();
  });

  it("renders the unauthorized page", async () => {
    await renderApp("/unauthorized");

    expect(
      await screen.findByRole("heading", { name: "Access Denied" }),
    ).toBeInTheDocument();
  });
});
