export type Isolate = {
  id: string;
  name: string;
  organism: string;
  sequence_type: string;
  k_locus: string;
  resistance: string[];
  description: string;
};

export type Contribution = { label: string; value: number; direction: string };

export type RankedPhage = {
  id: string;
  name: string;
  family: string;
  receptor: string;
  compatibility: number;
  confidence_band: string;
  rationale: string[];
  contributions: Contribution[];
  evidence: string;
  safety_status: string;
};

export type Analysis = {
  analysis_id: string;
  isolate: Isolate;
  input_mode: string;
  feature_source: string;
  sequence_qc?: {
    sequence_sha256: string;
    length_bp: number;
    gc_fraction: number;
    ambiguous_fraction: number;
    status: string;
    warnings: string[];
  } | null;
  model: string;
  ranked_phages: RankedPhage[];
  cocktail: {
    members: { phage_id: string; name: string; role: string; compatibility: number }[];
    compatibility: number;
    diversity: number;
    redundancy: number;
    objective_score: number;
    rationale: string[];
    constraints_passed: string[];
  };
  limitations: string[];
  disclaimer: string;
};

export type ResearchRank = {
  host_id: string;
  split_role: string;
  model_version: string;
  feature_source: string;
  candidates: {
    phage_id: string;
    compatibility: number;
    decision: string;
    safety_status: string;
  }[];
  cocktail_status: string;
  cocktail_blockers: string[];
  disclaimer: string;
};

export type ProcessingCapabilities = {
  novel_isolate_pipeline_ready: boolean;
  tools: Record<string, boolean>;
  blockers: string[];
  esm2_model: string;
  embedding_dimensions: number;
};

export type AssemblyInspection = {
  assembly_sha256: string;
  contig_count: number;
  total_length_bp: number;
  n50_bp: number;
  gc_fraction: number;
  ambiguous_fraction: number;
  qc_status: string;
  warnings: string[];
  pipeline_status: string;
  completed_stages: string[];
  blockers: string[];
  sequence_persisted: boolean;
};

export type IsolateLocusExtraction = {
  assembly_sha256: string;
  locus: string;
  confidence: string;
  percent_identity: number;
  percent_coverage: number;
  protein_count: number;
  total_residues: number;
  protein_names: string[];
  protein_set_sha256: string;
  missing_genes: string[];
  problems: string;
  kaptive_version: string;
  species_status: string;
  pipeline_status: string;
  raw_sequences_returned: boolean;
  sequence_persisted: boolean;
  disclaimer: string;
};
