"use client";

/**
 * The session player: unedited transcripts of real agent runs, rendered as a
 * first-class experience — every SQL query, every Python execution, every
 * error the agent hit and corrected, and the charts it produced.
 */

import { useEffect, useMemo, useState } from "react";
import clsx from "clsx";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { sessionsIndex, TEAM_BLURBS, TEAMS, type Session, type SessionStep } from "@/lib/data";
import { Card, Pill } from "@/components/ui";
import { PlotlyFigure } from "@/components/plotly-figure";

function Markdown({ children }: { children: string }) {
  return (
    <div className="md-body">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{children}</ReactMarkdown>
    </div>
  );
}

export function SessionPlayer() {
  const [team, setTeam] = useState<string>("Executive");
  const [file, setFile] = useState<string>(sessionsIndex[0].file);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  const teamSessions = useMemo(() => sessionsIndex.filter((s) => s.team === team), [team]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetch(`/data/sessions/${file}`)
      .then((r) => r.json())
      .then((s: Session) => {
        if (!cancelled) {
          setSession(s);
          setLoading(false);
        }
      })
      .catch(() => setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [file]);

  return (
    <div className="grid gap-4 lg:grid-cols-4">
      <div className="space-y-3 lg:col-span-1">
        <div className="flex flex-wrap gap-1.5">
          {TEAMS.map((t) => (
            <button
              key={t}
              onClick={() => {
                setTeam(t);
                const first = sessionsIndex.find((s) => s.team === t);
                if (first) setFile(first.file);
              }}
              className={clsx(
                "rounded-md px-2.5 py-1.5 text-xs font-medium",
                t === team ? "bg-accent-soft text-accent" : "bg-zinc-100 text-foreground/70 hover:text-foreground",
              )}
            >
              {t}
            </button>
          ))}
        </div>
        <p className="text-xs leading-relaxed text-muted">{TEAM_BLURBS[team]}</p>
        <div className="space-y-2">
          {teamSessions.map((s) => (
            <button
              key={s.file}
              onClick={() => setFile(s.file)}
              className={clsx(
                "block w-full rounded-lg border p-3 text-left text-sm transition-colors",
                s.file === file
                  ? "border-accent bg-accent-soft/60 font-medium text-foreground"
                  : "border-border-subtle bg-white text-foreground/80 hover:border-zinc-300",
              )}
            >
              “{s.question}”
              <span className="mt-1 block text-xs font-normal text-muted">
                {s.n_steps} tool calls · {s.n_figures} chart{s.n_figures === 1 ? "" : "s"}
                {s.n_errors > 0 ? ` · ${s.n_errors} self-correction${s.n_errors === 1 ? "" : "s"}` : ""} · {s.elapsed_s}s
              </span>
            </button>
          ))}
        </div>
      </div>

      <div className="lg:col-span-3">
        {loading || !session ? (
          <Card className="grid h-64 place-items-center text-sm text-muted">Loading transcript…</Card>
        ) : (
          <Transcript session={session} />
        )}
      </div>
    </div>
  );
}

function Transcript({ session }: { session: Session }) {
  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <div className="max-w-xl rounded-2xl rounded-br-sm bg-accent px-4 py-2.5 text-sm font-medium text-white">
          {session.question}
        </div>
      </div>

      <Card>
        <div className="mb-3 flex items-center justify-between gap-2">
          <h3 className="text-sm font-semibold tracking-tight">How the agent worked the question</h3>
          <Pill className="border-accent/40 bg-accent-soft text-accent">unedited transcript</Pill>
        </div>
        <ol className="space-y-3">
          {session.steps.map((step, i) => (
            <StepCard key={i} step={step} index={i + 1} steps={session.steps} />
          ))}
        </ol>
      </Card>

      <Card>
        <h3 className="mb-2 text-sm font-semibold tracking-tight">The answer</h3>
        <Markdown>{session.text}</Markdown>
        {session.figures.map((fig, i) => (
          <div key={i} className="mt-4 rounded-lg border border-border-subtle p-2">
            <PlotlyFigure figJson={fig} />
          </div>
        ))}
        <p className="mt-4 border-t border-border-subtle pt-3 text-xs text-muted">
          Recorded {session.recorded_at} · {session.model} · answered in {session.elapsed_s}s · the SQL, results,
          errors, and charts above are exactly what the agent produced, in order.
        </p>
      </Card>
    </div>
  );
}

function isError(step: SessionStep): boolean {
  return Boolean(step.output && step.output.slice(0, 300).includes("Error"));
}

function StepCard({ step, index, steps }: { step: SessionStep; index: number; steps: SessionStep[] }) {
  const errored = isError(step);
  const recovered = index > 1 && isError(steps[index - 2]);
  const [showResult, setShowResult] = useState(errored);
  const code = step.tool === "run_sql" ? step.input.query ?? "" : step.input.code ?? "";

  return (
    <li className="rounded-lg border border-border-subtle">
      <div className="flex flex-wrap items-center gap-2 border-b border-border-subtle/70 px-3 py-2">
        <span className="grid h-5 w-5 place-items-center rounded-full bg-zinc-100 text-[11px] font-bold text-zinc-600">
          {index}
        </span>
        <span className="text-xs font-semibold">{step.tool === "run_sql" ? "Ran SQL" : "Ran Python"}</span>
        {errored ? (
          <Pill className="border-amber-300/70 bg-amber-50 text-amber-800">hit an error — corrects itself next</Pill>
        ) : null}
        {recovered && !errored ? (
          <Pill className="border-emerald-300/70 bg-emerald-50 text-emerald-800">self-corrected retry</Pill>
        ) : null}
        <button
          onClick={() => setShowResult(!showResult)}
          className="ml-auto text-xs font-medium text-accent underline-offset-2 hover:underline"
        >
          {showResult ? "Hide result" : "Show result"}
        </button>
      </div>
      <pre className="max-h-56 overflow-auto px-3 py-2.5 font-mono text-[11.5px] leading-relaxed text-zinc-800">
        {code.trim()}
      </pre>
      {showResult && step.output ? (
        <div className="border-t border-border-subtle/70 bg-zinc-50/60 px-3 py-2.5">
          <div className="mb-1 text-[10.5px] font-semibold uppercase tracking-wide text-muted">Result</div>
          <div className={clsx("max-h-72 overflow-auto", errored && "text-red-800")}>
            <Markdown>{step.output}</Markdown>
          </div>
        </div>
      ) : null}
    </li>
  );
}
