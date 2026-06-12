"use client";

/** Renders one of the agent's recorded Plotly figures exactly as produced.
 *  plotly.js is ~1MB gzipped, so it loads only on this page, on demand. */

import { useEffect, useRef, useState } from "react";

interface PlotlyLike {
  newPlot: (el: HTMLElement, data: unknown, layout: unknown, config: unknown) => void;
  purge: (el: HTMLElement) => void;
}

let plotlyPromise: Promise<PlotlyLike> | null = null;
function loadPlotly(): Promise<PlotlyLike> {
  if (!plotlyPromise) {
    plotlyPromise = import("plotly.js-dist-min").then((m) => (m.default ?? m) as unknown as PlotlyLike);
  }
  return plotlyPromise;
}

export function PlotlyFigure({ figJson }: { figJson: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    let cancelled = false;
    let plotted: PlotlyLike | null = null;

    loadPlotly()
      .then((Plotly) => {
        if (cancelled || !el) return;
        const fig = JSON.parse(figJson) as { data: unknown; layout?: Record<string, unknown> };
        const layout = {
          ...(fig.layout ?? {}),
          autosize: true,
          margin: { t: 48, r: 24, b: 48, l: 56 },
          paper_bgcolor: "rgba(0,0,0,0)",
          plot_bgcolor: "rgba(0,0,0,0)",
          font: { size: 12 },
        };
        plotted = Plotly;
        Plotly.newPlot(el, fig.data, layout, { displayModeBar: false, responsive: true });
      })
      .catch(() => setFailed(true));

    return () => {
      cancelled = true;
      if (plotted && el) plotted.purge(el);
    };
  }, [figJson]);

  if (failed) {
    return <p className="text-xs text-muted">Chart failed to render — the raw figure JSON is in the repo transcript.</p>;
  }
  return <div ref={ref} className="h-[380px] w-full" />;
}
