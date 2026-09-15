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
import { embedIsolateLocus, extractIsolateLocus, getProcessingCapabilities, getResearchIsolates, getResearchModelStatus, inspectAssembly, rankNovelIsolateInBackground, rankResearchHost } from "./api";
import type { Analysis, AssemblyInspection, Isolate, IsolateEmbedding, IsolateLocusExtraction, NovelIsolateRank, ProcessingCapabilities, RankedPhage, ResearchModelStatus, ResearchRank } from "./types";

function DnaBackdrop() {
  return (
    <div className="dna-scene" aria-hidden="true">
      <img src="/assets/dna-hero.png" alt="" />
    </div>
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

function ExportResult({ data, name }: { data: unknown; name: string }) {
  function download() {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${name.replace(/[^a-z0-9-]+/gi, "-").toLowerCase()}-phage-ranking.json`;
    link.click();
    URL.revokeObjectURL(url);
  }
  return <button className="result-export" onClick={download}><Download size={14} /> Export results</button>;
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

function Results({ result }: { result: Analysis }) {
  return (
    <main className="results page-shell">
      <div className="results-head">
        <div>
          <span className="eyebrow"><Sparkles size={14} /> analysis complete · research use only</span>
          <h1>Candidate landscape for <em>{result.isolate.name}</em></h1>
          <p>{result.isolate.organism} · {result.isolate.sequence_type} · {result.isolate.k_locus}</p>
        </div>
        <ExportResult data={result} name={result.isolate.name} />
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
        <ExportResult data={result} name={result.host_id} />
      </div>
      <section className="panel blocked-panel">
        <AlertTriangle size={24} />
        <div><span className="step-label">COCKTAIL {result.cocktail_status}</span><h2>Catalog evidence incomplete</h2>
          <p>Combination output is unavailable until the catalog metadata is reviewed.</p>
        </div>
      </section>
      <section className="panel ranking-panel">
        <div className="panel-heading compact"><div><span className="step-label">REAL PRECOMPUTED EMBEDDINGS</span><h2>Ranked dataset phages</h2></div><span className="catalog-count">top {result.candidates.length}</span></div>
        <div className="research-ranking-head"><span>Rank</span><span>Phage ID</span><span>Decision</span><span>Score</span></div>
        {result.candidates.map((candidate, index) => (
          <div className="research-row" key={candidate.phage_id}>
            <span>{String(index + 1).padStart(2, "0")}</span><strong>{candidate.phage_id}</strong>
            <em title={`${candidate.safety_status}. ${candidate.rationale.join(" ")}`}>{candidate.decision.replaceAll("-", " ")}</em><b>{Math.round(candidate.compatibility * 100)}%</b>
          </div>
        ))}
      </section>
    </main>
  );
}

function NovelResults({ result }: { result: NovelIsolateRank }) {
  return (
    <main className="results page-shell">
      <div className="results-head"><div><span className="eyebrow"><Network size={14} /> NOVEL ISOLATE RESEARCH RANKING</span><h1>Real catalog ranking for <em>{result.locus}</em></h1><p>{result.species_ani_percent.toFixed(2)}% species match</p></div><ExportResult data={result} name={result.locus} /></div>
      <section className="panel blocked-panel"><AlertTriangle size={24} /><div><span className="step-label">COCKTAIL {result.cocktail_status}</span><h2>Catalog evidence incomplete</h2><p>Combination output is unavailable until the catalog metadata is reviewed.</p></div></section>
      <section className="panel ranking-panel">
        <div className="panel-heading compact"><div><span className="step-label">105-PHAGE RBP CATALOG</span><h2>Ranked candidates</h2></div><span className="catalog-count">top {result.candidates.length}</span></div>
        <div className="research-ranking-head"><span>Rank</span><span>Phage ID</span><span>Decision</span><span>Score</span></div>
        {result.candidates.map((candidate, index) => <div className="research-row" key={candidate.phage_id}><span>{String(index + 1).padStart(2, "0")}</span><strong>{candidate.phage_id}</strong><em title={`${candidate.safety_status}. ${candidate.rationale.join(" ")}`}>{candidate.decision.replaceAll("-", " ")}</em><b>{Math.round(candidate.compatibility * 100)}%</b></div>)}
      </section>
    </main>
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
  const [error, setError] = useState("");
  const [draggingFile, setDraggingFile] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  function resetUploadChecks() {
    setInspection(null);
    setLocusExtraction(null);
    setIsolateEmbedding(null);
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
      <DnaBackdrop />
      <main className="page-shell hero-layout">
        <section className="hero-stage">
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
          <article className="story-card">
            <span>01 / REPRESENT</span>
            <h2>Read the bacterial surface.</h2>
            <p>The sequence pipeline checks the assembly, confirms the species, identifies the capsule locus, and turns its proteins into comparable features.</p>
            <small>Input → assembly QC → capsule-locus proteins → embedding</small>
          </article>
          <article className="story-card">
            <span>02 / RANK</span>
            <h2>Search fewer candidates.</h2>
            <p>The compatibility model compares the isolate representation with receptor-binding-protein features and orders the available phage catalog.</p>
            <small>{modelStatus ? `${modelStatus.candidate_phages} catalog phages · ${Math.round(modelStatus.test_metrics.top_5_host_recall * 100)}% internal top-5 recall` : "Explainable catalog ranking"}</small>
          </article>
          <article className="story-card">
            <span>03 / COMBINE</span>
            <h2>Avoid redundant choices.</h2>
            <p>The shortlist favors individually strong candidates that add receptor and family diversity instead of repeating the same profile.</p>
            <small>Compatibility · receptor diversity · family diversity</small>
          </article>
        </section>

        <section className="input-panel panel">
          <div className="panel-top"><span>01</span><div><h2>Choose your input</h2></div></div>
          <div className="tabs">
            <button className={mode === "demo" ? "active" : ""} onClick={() => setMode("demo")}>XGBoost sample</button>
            <button className={mode === "upload" ? "active" : ""} onClick={() => setMode("upload")}><Upload size={15} />Use my FASTA</button>
            <button className={mode === "research" ? "active" : ""} onClick={() => setMode("research")}><Network size={15} />Model benchmark</button>
          </div>
          <p className="mode-help">{mode === "demo" ? "Choose a real held-out Klebsiella isolate with precomputed protein features. Generate calls the trained XGBoost model." : mode === "upload" ? "Upload a bacterial genome assembly in FASTA format. The file must start with a > header line." : "Checks the model on known isolates that were excluded from training. Use this to demonstrate model performance, not to analyze your own sequence."}</p>

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
                <small>Other organisms require their own validated host–phage dataset, phage catalog, receptor features, and species reference.</small>
              </div>
              <div className="upload-label-row">
                <label htmlFor="fasta">FASTA sequence</label>
                <div className="input-actions">
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
                <a href="http://127.0.0.1:8000/docs" target="_blank" rel="noreferrer">Open FastAPI routes ↗</a>
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
              <label htmlFor="research-host">Known isolate excluded from model training</label>
              <select id="research-host" value={researchHost} onChange={(event) => setResearchHost(event.target.value)}>
                {researchIsolates.map((item) => <option value={item} key={item}>{item}</option>)}
              </select>
              {modelStatus && <div className="inspection-result">
                <strong>{modelStatus.candidate_phages} candidate phages</strong>
                <span>Test AUROC {modelStatus.test_metrics.roc_auc.toFixed(3)} · Top-5 recall {Math.round(modelStatus.test_metrics.top_5_host_recall * 100)}% · Average precision {modelStatus.test_metrics.average_precision.toFixed(3)}</span>
                <small>{modelStatus.benchmark_hosts} held-out hosts · internal benchmark</small>
              </div>}
            </div>
          )}

          {error && <div className="error"><AlertTriangle size={16} />{error}</div>}
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
