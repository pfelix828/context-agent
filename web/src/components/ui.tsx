import Link from "next/link";
import type { ReactNode } from "react";
import clsx from "clsx";

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className={clsx("rounded-xl border border-border-subtle bg-card p-5 shadow-[0_1px_2px_rgba(0,0,0,0.04)]", className)}>
      {children}
    </div>
  );
}

export function CardTitle({ children, sub }: { children: ReactNode; sub?: ReactNode }) {
  return (
    <div className="mb-3">
      <h3 className="text-sm font-semibold tracking-tight">{children}</h3>
      {sub ? <p className="mt-0.5 text-xs text-muted">{sub}</p> : null}
    </div>
  );
}

export function PageHeader({ title, subtitle, right }: { title: string; subtitle?: ReactNode; right?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div className="max-w-3xl">
        <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
        {subtitle ? <p className="mt-1 text-sm text-muted">{subtitle}</p> : null}
      </div>
      {right}
    </div>
  );
}

/** Colored delta chip in percentage points: green up / red down. */
export function Delta({ value, suffix = "pts", goodWhenUp = true, digits = 0 }: { value: number; suffix?: string; goodWhenUp?: boolean; digits?: number }) {
  const up = value >= 0;
  const good = goodWhenUp ? up : !up;
  const v = Math.abs(value * 100).toFixed(digits);
  return (
    <span className={clsx("inline-flex items-center gap-0.5 rounded-md px-1.5 py-0.5 text-xs font-medium", good ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700")}>
      {up ? "▲" : "▼"} {v} {suffix}
    </span>
  );
}

export function Stat({ label, value, delta, hint }: { label: ReactNode; value: ReactNode; delta?: ReactNode; hint?: string }) {
  return (
    <div>
      <div className="text-xs font-medium text-muted" title={hint}>
        {label}
      </div>
      <div className="mt-1 flex items-baseline gap-2">
        <span className="text-2xl font-bold tracking-tight">{value}</span>
        {delta}
      </div>
    </div>
  );
}

const severityStyles: Record<string, { bg: string; text: string; label: string }> = {
  win: { bg: "bg-emerald-50", text: "text-emerald-700", label: "Win" },
  opportunity: { bg: "bg-sky-50", text: "text-sky-700", label: "Opportunity" },
  risk: { bg: "bg-red-50", text: "text-red-700", label: "Risk" },
  watch: { bg: "bg-amber-50", text: "text-amber-800", label: "Watch" },
};

export function SeverityBadge({ severity }: { severity: string }) {
  const s = severityStyles[severity] ?? severityStyles.watch;
  return <span className={clsx("rounded-md px-2 py-0.5 text-xs font-semibold", s.bg, s.text)}>{s.label}</span>;
}

export function Pill({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <span className={clsx("inline-flex items-center rounded-full border border-border-subtle bg-white px-2.5 py-0.5 text-xs font-medium text-foreground/80", className)}>
      {children}
    </span>
  );
}

/** Monospace chip for raw transaction descriptors. */
export function Descriptor({ children }: { children: ReactNode }) {
  return (
    <code className="rounded bg-zinc-100 px-1.5 py-0.5 font-mono text-[11px] text-zinc-800">
      {children}
    </code>
  );
}

/** Standing reminder that every number in the app is synthetic. */
export function SyntheticDataNote({ className }: { className?: string }) {
  return (
    <p className={clsx("text-xs text-muted", className)}>
      Sessions are <strong>unedited recordings of real agent runs</strong> over seeded synthetic GTM
      data — business magnitudes are illustrative, the agent behavior is not. See{" "}
      <Link href="/methodology" className="underline decoration-dotted underline-offset-2 hover:text-foreground">
        Methodology
      </Link>
      .
    </p>
  );
}

/** Inline metric definition the reader can hover. */
export function Term({ children, def }: { children: ReactNode; def: string }) {
  return (
    <span title={def} className="cursor-help underline decoration-dotted underline-offset-2">
      {children}
    </span>
  );
}
