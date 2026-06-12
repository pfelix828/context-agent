import { contextLayer } from "@/lib/data";
import { Card, CardTitle, PageHeader, Pill, SyntheticDataNote } from "@/components/ui";

export default function HowItWorksPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="The same question gets a different answer depending on who asks"
        subtitle={
          <>
            That&apos;s the point of the project. Data teams translate the same warehouse into different stories for
            different rooms; this agent makes the translation explicit and configurable. Everything that shapes an
            answer lives in plain markdown files — swap them and the agent serves a different org.
          </>
        }
      />

      <Card>
        <CardTitle>The pipeline, end to end</CardTitle>
        <div className="grid gap-2 text-sm sm:grid-cols-5">
          {[
            { n: "1", t: "Pick a team", d: "Stakeholder profile loads: what they care about, how they want it said." },
            { n: "2", t: "Assemble context", d: "Profile + domain knowledge + data dictionary + analysis skills become the system prompt." },
            { n: "3", t: "Agent loop", d: "Claude writes SQL/Python; tools execute against read-only DuckDB and return results." },
            { n: "4", t: "Self-correct", d: "Errors come back as tool results; the agent revises and retries, up to 10 iterations." },
            { n: "5", t: "Tailored answer", d: "Findings framed in the stakeholder's terms, with interactive charts." },
          ].map((s) => (
            <div key={s.n} className="rounded-lg border border-border-subtle p-3">
              <div className="mb-1 flex items-center gap-2">
                <span className="grid h-5 w-5 place-items-center rounded-full bg-accent text-[11px] font-bold text-white">{s.n}</span>
                <span className="text-xs font-semibold">{s.t}</span>
              </div>
              <p className="text-xs leading-relaxed text-muted">{s.d}</p>
            </div>
          ))}
        </div>
      </Card>

      <Card>
        <CardTitle sub="One profile per team, in markdown. The agent reads the selected one before every conversation — this is what makes the same data sound different in different rooms.">
          The stakeholder profiles
        </CardTitle>
        <div className="grid gap-4 md:grid-cols-2">
          {contextLayer.stakeholders.map((s) => (
            <div key={s.team} className="rounded-lg border border-border-subtle p-4">
              <h3 className="text-sm font-semibold tracking-tight">{s.team}</h3>
              <p className="mt-1 text-xs leading-relaxed text-muted">{s.mission}</p>
              <div className="mt-3 text-[10.5px] font-semibold uppercase tracking-wide text-muted">Cares about</div>
              <div className="mt-1.5 flex flex-wrap gap-1">
                {s.cares_about.slice(0, 4).map((c) => (
                  <Pill key={c} className="text-[11px]">{c.split("—")[0].split("(")[0].trim()}</Pill>
                ))}
              </div>
              <div className="mt-3 text-[10.5px] font-semibold uppercase tracking-wide text-muted">How answers are framed</div>
              <ul className="mt-1 list-disc space-y-0.5 pl-4 text-xs leading-relaxed text-muted">
                {s.communication.slice(0, 3).map((c) => (
                  <li key={c}>{c}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </Card>

      <Card>
        <CardTitle sub="Reusable analysis playbooks the agent can draw on, each with trigger questions and explicit steps.">
          The skills library
        </CardTitle>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {contextLayer.skills.map((sk) => (
            <div key={sk.name} className="rounded-lg border border-border-subtle p-4">
              <h3 className="text-sm font-semibold tracking-tight">{sk.name}</h3>
              <p className="mt-1 text-xs leading-relaxed text-muted">{sk.description}</p>
              {sk.when[0] ? (
                <p className="mt-2 text-xs italic text-muted">e.g. “{sk.when[0].replaceAll('"', "")}”</p>
              ) : null}
            </div>
          ))}
        </div>
        <p className="mt-3 max-w-3xl text-sm leading-relaxed text-muted">
          The same architecture pattern as production agent systems: capability lives in versioned, reviewable text
          files rather than code, so an analyst — not an engineer — can teach the agent a new analysis or a new
          stakeholder.
        </p>
      </Card>

      <SyntheticDataNote />
    </div>
  );
}
