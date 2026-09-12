import type { Analysis, Isolate, ResearchRank } from "./types";

const API = import.meta.env.VITE_API_URL || (import.meta.env.PROD ? "" : "http://localhost:8000");

async function parse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || "The analysis could not be completed.");
  }
  return response.json();
}

export async function getIsolates(): Promise<Isolate[]> {
  return parse(await fetch(`${API}/api/isolates`));
}

export async function analyze(payload: {
  isolate_id?: string;
  fasta?: string;
  isolate_name?: string;
  cocktail_size: number;
}): Promise<Analysis> {
  return parse(
    await fetch(`${API}/api/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  );
}

export async function getResearchIsolates(): Promise<string[]> {
  return parse(await fetch(`${API}/api/research-isolates`));
}

export async function rankResearchHost(host_id: string): Promise<ResearchRank> {
  return parse(
    await fetch(`${API}/api/research-rank`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ host_id, limit: 20 }),
    }),
  );
}
