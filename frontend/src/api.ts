import type { Analysis, AssemblyInspection, Isolate, IsolateEmbedding, IsolateLocusExtraction, NovelIsolateRank, ProcessingCapabilities, ResearchModelStatus, ResearchRank } from "./types";

const API = import.meta.env.VITE_API_URL || (import.meta.env.PROD ? "" : "http://localhost:8000");

export function researchRankExportUrl(hostId: string): string {
  return `${API}/api/research-rank/${encodeURIComponent(hostId)}/export`;
}

export async function downloadNovelRankPdf(result: NovelIsolateRank): Promise<void> {
  let response: Response;
  try {
    response = await fetch(`${API}/api/novel-rank/export`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(result),
    });
  } catch (error) {
    if (error instanceof TypeError) throw new Error("The PHAGE-X backend is offline. Start the local API, then retry.");
    throw error;
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(typeof body.detail === "string" ? body.detail : "The PDF report could not be generated.");
  }
  const blob = await response.blob();
  if (blob.type !== "application/pdf") throw new Error("The server did not return a PDF report.");
  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  const safeLocus = result.locus.replace(/[^a-z0-9-]+/gi, "-").toLowerCase();
  anchor.href = objectUrl;
  anchor.download = `${safeLocus || "uploaded-isolate"}-phage-ranking.pdf`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1_000);
}

export async function getVerifiedSampleFasta(sampleId = "atcc-baa-2146"): Promise<string> {
  try {
    const response = await fetch(`${API}/api/verified-samples/${encodeURIComponent(sampleId)}/fasta`);
    if (!response.ok) throw new Error("The verified FASTA example is unavailable.");
    return response.text();
  } catch (error) {
    if (error instanceof TypeError) throw new Error("The PHAGE-X backend is offline. Start the local API, then retry.");
    throw error;
  }
}

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

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  try {
    return await parse<T>(await fetch(`${API}${path}`, init));
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error("The PHAGE-X backend is offline. Start the local API, then reload this page.");
    }
    throw error;
  }
}

export async function getIsolates(): Promise<Isolate[]> {
  return request("/api/isolates");
}

export async function analyze(payload: {
  isolate_id?: string;
  fasta?: string;
  isolate_name?: string;
  demo_fasta?: boolean;
  cocktail_size: number;
}): Promise<Analysis> {
  return request(
    "/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
  );
}

export async function getResearchIsolates(): Promise<string[]> {
  return request("/api/research-isolates");
}

export async function getResearchModelStatus(): Promise<ResearchModelStatus> {
  return request("/api/research-model");
}

export async function rankResearchHost(host_id: string): Promise<ResearchRank> {
  return request(
    "/api/research-rank", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ host_id, limit: 20 }),
    },
  );
}

export async function getProcessingCapabilities(): Promise<ProcessingCapabilities> {
  return request("/api/processing-capabilities");
}

export async function inspectAssembly(fasta: string): Promise<AssemblyInspection> {
  return request(
    "/api/inspect-assembly", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ fasta }),
    },
  );
}

export async function extractIsolateLocus(fasta: string): Promise<IsolateLocusExtraction> {
  return request(
    "/api/extract-isolate-locus", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ fasta }),
    },
  );
}

export async function embedIsolateLocus(fasta: string): Promise<IsolateEmbedding> {
  return request(
    "/api/embed-isolate-locus", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ fasta }),
    },
  );
}

export async function rankNovelIsolateInBackground(fasta: string): Promise<NovelIsolateRank> {
  const job = await request<{ job_id: string }>(
    "/api/jobs/novel-rank", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ fasta, limit: 20 }),
    },
  );
  for (let attempt = 0; attempt < 800; attempt += 1) {
    const status = await request<{ status: string; result?: NovelIsolateRank; error?: string }>(`/api/jobs/${job.job_id}`);
    if (status.status === "succeeded" && status.result) return status.result;
    if (status.status === "failed" || status.status === "cancelled") {
      throw new Error(status.error || `Feature job ${status.status}.`);
    }
    await new Promise((resolve) => window.setTimeout(resolve, 750));
  }
  throw new Error("Feature job exceeded the local ten-minute limit.");
}
