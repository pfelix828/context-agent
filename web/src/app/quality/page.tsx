import clsx from "clsx";
import { quality } from "@/lib/data";
import { pct } from "@/lib/format";
import { Card, CardTitle, PageHeader, Pill, Stat, SyntheticDataNote, Term } from "@/components/ui";

const CATEGORY_LABELS: Record<string, string> = {
  simple_count: "Simple counts",
  aggregation: "Aggregations",
  rate: "Rates & conversions",
  join: "Multi-table joins",
  time: "Time filters",
  ranking: "Ranking",
  multi_step: "Multi-step analysis",
};

export default function QualityPage() {
  const g = quality.gold;
  const a = quality.adversarial;
  const failures = a.results.filter((r) => !r.passed);
  const passes = a.results.filter((r) => r.passed);
  return (
    <div className="space-y-6">
      <PageHeader
        title="Evaluated like it matters — failures included"
        subtitle={
          <>
            An agent demo without an eval is a vibe. This one ships two published test sets: a{" "}
            <Term def="20 well-specified questions with reference SQL and numeric tolerances. Pass = the agent's number matches the reference answer.">
              gold set
            </Term>{" "}
            of deterministic correctness checks, and an{" "}
            <Term def="12 questions designed to tempt the agent into hallucination, unstated assumptions, or SQL traps. An LLM judge scores each against a rubric.">
              adversarial set
            </Term>{" "}
            designed to make it misbehave. The second one finds real problems, which is the point of having it.
          </>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2">
        <Card>
          <Stat label={`Gold set · ${quality.gold_recorded_at}`} value={`${g.pass}/${g.n}`} hint="Numeric correctness against reference SQL, deterministic scoring." />
          <p className="mt-2 text-sm text-muted">
            Every count, aggregation, rate, join, time filter, ranking, and multi-step question matched the
            reference answer within tolerance.
          </p>
        </Card>
        <Card>
          <Stat label={`Adversarial set · ${quality.adv_recorded_at}`} value={`${a.pass}/${a.n}`} hint="LLM-judged behavioral quality under adversarial questions." />
          <p className="mt-2 text-sm text-muted">
            {pct(a.pass / a.n)} pass. The five failures are listed below with the judge&apos;s reasons — publishing
            them is what makes the 20/20 above believable.
          </p>
        </Card>
      </div>

      <Card>
        <CardTitle sub="Pass rate by question category, gold set.">Where correctness was checked</CardTitle>
        <div className="grid gap-2 sm:grid-cols-3 lg:grid-cols-4">
          {Object.entries(g.by_category).map(([cat, v]) => (
            <div key={cat} className="rounded-lg border border-border-subtle px-3 py-2.5">
              <div className="text-xs font-medium text-muted">{CATEGORY_LABELS[cat] ?? cat}</div>
              <div className="mt-0.5 text-lg font-bold tabular-nums tracking-tight">
                {v.pass}/{v.total}
              </div>
            </div>
          ))}
        </div>
      </Card>

      <Card className="border-amber-300/70">
        <CardTitle sub="Each failure with the judge's reasoning, quoted. These are the agent's real current limits.">
          The five adversarial failures, named
        </CardTitle>
        <div className="space-y-3">
          {failures.map((r) => (
            <div key={r.id} className="rounded-lg border border-border-subtle p-4">
              <div className="flex flex-wrap items-center gap-2">
                <Pill className="border-red-200 bg-red-50 text-red-800">fail</Pill>
                <span className="text-sm font-medium">“{r.question}”</span>
              </div>
              <p className="mt-2 text-xs leading-relaxed text-muted">
                <strong className="text-foreground">Judge:</strong> {r.judge_reason}
              </p>
            </div>
          ))}
        </div>
        <p className="mt-3 max-w-3xl text-sm leading-relaxed text-muted">
          The pattern across failures: the agent answers helpfully where it should first refuse or disambiguate —
          deriving a churn proxy without flagging it, accepting ambiguous date conventions silently, not surfacing a
          pipeline-stage filter assumption. The fixes are context-layer work (sharper instructions about stating
          assumptions), which is exactly what the eval is for: it turns &quot;the agent feels off sometimes&quot; into
          a to-do list.
        </p>
      </Card>

      <Card>
        <CardTitle sub="The seven adversarial passes, for balance.">What it resists</CardTitle>
        <div className="grid gap-2 sm:grid-cols-2">
          {passes.map((r) => (
            <div key={r.id} className={clsx("rounded-lg border border-border-subtle px-3 py-2.5")}>
              <div className="flex items-center gap-2">
                <Pill className="border-emerald-200 bg-emerald-50 text-emerald-800">pass</Pill>
                <span className="text-xs font-medium">“{r.question}”</span>
              </div>
            </div>
          ))}
        </div>
      </Card>

      <SyntheticDataNote />
    </div>
  );
}
