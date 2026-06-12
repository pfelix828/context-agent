/** Formatting helpers shared across pages. */

export const pct = (x: number, digits = 0) => `${(x * 100).toFixed(digits)}%`;

/** Percentage-point delta, signed: +4 pts / -2 pts */
export const pts = (x: number, digits = 0) => {
  const v = (x * 100).toFixed(digits);
  return `${x >= 0 ? "+" : ""}${v} pts`;
};

export const num = (x: number) =>
  Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 }).format(x);

/** 0.1536 -> "0.154" for ECE-style scores */
export const score3 = (x: number) => x.toFixed(3);

/** snake_case cause/tag keys -> human label */
export const humanize = (key: string) =>
  key.replaceAll("_", " ").replace(/^./, (c) => c.toUpperCase());
