import { Card, CardTitle, PageHeader, Term } from "@/components/ui";

export default function MethodologyPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Methodology"
        subtitle="What the agent runs on, how execution is kept safe, what the recordings are, and how to run it live yourself."
      />

      <Card>
        <CardTitle>The data underneath</CardTitle>
        <p className="max-w-3xl text-sm leading-relaxed text-muted">
          A seeded synthetic B2B SaaS GTM warehouse in DuckDB: 2,000 accounts, 8,000 leads through a five-stage
          funnel, 45 campaigns across six channels, 17K+ attribution touches, and 100K+ daily product-usage rows,
          spanning January 2025 to February 2026. The exact database file ships in the repo, so the recorded
          sessions, the local app, and the eval all compute against byte-identical data. Synthetic means the
          business magnitudes are illustrative; the agent&apos;s SQL, reasoning, and behavior are real.
        </p>
      </Card>

      <Card>
        <CardTitle>Sandboxed execution</CardTitle>
        <ul className="max-w-3xl list-disc space-y-1.5 pl-5 text-sm leading-relaxed text-muted">
          <li>SQL runs against a <strong className="text-foreground">read-only</strong> DuckDB connection — the agent cannot mutate data.</li>
          <li>Python executes in a restricted namespace: pandas, numpy, plotly, and a query() helper; imports outside an allowlist are blocked, file access is blocked. Unit tests pin the blocklist.</li>
          <li>The tool loop is capped at 10 iterations per question, and errors return to the model as tool results — which is what produces the visible self-corrections in the transcripts.</li>
        </ul>
      </Card>

      <Card>
        <CardTitle>What the recordings are</CardTitle>
        <p className="max-w-3xl text-sm leading-relaxed text-muted">
          Each session was produced by{" "}
          <code className="rounded bg-zinc-100 px-1 py-0.5 font-mono text-xs">scripts/record_demo_sessions.py</code>,
          which runs the real agent through its streaming interface and persists every event — tool inputs, raw
          outputs, figures as Plotly JSON, timing — to{" "}
          <code className="rounded bg-zinc-100 px-1 py-0.5 font-mono text-xs">demo_sessions/*.json</code>. This site
          renders those files verbatim. Re-running the script regenerates them from scratch; because the model is
          not deterministic, fresh recordings differ in wording and occasionally in approach, which is part of why
          the published <Term def="20/20 on deterministic numeric checks; 7/12 on LLM-judged adversarial behavior. See the Quality page.">eval results</Term>{" "}
          matter more than any single pretty transcript.
        </p>
      </Card>

      <Card>
        <CardTitle>Honest limits</CardTitle>
        <ul className="max-w-3xl list-disc space-y-1.5 pl-5 text-sm leading-relaxed text-muted">
          <li>The adversarial eval found real failure modes (assumption-flagging, refusal calibration); they are listed on the Quality page, not patched out of the recordings.</li>
          <li>Stakeholder adaptation is demonstrated across four profiles on one synthetic domain; production would need profile governance and feedback loops.</li>
          <li>Latency is real: 17-96 seconds per question in the recordings, dominated by the tool loop. Fine for analysis work, not for dashboard-speed queries.</li>
          <li>Each question costs real API usage, which is why the public demo replays recordings rather than exposing a shared live endpoint.</li>
        </ul>
      </Card>

      <Card>
        <CardTitle>Run it live</CardTitle>
        <div className="max-w-3xl space-y-2 text-sm leading-relaxed text-muted">
          <p>
            The agent runs interactively on your machine with your own Anthropic API key — chat UI, live tool
            execution, all four stakeholder modes:
          </p>
          <pre className="overflow-x-auto rounded-lg bg-zinc-100 px-4 py-3 font-mono text-xs leading-relaxed text-zinc-800">{`git clone https://github.com/pfelix828/context-agent
cd context-agent && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
streamlit run app/streamlit_app.py`}</pre>
          <p>
            The eval harness is one command too:{" "}
            <code className="rounded bg-zinc-100 px-1 py-0.5 font-mono text-xs">python -m evals.run_eval</code>{" "}
            re-scores the gold and adversarial sets against your runs.
          </p>
        </div>
      </Card>
    </div>
  );
}
