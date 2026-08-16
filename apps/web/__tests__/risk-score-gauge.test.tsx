import { describe, expect, test } from "vitest";
import { render, screen } from "@testing-library/react";

import { RiskScoreGauge } from "@/components/analysis/risk-score-gauge";

describe("RiskScoreGauge", () => {
  test("scores below 34 are labeled Low Risk", () => {
    render(<RiskScoreGauge score={0} />);
    expect(screen.getByText("Low Risk")).toBeInTheDocument();

    render(<RiskScoreGauge score={33} />);
    expect(screen.getAllByText("Low Risk")).toHaveLength(2);
  });

  test("scores from 34 up to 66 are labeled Medium Risk", () => {
    render(<RiskScoreGauge score={34} />);
    expect(screen.getByText("Medium Risk")).toBeInTheDocument();

    render(<RiskScoreGauge score={66} />);
    expect(screen.getAllByText("Medium Risk")).toHaveLength(2);
  });

  test("scores of 67 and above are labeled High Risk", () => {
    render(<RiskScoreGauge score={67} />);
    expect(screen.getByText("High Risk")).toBeInTheDocument();

    render(<RiskScoreGauge score={100} />);
    expect(screen.getAllByText("High Risk")).toHaveLength(2);
  });

  test("renders the numeric score itself", () => {
    render(<RiskScoreGauge score={42} />);
    expect(screen.getByText("42")).toBeInTheDocument();
  });
});
