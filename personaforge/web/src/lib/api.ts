const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export interface Stats {
  total_runs: number;
  total_conversations: number;
  total_failures: number;
  pass_rate: number;
  total_cost: number;
  pass_rate_over_time: { date: string; rate: number }[];
}

export interface Run {
  id: string;
  timestamp: string;
  status: "completed" | "failed" | "running";
  pass_rate: number;
  total_conversations: number;
  total_failures: number;
  cost: number;
  version: string;
}

export interface Conversation {
  id: string;
  run_id?: string;
  persona_id?: string;
  persona_name?: string;
  scenario_name?: string;
  status: "passed" | "failed";
  failure_type?: string;
  severity?: "low" | "medium" | "high" | "critical";
  cost?: number;
  total_cost?: number;
  latency?: number;
  turns?: Turn[];
  failures?: {
    category: string;
    severity: string;
    reason: string;
    evidence?: string;
  }[];
  evaluation?: {
    score?: number;
    reasoning?: string;
    summary?: string;
    failures?: {
      category: string;
      severity: string;
      reason: string;
      evidence?: string;
      turn_index?: number;
    }[];
  };
}

export interface Turn {
  role: "customer" | "agent";
  content: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

export interface Failure {
  type: string;
  evidence: string;
  severity: string;
  turn_index: number;
}

export interface PersonaMetric {
  name: string;
  pass_rate: number;
  total_runs: number;
  avg_latency: number;
}

export async function getStats(): Promise<Stats> {
  const res = await fetch(`${BASE_URL}/stats`, { next: { revalidate: 60 } });
  if (!res.ok) throw new Error("Failed to fetch stats");
  return res.json();
}

export async function getRuns(): Promise<Run[]> {
  const res = await fetch(`${BASE_URL}/runs`, { next: { revalidate: 30 } });
  if (!res.ok) throw new Error("Failed to fetch runs");
  return res.json();
}

export async function getRunDetails(
  runId: string,
): Promise<{ run: Run; conversations: Conversation[] }> {
  const res = await fetch(`${BASE_URL}/runs/${runId}`, {
    next: { revalidate: 30 },
  });
  if (!res.ok) throw new Error("Failed to fetch run details");
  return res.json();
}

export async function getConversation(
  conversationId: string,
): Promise<Conversation> {
  const res = await fetch(`${BASE_URL}/conversations/${conversationId}`, {
    next: { revalidate: 3600 },
  });
  if (!res.ok) throw new Error("Failed to fetch conversation");
  return res.json();
}

export async function getAgentHealth(): Promise<unknown[]> {
  const res = await fetch(`${BASE_URL}/agent-health`, {
    next: { revalidate: 300 },
  });
  if (!res.ok) throw new Error("Failed to fetch agent health");
  return res.json();
}

export async function getPersonaPerformance(): Promise<PersonaMetric[]> {
  const res = await fetch(`${BASE_URL}/persona-performance`, {
    next: { revalidate: 300 },
  });
  if (!res.ok) throw new Error("Failed to fetch persona performance");
  return res.json();
}

export interface FailureInstance {
  id: string;
  type: string;
  severity: string;
  persona: string;
  scenario: string;
  evidence: string;
  timestamp: string;
}

export async function getFailures(
  category?: string,
): Promise<FailureInstance[]> {
  const url = category
    ? `${BASE_URL}/failures?category=${category}`
    : `${BASE_URL}/failures`;
  const res = await fetch(url, { next: { revalidate: 30 } });
  if (!res.ok) throw new Error("Failed to fetch failures");
  return res.json();
}
