/** Typed loaders for the data exported by scripts/export_web_data.py.
 *  Session transcripts live in public/data/sessions/ and are fetched on
 *  demand; everything here ships in the bundle. */

import sessionsIndexJson from "@/data/sessions_index.json";
import contextJson from "@/data/context.json";
import qualityJson from "@/data/quality.json";

export interface SessionMeta {
  file: string;
  team: string;
  question: string;
  n_steps: number;
  n_errors: number;
  n_figures: number;
  elapsed_s: number;
  model: string;
  recorded_at: string;
}

export interface SessionStep {
  tool: "run_sql" | "run_python";
  input: { query?: string; code?: string };
  output: string | null;
  figures: string[];
}

export interface Session {
  team: string;
  question: string;
  steps: SessionStep[];
  text: string;
  figures: string[];
  elapsed_s: number;
  model: string;
  recorded_at: string;
}

export interface Stakeholder {
  team: string;
  mission: string;
  cares_about: string[];
  communication: string[];
  usage: string[];
}

export interface Skill {
  name: string;
  description: string;
  when: string[];
  steps: string[];
}

export interface GoldExample {
  id: string;
  category: string;
  question: string;
  expected: unknown;
  observed: unknown;
  passed: boolean;
}

export interface AdversarialResult {
  id: string;
  category: string;
  question: string;
  passed: boolean;
  judge_reason: string;
  excerpt: string;
}

export interface Quality {
  gold: {
    n: number;
    pass: number;
    by_category: Record<string, { pass: number; total: number }>;
    examples: GoldExample[];
  };
  adversarial: { n: number; pass: number; results: AdversarialResult[] };
  gold_recorded_at: string;
  adv_recorded_at: string;
}

export const sessionsIndex = sessionsIndexJson as SessionMeta[];
export const contextLayer = contextJson as { stakeholders: Stakeholder[]; skills: Skill[] };
export const quality = qualityJson as Quality;

export const TEAMS = ["Executive", "Marketing", "Sales", "Product"] as const;

export const TEAM_BLURBS: Record<string, string> = {
  Executive: "ARR, bookings vs plan, unit economics — headline first, risks flagged early.",
  Marketing: "Pipeline contribution, campaign ROI, budget moves — always ends in a recommendation.",
  Sales: "Pipeline health, win rates, deal velocity — built for forecast calls.",
  Product: "Usage, adoption, retention — engagement trends by segment.",
};
