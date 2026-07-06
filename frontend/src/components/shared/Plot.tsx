// Plotly (distribution basic : bar, pie, scatter) — léger et suffisant.
import Plotly from "plotly.js-basic-dist-min";
import createPlotlyComponent from "react-plotly.js/factory";

export const Plot = createPlotlyComponent(Plotly);

// Layout de base partagé : transparent + couleurs du thème courant.
export function chartLayout(dark: boolean, overrides: Record<string, unknown> = {}) {
  return {
    paper_bgcolor: "transparent",
    plot_bgcolor: "transparent",
    font: { color: dark ? "#9aa5b1" : "#64707d", size: 12 },
    margin: { t: 8, r: 16, b: 40, l: 44 },
    ...overrides,
  };
}
