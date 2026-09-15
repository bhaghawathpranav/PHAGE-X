import type { Analysis, AssemblyInspection, Isolate, IsolateEmbedding, IsolateLocusExtraction, NovelIsolateRank, ProcessingCapabilities, ResearchModelStatus, ResearchRank } from "./types";

const API = import.meta.env.VITE_API_URL || (import.meta.env.PROD ? "" : "http://localhost:8000");

async function parse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = body.detail;
    if (typeof detail === "string") throw new Error(detail);
    if (Array.isArray(detail)) {
      const messages = detail
        .map((item) => typeof item?.msg === "string" ? item.msg.replace(/^Value error,\s*/i, "") : "")
        .filter(Boolean);
      throw new Error(messages.join(" ") || "Please check the submitted input.");
    }
    if (detail && typeof detail === "object") {
      throw new Error(typeof detail.message === "string" ? detail.message : "Please check the submitted input.");
    }
    throw new Error("The analysis could not be completed.");
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
  demo_fasta?: boolean;
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

export async function getResearchModelStatus(): Promise<ResearchModelStatus> {
  return parse(await fetch(`${API}/api/research-model`));
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

export async function getProcessingCapabilities(): Promise<ProcessingCapabilities> {
  return parse(await fetch(`${API}/api/processing-capabilities`));
}

export async function inspectAssembly(fasta: string): Promise<AssemblyInspection> {
  return parse(
    await fetch(`${API}/api/inspect-assembly`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ fasta }),
    }),
  );
}

export async function extractIsolateLocus(fasta: string): Promise<IsolateLocusExtraction> {
  return parse(
    await fetch(`${API}/api/extract-isolate-locus`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ fasta }),
    }),
  );
}

export async function embedIsolateLocus(fasta: string): Promise<IsolateEmbedding> {
  return parse(
    await fetch(`${API}/api/embed-isolate-locus`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ fasta }),
    }),
  );
}

export async function rankNovelIsolateInBackground(fasta: string): Promise<NovelIsolateRank> {
  const job = await parse<{ job_id: string }>(
    await fetch(`${API}/api/jobs/novel-rank`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ fasta, limit: 20 }),
    }),
  );
  for (let attempt = 0; attempt < 800; attempt += 1) {
    const status = await parse<{ status: string; result?: NovelIsolateRank; error?: string }>(
      await fetch(`${API}/api/jobs/${job.job_id}`),
    );
    if (status.status === "succeeded" && status.result) return status.result;
    if (status.status === "failed" || status.status === "cancelled") {
      throw new Error(status.error || `Feature job ${status.status}.`);
    }
    await new Promise((resolve) => window.setTimeout(resolve, 750));
  }
  throw new Error("Feature job exceeded the local ten-minute limit.");
}
