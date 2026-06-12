import { sessionsIndex } from "@/lib/data";
import { PageHeader, SyntheticDataNote } from "@/components/ui";
import { SessionPlayer } from "@/components/session-player";

export default function SessionsPage() {
  const totalSteps = sessionsIndex.reduce((a, s) => a + s.n_steps, 0);
  const totalCorrections = sessionsIndex.reduce((a, s) => a + s.n_errors, 0);
  return (
    <div className="space-y-6">
      <PageHeader
        title="Watch a real AI analyst work, unedited"
        subtitle={
          <>
            The agent reads a stakeholder profile, then answers business questions by writing and running SQL and
            Python against a GTM warehouse — live, with no canned answers. These {sessionsIndex.length} sessions are
            unedited recordings of real runs: {totalSteps} tool calls, including {totalCorrections} places where the
            agent hit an error and corrected itself. The errors stay in because that&apos;s what working with agents
            actually looks like — and recovering from them is the skill.
          </>
        }
      />
      <SessionPlayer />
      <SyntheticDataNote />
    </div>
  );
}
