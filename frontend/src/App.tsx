import { useEffect, useRef, useState } from "react";
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  Check,
  ChevronDown,
  Dna,
  Download,
  FlaskConical,
  Layers3,
  LoaderCircle,
  Microscope,
  Network,
  ShieldCheck,
  Sparkles,
  Upload,
} from "lucide-react";
import { apiDocsUrl, downloadNovelRankPdf, embedIsolateLocus, extractIsolateLocus, getProcessingCapabilities, getResearchIsolates, getResearchModelStatus, getVerifiedSampleFasta, inspectAssembly, rankNovelIsolateInBackground, rankResearchHost, researchRankExportUrl } from "./api";
import type { Analysis, AssemblyInspection, Isolate, IsolateEmbedding, IsolateLocusExtraction, NovelIsolateRank, ProcessingCapabilities, RankedPhage, ResearchModelStatus, ResearchRank } from "./types";

type DnaPoint = { x: number; y: number; z: number };
type DnaItem =
  | { z: number; kind: "strand"; a: DnaPoint; b: DnaPoint; strand: number }
  | { z: number; kind: "dot"; point: DnaPoint; strand: number }
  | { z: number; kind: "bond"; a: DnaPoint; b: DnaPoint; index: number };

function DnaBackdrop({ controls = false }: { controls?: boolean }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const progressRef = useRef<HTMLSpanElement>(null);
  const currentRef = useRef<HTMLSpanElement>(null);
  const reducedMotionRef = useRef(false);
  const pausedRef = useRef(false);
  const [paused, setPaused] = useState(false);

  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    reducedMotionRef.current = media.matches;
    pausedRef.current = media.matches;
    setPaused(media.matches);
    const onMotionPreference = (event: MediaQueryListEvent) => {
      reducedMotionRef.current = event.matches;
      if (event.matches) {
        pausedRef.current = true;
        setPaused(true);
      }
    };
    media.addEventListener("change", onMotionPreference);
    return () => media.removeEventListener("change", onMotionPreference);
  }, []);

  useEffect(() => {
    const canvasElement = canvasRef.current;
    if (!canvasElement) return;
    const canvas = canvasElement;
    const renderingContext = canvas.getContext("2d");
    if (!renderingContext) return;
    const context = renderingContext;

    let width = 0;
    let height = 0;
    let scroll = window.scrollY;
    let smooth = scroll;
    let angle = 0.4;
    let last = performance.now();
    let animationFrame = 0;
    const stageTop = (element: HTMLElement) => element.getBoundingClientRect().top + window.scrollY;
    const sections = [...document.querySelectorAll<HTMLElement>("[data-stage]")]
      .sort((first, second) => stageTop(first) - stageTop(second));

    function resize() {
      const density = Math.min(window.devicePixelRatio || 1, 2);
      width = canvas.clientWidth;
      height = canvas.clientHeight;
      canvas.width = width * density;
      canvas.height = height * density;
      context.setTransform(density, 0, 0, density, 0, 0);
    }

    function updateScroll() {
      scroll = window.scrollY;
      if (progressRef.current) {
        const available = Math.max(document.documentElement.scrollHeight - window.innerHeight, 1);
        progressRef.current.style.width = `${Math.min(100, (100 * scroll) / available)}%`;
      }
    }

    function line(a: DnaPoint, b: DnaPoint, color: string, weight: number) {
      context.beginPath();
      context.moveTo(a.x, a.y);
      context.lineTo(b.x, b.y);
      context.strokeStyle = color;
      context.lineWidth = weight;
      context.lineCap = "round";
      context.stroke();
    }

    function sphere(point: DnaPoint, radius: number, color: string, edge: string) {
      const gradient = context.createRadialGradient(point.x - radius * 0.3, point.y - radius * 0.35, 0, point.x, point.y, radius);
      gradient.addColorStop(0, color);
      gradient.addColorStop(0.45, color);
      gradient.addColorStop(1, edge);
      context.beginPath();
      context.arc(point.x, point.y, radius, 0, Math.PI * 2);
      context.fillStyle = gradient;
      context.fill();
    }

    function draw(time: number) {
      const delta = Math.min((time - last) / 1000, 0.05);
      last = time;
      if (!pausedRef.current) angle += delta * 0.16;
      smooth += (scroll - smooth) * 0.07;
      let stage = 0;
      for (let index = 1; index < sections.length; index += 1) {
        if (smooth + height * 0.5 > stageTop(sections[index])) stage = index;
      }
      if (currentRef.current) currentRef.current.textContent = String(stage + 1).padStart(2, "0");

      const separationAnchor = sections[3] ? stageTop(sections[3]) : Number.POSITIVE_INFINITY;
      const separation = Math.max(0, Math.min(1, (smooth - separationAnchor + height * 0.65) / (height * 0.85)));
      context.clearRect(0, 0, width, height);
      const radius = Math.min(width * 0.22, 180);
      const centerX = width * 0.52;
      const centerY = height * 0.51;
      const step = Math.min(height * 0.033, 28);
      const count = 34;
      const tilt = -0.21;
      const rotation = angle + (reducedMotionRef.current ? 0 : smooth * 0.0015);
      const points: [DnaPoint[], DnaPoint[]] = [[], []];
      const bonds: Array<{ a: DnaPoint; b: DnaPoint; index: number }> = [];

      function point(index: number, strand: number): DnaPoint {
        const theta = index * 0.43 + rotation + strand * Math.PI;
        const vertical = (index - (count - 1) / 2) * step;
        const spread = separation * radius * 0.75 * (strand ? 1 : -1);
        const horizontal = Math.sin(theta) * radius + spread;
        const depth = Math.cos(theta);
        return {
          x: centerX + horizontal * Math.cos(tilt) - vertical * Math.sin(tilt),
          y: centerY + horizontal * Math.sin(tilt) + vertical * Math.cos(tilt),
          z: depth,
        };
      }

      for (let index = 0; index < count; index += 1) {
        for (let strand = 0; strand < 2; strand += 1) points[strand].push(point(index, strand));
        bonds.push({ a: points[0][index], b: points[1][index], index });
      }

      const items: DnaItem[] = [];
      for (let strand = 0; strand < 2; strand += 1) {
        for (let index = 0; index < count; index += 1) {
          const current = points[strand][index];
          if (index < count - 1) items.push({ z: (current.z + points[strand][index + 1].z) / 2, kind: "strand", a: current, b: points[strand][index + 1], strand });
          items.push({ z: current.z, kind: "dot", point: current, strand });
        }
      }
      for (const bond of bonds) items.push({ z: 0, kind: "bond", ...bond });
      items.sort((a, b) => a.z - b.z);

      for (const item of items) {
        if (item.kind === "strand") {
          const light = (item.z + 1) / 2;
          line(item.a, item.b, item.strand ? `rgba(225,58,151,${0.35 + light * 0.65})` : `rgba(125,50,204,${0.35 + light * 0.65})`, 3.5 + light * 2);
        } else if (item.kind === "dot") {
          const light = (item.z + 1) / 2;
          sphere(item.point, 3.5 + light * 3, item.strand ? `rgb(${216 + light * 30},${72 + light * 50},${148 + light * 40})` : `rgb(${123 + light * 45},${55 + light * 45},${195 + light * 45})`, item.strand ? "#b52377" : "#6528a3");
        } else {
          const middle = { x: (item.a.x + item.b.x) / 2, y: (item.a.y + item.b.y) / 2, z: 0 };
          const gap = separation * 0.27;
          const start = { x: middle.x + (item.a.x - middle.x) * gap, y: middle.y + (item.a.y - middle.y) * gap, z: 0 };
          const end = { x: middle.x + (item.b.x - middle.x) * gap, y: middle.y + (item.b.y - middle.y) * gap, z: 0 };
          line(item.a, start, "rgba(125,50,204,.52)", 2);
          line(end, item.b, "rgba(225,58,151,.52)", 2);
          if (stage === 2 && item.index % 3 === 0) {
            const letters = item.index % 2 ? ["A", "T"] : ["C", "G"];
            context.font = "11px monospace";
            context.textAlign = "center";
            context.fillStyle = "#792cce";
            context.fillText(letters[0], item.a.x * 0.64 + middle.x * 0.36, item.a.y * 0.64 + middle.y * 0.36 - 9);
            context.fillStyle = "#c52c86";
            context.fillText(letters[1], item.b.x * 0.64 + middle.x * 0.36, item.b.y * 0.64 + middle.y * 0.36 - 9);
          }
        }
      }
      animationFrame = requestAnimationFrame(draw);
    }

    window.addEventListener("resize", resize);
    window.addEventListener("scroll", updateScroll, { passive: true });
    resize();
    updateScroll();
    animationFrame = requestAnimationFrame(draw);
    return () => {
      window.removeEventListener("resize", resize);
      window.removeEventListener("scroll", updateScroll);
      cancelAnimationFrame(animationFrame);
    };
  }, []);

  function toggleMotion() {
    const next = !pausedRef.current;
    pausedRef.current = next;
    setPaused(next);
  }

  return (
    <>
      <div className="dna-canvas-visual" aria-hidden="true"><canvas id="dna" ref={canvasRef} /></div>
      {controls && <>
        <div className="dna-progress" aria-hidden="true"><span id="progress-bar" ref={progressRef} /></div>
        <div className="dna-chapter" aria-label="Current scroll chapter"><span id="current" ref={currentRef}>01</span><i>/</i><span>05</span></div>
        <button id="motion" className="dna-motion" type="button" aria-pressed={paused} onClick={toggleMotion}>
          {paused ? <>Resume motion <span>▶</span></> : <>Pause motion <span>Ⅱ</span></>}
        </button>
      </>}
    </>
  );
}

function ScoreRing({ value, size = 74 }: { value: number; size?: number }) {
  const radius = 28;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - value);
  return (
    <div className="score-ring" style={{ width: size, height: size }}>
      <svg viewBox="0 0 68 68" aria-hidden="true">
        <circle className="score-track" cx="34" cy="34" r={radius} />
        <circle
          className="score-progress"
          cx="34"
          cy="34"
          r={radius}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>
      <strong>{Math.round(value * 100)}</strong>
    </div>
  );
}

function ExportResult({ href, onDownload }: { href?: string; onDownload?: () => Promise<void> }) {
  const [downloading, setDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState("");
  if (href) return <a className="result-export" href={href}><Download size={14} /> Download PDF</a>;
  if (!onDownload) return null;
  return <div className="export-action">
    <button className="result-export" type="button" disabled={downloading} onClick={async () => {
      setDownloading(true);
      setDownloadError("");
      try { await onDownload(); }
      catch (error) { setDownloadError(error instanceof Error ? error.message : "The PDF report could not be generated."); }
      finally { setDownloading(false); }
    }}><Download size={14} /> {downloading ? "Preparing PDF…" : "Download PDF"}</button>
    {downloadError && <span className="export-error" role="alert">{downloadError}</span>}
  </div>;
}

function EvidenceReviewNotice({ status = "blocked", blockers = [] }: { status?: string; blockers?: string[] }) {
  const pending = blockers.length ? blockers : ["The catalog does not yet contain enough independently reviewed phages."];
  return (
    <section className="evidence-note" role="note" aria-label="Combination evidence status">
      <div className="evidence-note-icon"><Layers3 size={20} /></div>
      <div className="evidence-note-copy">
        <span>Combination builder</span>
        <h2>{status === "blocked" ? "Ranking complete. Combination not issued." : "Combination candidate available"}</h2>
        {pending.map((item) => <p key={item}>{item}</p>)}
      </div>
      <div className="evidence-note-status"><i /> {status.replaceAll("-", " ")}</div>
    </section>
  );
}

function NovelCocktailResult({ result }: { result: NovelIsolateRank }) {
  if (!result.cocktail_members.length) {
    return <EvidenceReviewNotice status={result.cocktail_status} blockers={result.cocktail_blockers} />;
  }
  return (
    <section className="panel real-cocktail-card" aria-label="Reviewed cocktail candidate">
      <div className="panel-heading">
        <div><span className="step-label">REVIEWED COMBINATION</span><h2>Laboratory-validation candidate</h2></div>
        <ScoreRing value={result.cocktail_objective_score ?? 0} />
      </div>
      <div className="cocktail-map">
        {result.cocktail_members.map((member, index) => <div className="member-wrap" key={member}>
          <div className="phage-orb"><Dna size={22} /><span>P{index + 1}</span></div>
          {index < result.cocktail_members.length - 1 && <span className="connector">+</span>}
          <strong>{member}</strong><small>reviewed catalog phage</small>
        </div>)}
      </div>
      <div className="cocktail-metrics">
        <div><span>Mean compatibility</span><strong>{Math.round((result.cocktail_mean_compatibility ?? 0) * 100)}%</strong></div>
        <div><span>Family diversity</span><strong>{Math.round((result.cocktail_family_diversity ?? 0) * 100)}%</strong></div>
        <div><span>Receptor diversity</span><strong>{Math.round((result.cocktail_receptor_diversity ?? 0) * 100)}%</strong></div>
        <div><span>Redundancy</span><strong>{Math.round((result.cocktail_redundancy ?? 0) * 100)}%</strong></div>
      </div>
      <p className="cocktail-caveat">This is a computational research candidate. Laboratory confirmation is required before any downstream use.</p>
    </section>
  );
}

function PhageRow({ phage, rank }: { phage: RankedPhage; rank: number }) {
  const [open, setOpen] = useState(false);
  return (
    <div className={`phage-row ${open ? "open" : ""}`}>
      <button className="phage-summary" onClick={() => setOpen(!open)} aria-expanded={open}>
        <span className="rank">{String(rank).padStart(2, "0")}</span>
        <span className="phage-identity">
          <strong>{phage.name}</strong>
          <small>{phage.family} · {phage.receptor}</small>
        </span>
        <span className={`band ${phage.confidence_band}`}>{phage.confidence_band}</span>
        <span className="mini-score">{Math.round(phage.compatibility * 100)}%</span>
        <ChevronDown size={17} className="chevron" />
      </button>
      {open && (
        <div className="phage-details">
          <div>
            <h4>Why it ranked here</h4>
            {phage.rationale.map((item) => <p key={item}><Check size={14} />{item}</p>)}
            <p><AlertTriangle size={14} />Safety screen: {phage.safety_status}</p>
          </div>
          <div>
            <h4>Model contributions</h4>
            {phage.contributions.map((item) => (
              <div className="contribution" key={item.label}>
                <span>{item.label}</span><i style={{ width: `${Math.min(item.value / 2.4, 1) * 100}%` }} />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function ResearchCandidateRow({ candidate, rank }: { candidate: ResearchRank["candidates"][number]; rank: number }) {
  return (
    <div className="research-entry">
      <div className="research-row">
        <span>{String(rank).padStart(2, "0")}</span><strong>{candidate.phage_id}</strong>
        <em>{candidate.decision.replaceAll("-", " ")}</em><b>{Math.round(candidate.compatibility * 100)}%</b>
      </div>
      <details className="research-explanation">
        <summary>Why this candidate ranked here</summary>
        <div>
          <ul>{candidate.rationale.map((item) => <li key={item}>{item}</li>)}</ul>
          {!!candidate.attributions?.length && <section><span>Local XGBoost contributions to the raw model score</span>{candidate.attributions.map((item) => <p key={item.feature}><code>{item.feature}</code><strong>{item.contribution >= 0 ? "+" : ""}{item.contribution.toFixed(3)}</strong><small>{item.direction.replaceAll("-", " ")}</small></p>)}</section>}
        </div>
      </details>
    </div>
  );
}

function Results({ result }: { result: Analysis }) {
  return (
    <main className="results page-shell">
      <div className="results-head">
        <div>
          <span className="eyebrow"><Sparkles size={14} /> analysis complete · research use only</span>
          <h1>Candidate landscape for <em>{result.isolate.name}</em></h1>
          <p>{result.isolate.organism} · {result.isolate.sequence_type} · {result.isolate.k_locus}</p>
        </div>
      </div>

      <section className="result-grid">
        <article className="panel cocktail-card">
          <div className="panel-heading">
            <div><span className="step-label">PRIMARY OUTPUT</span><h2>Complementary cocktail</h2></div>
            <ScoreRing value={result.cocktail.objective_score} />
          </div>
          <div className="cocktail-map">
            {result.cocktail.members.map((member, index) => (
              <div className="member-wrap" key={member.phage_id}>
                <div className="phage-orb"><Dna size={22} /><span>P{index + 1}</span></div>
                {index < result.cocktail.members.length - 1 && <span className="connector">+</span>}
                <strong>{member.name}</strong><small>{member.role}</small>
              </div>
            ))}
          </div>
          <div className="metric-row">
            <div><span>Compatibility</span><strong>{Math.round(result.cocktail.compatibility * 100)}%</strong></div>
            <div><span>Diversity</span><strong>{Math.round(result.cocktail.diversity * 100)}%</strong></div>
            <div><span>Redundancy</span><strong>{Math.round(result.cocktail.redundancy * 100)}%</strong></div>
          </div>
        </article>

        <aside className="panel isolate-card">
          <span className="step-label">ISOLATE PROFILE</span>
          <h3>{result.isolate.name}</h3>
          <div className="profile-line"><span>Organism</span><strong>{result.isolate.organism}</strong></div>
          <div className="profile-line"><span>Sequence type</span><strong>{result.isolate.sequence_type}</strong></div>
          <div className="profile-line"><span>K locus</span><strong>{result.isolate.k_locus}</strong></div>
          <span className="profile-label">Resistance markers</span>
          <div className="tag-list">{result.isolate.resistance.map((tag) => <span key={tag}>{tag}</span>)}</div>
          {result.sequence_qc && (
            <div className="qc-card">
              <strong>Sequence QC: {result.sequence_qc.status}</strong>
              <span>{result.sequence_qc.length_bp.toLocaleString()} bp · {Math.round(result.sequence_qc.gc_fraction * 100)}% GC</span>
              <small>Feature source: {result.feature_source}</small>
            </div>
          )}
        </aside>
      </section>

      <section className="panel ranking-panel">
        <div className="panel-heading compact">
          <div><span className="step-label">EXPLAINABLE RANKING</span><h2>Candidate phages</h2></div>
          <span className="catalog-count">{result.ranked_phages.length} lytic candidates</span>
        </div>
        <div className="ranking-head"><span>Rank</span><span>Candidate</span><span>Band</span><span>Score</span><span /></div>
        {result.ranked_phages.map((phage, index) => <PhageRow phage={phage} rank={index + 1} key={phage.id} />)}
      </section>

    </main>
  );
}

function ResearchResults({ result }: { result: ResearchRank }) {
  return (
    <main className="results page-shell">
      <div className="results-head">
        <div>
          <span className="eyebrow"><Network size={14} /> HELD-OUT RESEARCH BENCHMARK</span>
          <h1>Real-model ranking for <em>{result.host_id}</em></h1>
          <p>Ranked against the available phage catalog</p>
        </div>
        <ExportResult href={researchRankExportUrl(result.host_id)} />
      </div>
      <EvidenceReviewNotice status={result.cocktail_status} blockers={result.cocktail_blockers} />
      <section className="panel ranking-panel">
        <div className="panel-heading compact"><div><span className="step-label">REAL PRECOMPUTED EMBEDDINGS</span><h2>Ranked dataset phages</h2></div><span className="catalog-count">top {result.candidates.length}</span></div>
        <div className="research-ranking-head"><span>Rank</span><span>Phage ID</span><span>Decision</span><span>Score</span></div>
        {result.candidates.map((candidate, index) => <ResearchCandidateRow candidate={candidate} rank={index + 1} key={candidate.phage_id} />)}
      </section>
    </main>
  );
}

function NovelResults({ result }: { result: NovelIsolateRank }) {
  return (
    <main className="results page-shell">
      <div className="results-head"><div><span className="eyebrow"><Network size={14} /> NOVEL ISOLATE RESEARCH RANKING</span><h1>Real catalog ranking for <em>{result.locus}</em></h1><p>{result.species_ani_percent.toFixed(2)}% species match</p></div><ExportResult onDownload={() => downloadNovelRankPdf(result)} /></div>
      <NovelCocktailResult result={result} />
      <section className="panel ranking-panel">
        <div className="panel-heading compact"><div><span className="step-label">105-PHAGE RBP CATALOG</span><h2>Ranked candidates</h2></div><span className="catalog-count">top {result.candidates.length}</span></div>
        <div className="research-ranking-head"><span>Rank</span><span>Phage ID</span><span>Decision</span><span>Score</span></div>
        {result.candidates.map((candidate, index) => <ResearchCandidateRow candidate={candidate} rank={index + 1} key={candidate.phage_id} />)}
      </section>
    </main>
  );
}

type SpeciesValidationFailure = {
  aniPercent: number;
  alignmentFraction: number;
};

function speciesValidationFailure(message: string): SpeciesValidationFailure | null {
  const match = message.match(/Species confirmation failed:\s*ANI\s*([\d.]+)%\s*and alignment fraction\s*([\d.]+)/i);
  if (!match) return null;
  return {
    aniPercent: Number(match[1]),
    alignmentFraction: Number(match[2]),
  };
}

function AnalysisError({ message }: { message: string }) {
  const cleanMessage = message.replace(/^\s*\d{3}:\s*/i, "");
  const speciesFailure = speciesValidationFailure(cleanMessage);
  if (!speciesFailure) {
    return <div className="error" role="alert"><AlertTriangle size={19} />{cleanMessage}</div>;
  }

  const observedAlignment = speciesFailure.alignmentFraction * 100;
  return (
    <section className="validation-result validation-mismatch" role="status" aria-labelledby="species-validation-title">
      <div className="validation-result-icon"><ShieldCheck size={24} /></div>
      <div className="validation-result-copy">
        <span>INPUT CHECK COMPLETE · OUTSIDE SUPPORTED RANGE</span>
        <h3 id="species-validation-title">This assembly does not match the model’s supported <em>K. pneumoniae</em> reference range.</h3>
        <p>The app is working and the FASTA passed basic assembly checks. Ranking stopped intentionally because both species-similarity measures are below the validated input thresholds.</p>
        <div className="validation-measures">
          <div>
            <span>Average nucleotide identity</span>
            <strong>{speciesFailure.aniPercent.toFixed(2)}%</strong>
            <small>Required: at least 95%</small>
          </div>
          <div>
            <span>Genome alignment coverage</span>
            <strong>{observedAlignment.toFixed(1)}%</strong>
            <small>Required: at least 65%</small>
          </div>
        </div>
        <p className="validation-next"><strong>Next step:</strong> upload a complete <em>K. pneumoniae</em> genome assembly, or choose “Load verified K. pneumoniae” to run the full workflow.</p>
      </div>
    </section>
  );
}

export default function App() {
  const [mode, setMode] = useState<"demo" | "upload" | "research">("demo");
  const [researchIsolates, setResearchIsolates] = useState<string[]>([]);
  const [researchHost, setResearchHost] = useState("");
  const [modelStatus, setModelStatus] = useState<ResearchModelStatus | null>(null);
  const [capabilities, setCapabilities] = useState<ProcessingCapabilities | null>(null);
  const [inspection, setInspection] = useState<AssemblyInspection | null>(null);
  const [locusExtraction, setLocusExtraction] = useState<IsolateLocusExtraction | null>(null);
  const [isolateEmbedding, setIsolateEmbedding] = useState<IsolateEmbedding | null>(null);
  const [fasta, setFasta] = useState("");
  const [result, setResult] = useState<Analysis | null>(null);
  const [researchResult, setResearchResult] = useState<ResearchRank | null>(null);
  const [novelResult, setNovelResult] = useState<NovelIsolateRank | null>(null);
  const [loading, setLoading] = useState(false);
  const [featureLoading, setFeatureLoading] = useState(false);
  const [sampleLoading, setSampleLoading] = useState(false);
  const [error, setError] = useState("");
  const [draggingFile, setDraggingFile] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  function resetUploadChecks() {
    setInspection(null);
    setLocusExtraction(null);
    setIsolateEmbedding(null);
    setError("");
  }

  function changeMode(nextMode: "demo" | "upload" | "research") {
    setMode(nextMode);
    setError("");
  }

  function validateFastaInput(value: string): string | null {
    const trimmed = value.trim();
    if (!trimmed) return "Choose a FASTA file or load the example first.";
    if (!trimmed.startsWith(">")) return "FASTA must begin with a header line starting with >, followed by the DNA sequence.";
    const bases = trimmed.split(/\r?\n/).filter((line) => !line.startsWith(">") && line.trim()).join("").replace(/\s/g, "");
    if (bases.length < 100) return "This sequence is too short. Provide at least 100 DNA bases.";
    if (/[^ACGTN]/i.test(bases)) return "The sequence contains unsupported characters. Use only A, C, G, T, or N.";
    return null;
  }

  async function loadFastaFile(file: File) {
    if (file.size > 15_000_000) { setError("The selected file is larger than the 15 MB limit."); return; }
    const contents = await file.text();
    setFasta(contents);
    resetUploadChecks();
  }

  useEffect(() => {
    let frame = 0;
    const updateScroll = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => {
        const progress = Math.min(window.scrollY / Math.max(document.body.scrollHeight - window.innerHeight, 1), 1);
        // Move from Apple blue to a restrained violet as the story progresses.
        const hue = 211 + progress * 45;
        document.documentElement.style.setProperty("--scroll-y", `${window.scrollY}`);
        document.documentElement.style.setProperty("--scroll-progress", `${progress}`);
        document.documentElement.style.setProperty("--mint", `hsl(${hue} 88% 66%)`);
        document.documentElement.style.setProperty("--accent-rgb", progress < 0.5 ? "52, 211, 255" : "156, 120, 255");
      });
    };
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => entry.target.classList.toggle("is-visible", entry.isIntersecting));
    }, { threshold: 0.12 });
    const timer = window.setTimeout(() => {
      document.querySelectorAll(".panel, .results-head, .flow-strip, .story-card").forEach((element) => {
        element.classList.add("scroll-reveal");
        observer.observe(element);
      });
      updateScroll();
    }, 0);
    window.addEventListener("scroll", updateScroll, { passive: true });
    return () => { window.clearTimeout(timer); window.removeEventListener("scroll", updateScroll); cancelAnimationFrame(frame); observer.disconnect(); };
  }, [result, researchResult, novelResult, mode]);

  useEffect(() => {
    getResearchIsolates().then((items) => { setResearchIsolates(items); setResearchHost(items[0] || ""); }).catch((err) => setError(err.message));
    getProcessingCapabilities().then(setCapabilities).catch(() => undefined);
    getResearchModelStatus().then(setModelStatus).catch(() => undefined);
  }, []);

  async function run() {
    if (mode === "upload") {
      const validationError = validateFastaInput(fasta);
      if (validationError) { setError(validationError); return; }
    }
    setLoading(true);
    setError("");
    try {
      if (mode === "research" || mode === "demo") {
        setResearchResult(await rankResearchHost(researchHost));
      } else if (mode === "upload") {
        if (!capabilities?.novel_isolate_pipeline_ready) {
          throw new Error("The real uploaded-genome ML pipeline is unavailable. Install the listed local tools; no demo fallback was used.");
        }
        setNovelResult(await rankNovelIsolateInBackground(fasta));
      }
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  }

  if (result) return <><DnaBackdrop /><Header onBack={() => setResult(null)} /><Results result={result} /></>;
  if (researchResult) return <><DnaBackdrop /><Header onBack={() => setResearchResult(null)} /><ResearchResults result={researchResult} /></>;
  if (novelResult) return <><DnaBackdrop /><Header onBack={() => setNovelResult(null)} /><NovelResults result={novelResult} /></>;

  return (
    <div className="app">
      <Header />
      <DnaBackdrop controls />
      <main className="page-shell hero-layout">
        <section className="hero-stage" data-stage="hero">
          <div className="hero-copy">
            <span className="eyebrow">AI-GUIDED PHAGE DISCOVERY</span>
            <h1>From bacterial isolate<br />to <em>phage shortlist.</em></h1>
            <p className="lead">Rank phages. Build complementary cocktails. Validate in the lab.</p>
            <div className="flow-strip">
              <div><Microscope /><span>Isolate</span></div><ArrowRight />
              <div><Network /><span>Embedding</span></div><ArrowRight />
              <div><Layers3 /><span>Ranking</span></div><ArrowRight />
              <div><FlaskConical /><span>Validate</span></div>
            </div>
            <button className="hero-cta" onClick={() => document.querySelector(".input-panel")?.scrollIntoView({ behavior: "smooth", block: "start" })}>Start analysis <ArrowRight size={17} /></button>
          </div>
          <div className="hero-visual"><span>GENOME / RECEPTOR / MATCH</span></div>
        </section>

        <section className="scroll-story" aria-label="How PHAGE-X works">
          <article className="story-card" data-stage="represent">
            <span>01 / REPRESENT</span>
            <h2>Read the bacterial surface.</h2>
            <p>The sequence pipeline checks the assembly, confirms the species, identifies the capsule locus, and turns its proteins into comparable features.</p>
            <small>Input → assembly QC → capsule-locus proteins → embedding</small>
          </article>
          <article className="story-card" data-stage="rank">
            <span>02 / RANK</span>
            <h2>Search fewer candidates.</h2>
            <p>The compatibility model compares the isolate representation with receptor-binding-protein features and orders the available phage catalog.</p>
            <small>{modelStatus ? `${modelStatus.candidate_phages} catalog phages · ${Math.round(modelStatus.test_metrics.top_5_host_recall * 100)}% internal top-5 recall` : "Explainable catalog ranking"}</small>
          </article>
          <article className="story-card" data-stage="combine">
            <span>03 / COMBINE</span>
            <h2>Avoid redundant choices.</h2>
            <p>The shortlist favors individually strong candidates that add receptor and family diversity instead of repeating the same profile.</p>
            <small>Compatibility · receptor diversity · family diversity</small>
          </article>
        </section>

        <section className="input-panel panel" data-stage="analyse">
          <div className="panel-top"><span>01</span><div><h2>Choose your input</h2></div></div>
          <div className="tabs">
            <button className={mode === "demo" ? "active" : ""} onClick={() => changeMode("demo")}>XGBoost sample</button>
            <button className={mode === "upload" ? "active" : ""} onClick={() => changeMode("upload")}><Upload size={15} />Use my FASTA</button>
            <button className={mode === "research" ? "active" : ""} onClick={() => changeMode("research")}><Network size={15} />Model validation</button>
          </div>
          <p className="mode-help">{mode === "demo" ? "Choose a real held-out Klebsiella isolate with precomputed protein features. Generate calls the trained XGBoost model." : mode === "upload" ? "Upload any complete K. pneumoniae genome assembly in FASTA format. It does not need to be pre-registered or included with PHAGE-X." : "Validate the trained model on isolates it never saw during training. This checks whether known interacting phages are ranked near the top; it does not analyze a new FASTA file."}</p>

          {mode === "demo" ? (
            <div className="case-list">
              {researchIsolates.slice(0, 3).map((isolate) => (
                <button key={isolate} className={`case-option ${researchHost === isolate ? "selected" : ""}`} onClick={() => setResearchHost(isolate)}>
                  <span className="radio"><i /></span>
                  <span><strong>{isolate}</strong><small>Held-out <em>K. pneumoniae</em> isolate</small></span>
                </button>
              ))}
              {researchHost && <div className="case-detail">
                <div className="case-detail-head"><span>Selected isolate</span><strong>{researchHost}</strong></div>
                <p>This isolate was excluded from model training. Its released protein embeddings are used to test how the trained model ranks unseen host-phage pairs.</p>
                <div className="case-facts">
                  <div><span>Organism</span><strong><em>K.</em> pneumoniae</strong></div>
                  <div><span>Model role</span><strong>Held-out test</strong></div>
                  <div><span>Catalog</span><strong>105 phages</strong></div>
                </div>
              </div>}
            </div>
          ) : mode === "upload" ? (
            <div className={`upload-area ${draggingFile ? "dragging" : ""}`} onDragOver={(event) => { event.preventDefault(); setDraggingFile(true); }} onDragLeave={(event) => { if (!event.currentTarget.contains(event.relatedTarget as Node | null)) setDraggingFile(false); }} onDrop={(event) => { event.preventDefault(); setDraggingFile(false); const file = event.dataTransfer.files[0]; if (file) void loadFastaFile(file); }}>
              <div className="organism-scope">
                <span>Supported organism</span>
                <strong><em>K</em>lebsiella pneumoniae species complex</strong>
                <small>New isolates are accepted after genome QC and species confirmation. Other organisms require their own validated host–phage dataset, phage catalog, receptor features, and species reference.</small>
              </div>
              <div className="upload-label-row">
                <label htmlFor="fasta">FASTA sequence</label>
                <div className="input-actions">
                  <button type="button" className="file-control verified-sample" disabled={sampleLoading} onClick={async () => {
                    setSampleLoading(true);
                    setError("");
                    try {
                      setFasta(await getVerifiedSampleFasta());
                      resetUploadChecks();
                    } catch (err) {
                      setError(err instanceof Error ? err.message : "Could not load the verified sample");
                    } finally {
                      setSampleLoading(false);
                    }
                  }}>{sampleLoading ? "Loading verified assembly…" : "Load verified K. pneumoniae"}</button>
                  <button type="button" className="file-control choose-file" onClick={() => fileInputRef.current?.click()}><Upload size={12} /> Choose FASTA file</button>
                  <input ref={fileInputRef} className="native-file-input" type="file" accept=".fasta,.fa,.fna,text/plain" onChange={(event) => { const file = event.target.files?.[0]; if (file) void loadFastaFile(file); event.target.value = ""; }} />
                </div>
              </div>
              <span className="drop-hint">or drop a FASTA file anywhere in this area</span>
              <p className="fasta-format"><strong>Expected format</strong><code>&gt;isolate-name<br />ACGTACGTACGT...</code><span>Whole-genome assemblies may contain multiple FASTA records. Maximum uncompressed file size: 15 MB.</span></p>
              <textarea id="fasta" placeholder={">isolate-name\nACGTACGTACGT..."} value={fasta} onChange={(event) => { setFasta(event.target.value); resetUploadChecks(); }} spellCheck={false} />
              {capabilities && (
                <div className={`pipeline-state ${capabilities.novel_isolate_pipeline_ready ? "ready" : "blocked"}`}>
                  <strong>Uploaded-genome ML: {capabilities.novel_isolate_pipeline_ready ? "ready" : "unavailable"}</strong>
                  <span>{capabilities.novel_isolate_pipeline_ready ? "Sequence-processing tools available" : `Missing: ${capabilities.blockers.join(", ")}`}</span>
                </div>
              )}
              <div className="ml-path">
                <div><span>01</span><strong>Assembly QC</strong><small>Validate the uploaded genome</small></div>
                <div><span>02</span><strong>Species + capsule</strong><small>fastANI and Kaptive</small></div>
                <div><span>03</span><strong>Protein features</strong><small>Local ESM-2 embeddings</small></div>
                <div><span>04</span><strong>Phage ranking</strong><small>Calibrated XGBoost, 105 phages</small></div>
                <a href={apiDocsUrl()} target="_blank" rel="noreferrer">Open FastAPI routes ↗</a>
              </div>
              <button className="inspect-button" onClick={async () => {
                setError("");
                const validationError = validateFastaInput(fasta);
                if (validationError) { setError(validationError); return; }
                try { setInspection(await inspectAssembly(fasta)); }
                catch (err) { setError(err instanceof Error ? err.message : "Inspection failed"); }
              }}>Check assembly</button>
              {inspection && <div className="inspection-result"><strong>Assembly: {inspection.qc_status}</strong><span>{inspection.contig_count} contig(s) · {inspection.total_length_bp.toLocaleString()} bp · N50 {inspection.n50_bp.toLocaleString()}</span></div>}
              {inspection?.qc_status === "pass" && capabilities?.tools.kaptive && capabilities?.tools.minimap2 && (
                <button className="inspect-button" onClick={async () => {
                  setError(""); setLocusExtraction(null);
                  try { setLocusExtraction(await extractIsolateLocus(fasta)); }
                  catch (err) { setError(err instanceof Error ? err.message : "K-locus extraction failed"); }
                }}>Extract K-locus</button>
              )}
              {locusExtraction && <div className="inspection-result"><strong>{locusExtraction.locus} · {locusExtraction.confidence}</strong><span>{locusExtraction.protein_count} proteins · {locusExtraction.species_ani_percent.toFixed(2)}% ANI</span></div>}
              {locusExtraction && capabilities?.novel_isolate_pipeline_ready && (
                <button className="inspect-button" disabled={featureLoading} onClick={async () => {
                  setError(""); setIsolateEmbedding(null); setFeatureLoading(true);
                  try { setIsolateEmbedding(await embedIsolateLocus(fasta)); }
                  catch (err) { setError(err instanceof Error ? err.message : "ESM-2 embedding failed"); }
                  finally { setFeatureLoading(false); }
                }}>{featureLoading ? "Generating ESM-2…" : "Generate ESM-2 feature"}</button>
              )}
              {isolateEmbedding && <div className="inspection-result"><strong>ESM-2 ready</strong><span>{isolateEmbedding.dimensions.toLocaleString()} dimensions</span></div>}
            </div>
          ) : (
            <div className="research-picker">
              <section className="benchmark-purpose">
                <div><Network size={20} /></div>
                <span>WHAT THIS TAB DOES</span>
                <h3>Tests whether the model retrieves known phage matches.</h3>
                <p>Select a held-out isolate with known interaction labels. PHAGE-X ranks all 105 candidate phages, then you can compare its shortlist with the known results and review Top-5 recall, ROC-AUC, PR-AUC, and positive recall.</p>
                <small>Use “My FASTA” for a new genome. Use this tab only to show model evaluation evidence.</small>
              </section>
              <label htmlFor="research-host">Known isolate excluded from model training</label>
              <select id="research-host" value={researchHost} onChange={(event) => setResearchHost(event.target.value)}>
                {researchIsolates.map((item) => <option value={item} key={item}>{item}</option>)}
              </select>
              {modelStatus && <div className="inspection-result">
                <strong>Kaggle-trained XGBoost · {modelStatus.candidate_phages} candidate phages</strong>
                <span>Test AUROC {modelStatus.test_metrics.roc_auc.toFixed(3)} · PR-AUC {modelStatus.test_metrics.average_precision.toFixed(3)} · Top-5 recall {Math.round(modelStatus.test_metrics.top_5_host_recall * 100)}%</span>
                <small>{Math.round(modelStatus.test_metrics.accuracy * 1000) / 10}% raw accuracy · {Math.round(modelStatus.test_metrics.balanced_accuracy * 1000) / 10}% balanced accuracy · {modelStatus.benchmark_hosts} held-out hosts</small>
              </div>}
              {modelStatus && <section className="model-evidence" aria-label="Model evaluation evidence">
                <div className="evidence-intro">
                  <span>WHAT THE EVALUATION SHOWS</span>
                  <h3>The model is useful for narrowing the search.</h3>
                  <p>Top-5 recall is the clearest product metric: for almost nine out of ten evaluable held-out hosts with a known interaction, a matching phage appeared within the first five candidates.</p>
                </div>
                <div className="evidence-metrics">
                  <div><strong>{Math.round(modelStatus.test_metrics.top_5_host_recall * 100)}%</strong><span>Top-5 host recall</span><small>Shortlist retrieval</small></div>
                  <div><strong>{modelStatus.test_metrics.roc_auc.toFixed(3)}</strong><span>ROC-AUC</span><small>Ranking separation</small></div>
                  <div><strong>{modelStatus.test_metrics.average_precision.toFixed(3)}</strong><span>PR-AUC</span><small>Positive-pair quality</small></div>
                  <div><strong>{Math.round(modelStatus.test_metrics.recall * 100)}%</strong><span>Positive recall</span><small>Thresholded detection</small></div>
                </div>
                <p className="evidence-caveat"><AlertTriangle size={14} /> Raw accuracy is not the headline metric because only 3.3% of evaluated pairs are positive. This evidence supports candidate prioritization, not automatic susceptibility or treatment decisions.</p>
              </section>}
            </div>
          )}

          {error && <AnalysisError message={error} />}
          <button className="run-button" onClick={run} disabled={loading || ((mode === "demo" || mode === "research") && !researchHost) || (mode === "upload" && (!fasta.trim() || !capabilities?.novel_isolate_pipeline_ready))}>
            {loading ? <><LoaderCircle className="spin" size={18} />Running XGBoost…</> : <>{mode === "upload" ? capabilities?.novel_isolate_pipeline_ready ? "Run uploaded-genome XGBoost ranking" : "Real ML pipeline unavailable" : "Run XGBoost ranking"} <ArrowRight size={18} /></>}
          </button>
          <p className="privacy"><ShieldCheck size={13} /> Runs locally.</p>
        </section>
      </main>
      <footer><span>PHAGE-X</span></footer>
    </div>
  );
}

function Header({ onBack }: { onBack?: () => void }) {
  return (
    <header>
      <div className="header-left">
        {onBack && <button className="header-back" onClick={onBack}><ArrowLeft size={16} /> Back</button>}
        <div className="brand-mark"><Dna size={20} /><strong>PHAGE<span>—X</span></strong></div>
      </div>
      <div className="header-meta"><span>K. pneumoniae</span></div>
    </header>
  );
}
