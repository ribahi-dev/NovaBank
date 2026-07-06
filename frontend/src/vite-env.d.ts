/// <reference types="vite/client" />

// Plotly n'expose pas de types pour ses distributions partielles :
// on les déclare pour garder un projet 100 % TypeScript strict.
declare module "plotly.js-basic-dist-min";
declare module "react-plotly.js/factory" {
  import type * as React from "react";
  const createPlotlyComponent: (plotly: unknown) => React.ComponentType<{
    data: unknown[];
    layout?: Record<string, unknown>;
    config?: Record<string, unknown>;
    style?: React.CSSProperties;
  }>;
  export default createPlotlyComponent;
}
