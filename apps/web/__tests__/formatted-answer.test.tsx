import { describe, expect, test } from "vitest";
import { render, screen } from "@testing-library/react";

import { FormattedAnswer } from "@/components/assistant/formatted-answer";

describe("FormattedAnswer", () => {
  test("renders plain text with no citation markers unchanged", () => {
    render(<FormattedAnswer text="This clause has no citations at all." />);
    expect(
      screen.getByText("This clause has no citations at all.")
    ).toBeInTheDocument();
    expect(screen.queryByRole("superscript")).not.toBeInTheDocument();
  });

  test("renders a single citation marker as a styled superscript", () => {
    const { container } = render(<FormattedAnswer text="The term is 12 months. [1]" />);
    const sup = container.querySelector("sup");
    expect(sup).not.toBeNull();
    expect(sup).toHaveTextContent("1");
    // The bracketed marker itself should not remain as literal text.
    expect(container.textContent).not.toContain("[1]");
    expect(container.textContent).toContain("The term is 12 months.");
  });

  test("renders multiple citation markers in one string", () => {
    const { container } = render(
      <FormattedAnswer text="Clause A applies. [1] Clause B also applies. [2]" />
    );
    const sups = container.querySelectorAll("sup");
    expect(sups).toHaveLength(2);
    expect(sups[0]).toHaveTextContent("1");
    expect(sups[1]).toHaveTextContent("2");
  });

  test("handles a marker at the very start and end of the text", () => {
    const { container } = render(<FormattedAnswer text="[1] leads and trails [2]" />);
    const sups = container.querySelectorAll("sup");
    expect(sups).toHaveLength(2);
    expect(container.textContent).toContain("leads and trails");
  });

  test("does not treat non-numeric brackets as citation markers", () => {
    const { container } = render(<FormattedAnswer text="See [Exhibit A] for details." />);
    expect(container.querySelectorAll("sup")).toHaveLength(0);
    expect(container.textContent).toContain("See [Exhibit A] for details.");
  });

  test("renders empty string without throwing", () => {
    const { container } = render(<FormattedAnswer text="" />);
    expect(container.querySelector("p")).not.toBeNull();
  });
});
