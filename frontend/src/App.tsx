import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowRight,
  Check,
  ChevronDown,
  CircleDot,
  Dna,
  FlaskConical,
  Info,
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

function Results({ result, onReset }: { result: Analysis; onReset: () => void }) {
  return (
    <main className="results page-shell">
      <div className="results-head">
        <div>
          <span className="eyebrow"><Sparkles size={14} /> analysis complete</span>
          <h1>Candidate landscape for <em>{result.isolate.name}</em></h1>
          <p>{result.isolate.organism} · {result.isolate.sequence_type} · {result.isolate.k_locus}</p>
        </div>
        <button className="ghost-button" onClick={onReset}>New analysis</button>
      </div>

      <div className="validation-banner"><ShieldCheck size={18} /><strong>{result.disclaimer}</strong></div>

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
          <p className="method-note"><Info size={15} /> Compatibility + diversity − redundancy.</p>
        </article>

        <aside className="panel isolate-card">
          <span className="step-label">ISOLATE PROFILE</span>
          <h3>{result.isolate.name}</h3>
          <div className="profile-line"><span>Organism</span><strong>{result.isolate.organism}</strong></div>
          <div className="profile-line"><span>Sequence type</span><strong>{result.isolate.sequence_type}</strong></div>
          <div className="profile-line"><span>K locus</span><strong>{result.isolate.k_locus}</strong></div>
          <span className="profile-label">Resistance markers</span>
          <div className="tag-list">{result.isolate.resistance.map((tag) => <span key={tag}>{tag}</span>)}</div>
          <div className="model-chip"><CircleDot size={14} />{result.model}</div>
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

      <section className="limitations">
        <AlertTriangle size={20} />
        <div><h3>Limits</h3><p>Demo ranking only. Laboratory validation is required.</p></div>
      </section>
    </main>
  );
}

function ResearchResults({ result, onReset }: { result: ResearchRank; onReset: () => void }) {
  return (
    <main className="results page-shell">
      <div className="results-head">
        <div>
          <span className="eyebrow"><Network size={14} /> HELD-OUT RESEARCH BENCHMARK</span>
          <h1>Real-model ranking for <em>{result.host_id}</em></h1>
          <p>{result.feature_source} · {result.model_version}</p>
        </div>
        <button className="ghost-button" onClick={onReset}>New analysis</button>
      </div>
      <div className="validation-banner"><ShieldCheck size={18} /><strong>{result.disclaimer}</strong></div>
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

function NovelResults({ result, onReset }: { result: NovelIsolateRank; onReset: () => void }) {
  return (
    <main className="results page-shell">
      <div className="results-head"><div><span className="eyebrow"><Network size={14} /> NOVEL ISOLATE RESEARCH RANKING</span><h1>Real catalog ranking for <em>{result.locus}</em></h1><p>{result.model_version} · {result.species_ani_percent.toFixed(2)}% species ANI</p></div><button className="ghost-button" onClick={onReset}>New analysis</button></div>
      <div className="validation-banner"><ShieldCheck size={18} /><strong>{result.disclaimer}</strong></div>
      <section className="panel blocked-panel"><AlertTriangle size={24} /><div><span className="step-label">COCKTAIL {result.cocktail_status}</span><h2>Safety evidence required</h2><p>Real cocktails require reviewed genomic metadata and laboratory confirmation.</p></div></section>
      <section className="panel ranking-panel">
        <div className="panel-heading compact"><div><span className="step-label">105-PHAGE RBP CATALOG</span><h2>Ranked candidates</h2></div><span className="catalog-count">top {result.candidates.length}</span></div>
        <div className="research-ranking-head"><span>Rank</span><span>Phage ID</span><span>Decision</span><span>Score</span></div>
        {result.candidates.map((candidate, index) => <div className="research-row" key={candidate.phage_id}><span>{String(index + 1).padStart(2, "0")}</span><strong>{candidate.phage_id}</strong><em title={`${candidate.safety_status}. ${candidate.rationale.join(" ")}`}>{candidate.decision.replaceAll("-", " ")}</em><b>{Math.round(candidate.compatibility * 100)}%</b></div>)}
      </section>
      <section className="limitations"><Info size={20} /><div><h3>Input check</h3><p>{result.distribution_status.replaceAll("-", " ")} · similarity {result.nearest_reference_cosine.toFixed(3)}</p></div></section>
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
  const [fasta, setFasta] = useState(demoFasta);
  const [size, setSize] = useState(3);
  const [result, setResult] = useState<Analysis | null>(null);
  const [researchResult, setResearchResult] = useState<ResearchRank | null>(null);
  const [novelResult, setNovelResult] = useState<NovelIsolateRank | null>(null);
  const [loading, setLoading] = useState(false);
  const [featureLoading, setFeatureLoading] = useState(false);
  const [error, setError] = useState("");

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

  if (result) return <><Header /><Results result={result} onReset={() => setResult(null)} /></>;
  if (researchResult) return <><Header /><ResearchResults result={researchResult} onReset={() => setResearchResult(null)} /></>;
  if (novelResult) return <><Header /><NovelResults result={novelResult} onReset={() => setNovelResult(null)} /></>;

  return (
    <div className="app">
      <Header />
      <main className="page-shell hero-layout">
        <section className="hero-copy">
          <span className="eyebrow"><span className="live-dot" /> OFFLINE RESEARCH PROTOTYPE</span>
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
          <div className="panel-top"><span>01</span><div><h2>Choose an isolate</h2></div></div>
          <div className="tabs">
            <button className={mode === "demo" ? "active" : ""} onClick={() => setMode("demo")}>Demo cases</button>
            <button className={mode === "upload" ? "active" : ""} onClick={() => setMode("upload")}><Upload size={15} />Upload FASTA</button>
            <button className={mode === "research" ? "active" : ""} onClick={() => setMode("research")}><Network size={15} />Real benchmark</button>
          </div>

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
                <label className="file-control">
                  <Upload size={12} /> Choose .fasta
                  <input
                    type="file"
                    accept=".fasta,.fa,.fna,text/plain"
                    onChange={async (event) => {
                      const file = event.target.files?.[0];
                      if (file) { setFasta(await file.text()); setInspection(null); setLocusExtraction(null); setIsolateEmbedding(null); }
                    }}
                  />
                </label>
              </div>
              <textarea id="fasta" value={fasta} onChange={(event) => { setFasta(event.target.value); setInspection(null); setLocusExtraction(null); setIsolateEmbedding(null); }} spellCheck={false} />
              {capabilities && (
                <div className={`pipeline-state ${capabilities.novel_isolate_pipeline_ready ? "ready" : "blocked"}`}>
                  <strong>Real pipeline: {capabilities.novel_isolate_pipeline_ready ? "ready" : "blocked locally"}</strong>
                  <span>{capabilities.novel_isolate_pipeline_ready ? capabilities.esm2_model : `Missing: ${capabilities.blockers.join(", ")}`}</span>
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
                <strong>{modelStatus.model.replace("xgboost.", "")} · {modelStatus.candidate_phages} phages</strong>
                <span>Test AUROC {modelStatus.test_metrics.roc_auc.toFixed(3)} · Top-5 recall {Math.round(modelStatus.test_metrics.top_5_host_recall * 100)}% · Average precision {modelStatus.test_metrics.average_precision.toFixed(3)}</span>
                <small>{modelStatus.benchmark_hosts} held-out hosts · internal benchmark</small>
              </div>}
            </div>
          )}

          {mode !== "research" && <div className="size-picker"><span>Cocktail size</span><div>{[2, 3].map((n) => <button className={size === n ? "active" : ""} onClick={() => setSize(n)} key={n}>{n} phages</button>)}</div></div>}
          {error && <div className="error"><AlertTriangle size={16} />{error}</div>}
          <button className="run-button" onClick={run} disabled={loading || (mode === "demo" && !active) || (mode === "research" && !researchHost)}>
            {loading ? <><LoaderCircle className="spin" size={18} />Running compatibility model…</> : <>{mode === "research" ? "Run held-out benchmark" : mode === "upload" && capabilities?.novel_isolate_pipeline_ready ? "Run real catalog ranking" : "Run candidate discovery"} <ArrowRight size={18} /></>}
          </button>
          <p className="privacy"><ShieldCheck size={13} /> Runs locally.</p>
        </section>
      </main>
      <footer><span>PHAGE-X / 24H MVP</span></footer>
    </div>
  );
}

function Header() {
  return (
    <header>
      <div className="brand-mark"><Dna size={20} /><strong>PHAGE<span>—X</span></strong></div>
      <div className="header-meta"><span>K. pneumoniae</span><i /><span>v0.1</span></div>
    </header>
  );
}
