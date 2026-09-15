import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  Check,
  ChevronDown,
  Dna,
  FlaskConical,
  Layers3,
  LoaderCircle,
  Microscope,
  Network,
  ShieldCheck,
  Sparkles,
  Upload,
} from "lucide-react";
import { analyze, embedIsolateLocus, extractIsolateLocus, getIsolates, getProcessingCapabilities, getResearchIsolates, getResearchModelStatus, inspectAssembly, rankNovelIsolateInBackground, rankResearchHost } from "./api";
import type { Analysis, AssemblyInspection, Isolate, IsolateEmbedding, IsolateLocusExtraction, NovelIsolateRank, ProcessingCapabilities, RankedPhage, ResearchModelStatus, ResearchRank } from "./types";

const demoFasta = `>KPN-demo-upload
ACGTGGCTAACGTTGACCGTACGATCGATGCTAGCTACGATGCTAGGCTAACCGTTAGCATCGATCGTACGATGCTAGCTAGCGATCGTAGCTAACGTAGCTAGCATCGATCGATGCTAGCTAACGTAGCTAGCATCGATCGATGCTAGCTA`;

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
          <span className="eyebrow"><Sparkles size={14} /> analysis complete</span>
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
      </div>
      <section className="panel blocked-panel">
        <AlertTriangle size={24} />
        <div><span className="step-label">COCKTAIL {result.cocktail_status}</span><h2>Safety evidence required</h2>
          <p>Real cocktails stay blocked until genomic metadata and laboratory results are reviewed.</p>
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
      <div className="results-head"><div><span className="eyebrow"><Network size={14} /> NOVEL ISOLATE RESEARCH RANKING</span><h1>Real catalog ranking for <em>{result.locus}</em></h1><p>{result.species_ani_percent.toFixed(2)}% species match</p></div></div>
      <section className="panel blocked-panel"><AlertTriangle size={24} /><div><span className="step-label">COCKTAIL {result.cocktail_status}</span><h2>Safety evidence required</h2><p>Real cocktails require reviewed genomic metadata and laboratory confirmation.</p></div></section>
      <section className="panel ranking-panel">
        <div className="panel-heading compact"><div><span className="step-label">105-PHAGE RBP CATALOG</span><h2>Ranked candidates</h2></div><span className="catalog-count">top {result.candidates.length}</span></div>
        <div className="research-ranking-head"><span>Rank</span><span>Phage ID</span><span>Decision</span><span>Score</span></div>
        {result.candidates.map((candidate, index) => <div className="research-row" key={candidate.phage_id}><span>{String(index + 1).padStart(2, "0")}</span><strong>{candidate.phage_id}</strong><em title={`${candidate.safety_status}. ${candidate.rationale.join(" ")}`}>{candidate.decision.replaceAll("-", " ")}</em><b>{Math.round(candidate.compatibility * 100)}%</b></div>)}
      </section>
    </main>
  );
}

export default function App() {
  const [isolates, setIsolates] = useState<Isolate[]>([]);
  const [selected, setSelected] = useState("kp-mdr-001");
  const [mode, setMode] = useState<"demo" | "upload" | "research">("demo");
  const [researchIsolates, setResearchIsolates] = useState<string[]>([]);
  const [researchHost, setResearchHost] = useState("");
  const [modelStatus, setModelStatus] = useState<ResearchModelStatus | null>(null);
  const [capabilities, setCapabilities] = useState<ProcessingCapabilities | null>(null);
  const [inspection, setInspection] = useState<AssemblyInspection | null>(null);
  const [locusExtraction, setLocusExtraction] = useState<IsolateLocusExtraction | null>(null);
  const [isolateEmbedding, setIsolateEmbedding] = useState<IsolateEmbedding | null>(null);
  const [fasta, setFasta] = useState("");
  const [size, setSize] = useState(3);
  const [result, setResult] = useState<Analysis | null>(null);
  const [researchResult, setResearchResult] = useState<ResearchRank | null>(null);
  const [novelResult, setNovelResult] = useState<NovelIsolateRank | null>(null);
  const [loading, setLoading] = useState(false);
  const [featureLoading, setFeatureLoading] = useState(false);
  const [error, setError] = useState("");

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
      document.querySelectorAll(".panel, .results-head, .flow-strip").forEach((element) => {
        element.classList.add("scroll-reveal");
        observer.observe(element);
      });
      updateScroll();
    }, 0);
    window.addEventListener("scroll", updateScroll, { passive: true });
    return () => { window.clearTimeout(timer); window.removeEventListener("scroll", updateScroll); cancelAnimationFrame(frame); observer.disconnect(); };
  }, [result, researchResult, novelResult, mode]);

  useEffect(() => {
    getIsolates().then(setIsolates).catch((err) => setError(err.message));
    getResearchIsolates().then((items) => { setResearchIsolates(items); setResearchHost(items[0] || ""); }).catch((err) => setError(err.message));
    getProcessingCapabilities().then(setCapabilities).catch(() => undefined);
    getResearchModelStatus().then(setModelStatus).catch(() => undefined);
  }, []);

  const active = useMemo(() => isolates.find((item) => item.id === selected), [isolates, selected]);

  async function run() {
    setLoading(true);
    setError("");
    try {
      if (mode === "research") {
        setResearchResult(await rankResearchHost(researchHost));
      } else if (mode === "upload" && capabilities?.novel_isolate_pipeline_ready) {
        setNovelResult(await rankNovelIsolateInBackground(fasta));
      } else {
        const next = await analyze(mode === "demo"
          ? { isolate_id: selected, cocktail_size: size }
          : { fasta, isolate_name: "Uploaded KPN isolate", cocktail_size: size });
        setResult(next);
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
      <DnaBackdrop />
      <Header />
      <main className="page-shell hero-layout">
        <section className="hero-copy">
          <span className="eyebrow">OFFLINE RESEARCH PROTOTYPE</span>
          <h1>From bacterial isolate<br />to <em>phage shortlist.</em></h1>
          <p className="lead">Rank phages. Build complementary cocktails. Validate in the lab.</p>
          <div className="flow-strip">
            <div><Microscope /><span>Isolate</span></div><ArrowRight />
            <div><Network /><span>Embedding</span></div><ArrowRight />
            <div><Layers3 /><span>Ranking</span></div><ArrowRight />
            <div><FlaskConical /><span>Validate</span></div>
          </div>
          <div className="guardrail"><ShieldCheck size={18} /><div><strong>Lab validation required</strong></div></div>
        </section>

        <section className="input-panel panel">
          <div className="panel-top"><span>01</span><div><h2>Choose your input</h2></div></div>
          <div className="tabs">
            <button className={mode === "demo" ? "active" : ""} onClick={() => setMode("demo")}>Try a sample</button>
            <button className={mode === "upload" ? "active" : ""} onClick={() => setMode("upload")}><Upload size={15} />Use my FASTA</button>
            <button className={mode === "research" ? "active" : ""} onClick={() => setMode("research")}><Network size={15} />Test dataset</button>
          </div>
          <p className="mode-help">{mode === "demo" ? "Select a prepared Klebsiella case to see the complete workflow." : mode === "upload" ? "Choose a bacterial genome assembly in FASTA format, or load the included example." : "Choose a held-out isolate to inspect benchmark ranking performance."}</p>

          {mode === "demo" ? (
            <div className="case-list">
              {isolates.map((isolate) => (
                <button key={isolate.id} className={`case-option ${selected === isolate.id ? "selected" : ""}`} onClick={() => setSelected(isolate.id)}>
                  <span className="radio"><i /></span>
                  <span><strong>{isolate.name}</strong><small>{isolate.sequence_type} · {isolate.k_locus}</small></span>
                  {isolate.id === "kp-mdr-001" && <em>Featured</em>}
                </button>
              ))}
              {active && <div className="case-detail"><div className="tag-list">{active.resistance.map((tag) => <span key={tag}>{tag}</span>)}</div></div>}
            </div>
          ) : mode === "upload" ? (
            <div className="upload-area">
              <div className="upload-label-row">
                <label htmlFor="fasta">FASTA sequence</label>
                <div className="input-actions"><button type="button" className="file-control" onClick={() => setFasta(demoFasta)}>Load example</button><label className="file-control"><Upload size={12} /> Choose file<input type="file" accept=".fasta,.fa,.fna,text/plain" onChange={async (event) => { const file = event.target.files?.[0]; if (file) { setFasta(await file.text()); setInspection(null); setLocusExtraction(null); setIsolateEmbedding(null); } }} /></label></div>
              </div>
              <textarea id="fasta" value={fasta} onChange={(event) => { setFasta(event.target.value); setInspection(null); setLocusExtraction(null); setIsolateEmbedding(null); }} spellCheck={false} />
              {capabilities && (
                <div className={`pipeline-state ${capabilities.novel_isolate_pipeline_ready ? "ready" : "blocked"}`}>
                  <strong>Real pipeline: {capabilities.novel_isolate_pipeline_ready ? "ready" : "blocked locally"}</strong>
                  <span>{capabilities.novel_isolate_pipeline_ready ? "Sequence-processing tools available" : `Missing: ${capabilities.blockers.join(", ")}`}</span>
                </div>
              )}
              <button className="inspect-button" onClick={async () => {
                setError("");
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
              <label htmlFor="research-host">Held-out PhageHostLearn isolate</label>
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

          {mode !== "research" && <div className="size-picker"><span>02 · Choose shortlist size</span><div>{[2, 3].map((n) => <button className={size === n ? "active" : ""} onClick={() => setSize(n)} key={n}>{n} phages</button>)}</div></div>}
          {error && <div className="error"><AlertTriangle size={16} />{error}</div>}
          <button className="run-button" onClick={run} disabled={loading || (mode === "demo" && !active) || (mode === "upload" && !fasta.trim()) || (mode === "research" && !researchHost)}>
            {loading ? <><LoaderCircle className="spin" size={18} />Analyzing…</> : <>{mode === "research" ? "02 · Run benchmark" : "03 · Generate phage shortlist"} <ArrowRight size={18} /></>}
          </button>
          <p className="privacy"><ShieldCheck size={13} /> Runs locally.</p>
        </section>
      </main>
      <footer><span>PHAGE-X</span><span>Research output only · laboratory validation required</span></footer>
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
