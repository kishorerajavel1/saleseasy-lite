import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import App from "./App";
import type { Analysis } from "../shared/api/contracts";

const analysis: Analysis = {
  issue_category: "stock_discrepancy",
  urgency: "high",
  evidence: [
    { source: "field_update", reference: "out of stock", verified: false },
  ],
  recommended_next_action: "verify_stock_physically",
  missing_information: ["What is the current physical stock count?"],
  needs_human_review: true,
  review_reason: "The field claim conflicts with system-recorded stock.",
};

function configure(response: Response | Promise<Response>) {
  return vi.spyOn(globalThis, "fetch").mockImplementation(async (url) => {
    if (String(url).endsWith("/status"))
      return Response.json({
        status: "ok",
        max_input_chars: 2000,
      });
    if (String(url).endsWith("/inventory"))
      return Response.json([
        {
          id: "inv-002",
          outlet: "Metro Fresh",
          sku: "Cola 500ml",
          system_stock: 48,
        },
      ]);
    return response;
  });
}

describe("field triage workflow", () => {
  it("submits the selected scenario and invalidates a result after editing", async () => {
    const fetch = configure(Response.json(analysis));
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: /Inventory conflict/ }));
    fireEvent.click(screen.getByRole("button", { name: /Analyze update/ }));
    await screen.findByRole("heading", { name: "Inventory discrepancy" });
    expect(
      fetch.mock.calls.find((call) => String(call[0]).endsWith("/analyze"))?.[1]
        ?.body,
    ).toBe(
      JSON.stringify({ text: "Metro Fresh says Cola 500ml is out of stock." }),
    );
    fireEvent.change(screen.getByRole("textbox"), {
      target: { value: "A different field update." },
    });
    expect(
      screen.queryByRole("heading", { name: "Inventory discrepancy" }),
    ).not.toBeInTheDocument();
  });

  it("renders untrusted quotations as text", async () => {
    configure(
      Response.json({
        ...analysis,
        evidence: [
          {
            source: "field_update",
            reference: "<script>attack()</script>",
            verified: false,
          },
        ],
      }),
    );
    const { container } = render(<App />);
    fireEvent.change(screen.getByRole("textbox"), {
      target: { value: "A field update." },
    });
    fireEvent.click(screen.getByRole("button", { name: /Analyze update/ }));
    await screen.findByRole("heading", { name: "Inventory discrepancy" });
    expect(screen.getByText("<script>attack()</script>")).toBeInTheDocument();
    expect(container.querySelector("script")).toBeNull();
    expect(screen.getByText("REPORTED · UNVERIFIED")).toBeInTheDocument();
  });

  it("presents rate limits clearly and re-enables submission", async () => {
    configure(
      new Response("{}", { status: 429, headers: { "Retry-After": "30" } }),
    );
    render(<App />);
    fireEvent.change(screen.getByRole("textbox"), {
      target: { value: "A field update." },
    });
    fireEvent.click(screen.getByRole("button", { name: /Analyze update/ }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Try again in 30 seconds",
    );
    expect(
      screen.getByRole("button", { name: /Analyze update/ }),
    ).toBeEnabled();
  });

  it("prevents duplicate requests and edits while analysis is pending", async () => {
    let finish!: (response: Response) => void;
    const fetch = configure(
      new Promise((resolve) => {
        finish = resolve;
      }),
    );
    render(<App />);
    fireEvent.change(screen.getByRole("textbox"), {
      target: { value: "A field update." },
    });
    fireEvent.click(screen.getByRole("button", { name: /Analyze update/ }));
    expect(screen.getByRole("textbox")).toBeDisabled();
    expect(screen.getByRole("button", { name: /Analyzing/ })).toBeDisabled();
    expect(
      fetch.mock.calls.filter((call) => String(call[0]).endsWith("/analyze")),
    ).toHaveLength(1);
    finish(Response.json(analysis));
    await waitFor(() => expect(screen.getByRole("textbox")).toBeEnabled());
  });

  it("shows provider failures without rendering a substitute analysis", async () => {
    configure(Response.json({ code: "analysis_unavailable" }, { status: 503 }));
    render(<App />);
    fireEvent.change(screen.getByRole("textbox"), {
      target: { value: "A customer feels unwell." },
    });
    fireEvent.click(screen.getByRole("button", { name: /Analyze update/ }));
    expect(await screen.findByRole("alert")).toHaveTextContent("manual review");
    expect(screen.queryByText("ANALYSIS COMPLETE")).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Analyze update/ }),
    ).toBeEnabled();
  });

  it("keeps the interface focused on triage", () => {
    configure(Response.json(analysis));
    render(<App />);
    expect(screen.queryByRole("complementary")).not.toBeInTheDocument();
    expect(screen.queryByText("Candidate workspace")).not.toBeInTheDocument();
    expect(screen.queryByText("API reference")).not.toBeInTheDocument();
    expect(screen.queryByText(/gemini/i)).not.toBeInTheDocument();
  });
});
