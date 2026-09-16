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
    rationale: string[];
    attributions: {
      feature: string;
      contribution: number;
      direction: string;
    }[];
  }[];
  cocktail_status: string;
  cocktail_blockers: string[];
  disclaimer: string;
};

export type ResearchModelStatus = {
  artifact_version: string;
  model: string;
  release_approved: boolean;
  release_reason: string;
  test_metrics: {
    decision_threshold: number;
    accuracy: number;
    balanced_accuracy: number;
    precision: number;
    recall: number;
    specificity: number;
    f1: number;
    matthews_correlation: number;
    roc_auc: number;
    average_precision: number;
    brier_score: number;
    top_3_host_recall: number;
    top_5_host_recall: number;
  };
  benchmark_hosts: number;
  candidate_phages: number;
  decision_threshold: number;
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
  species_reference_accession: string;
  species_ani_percent: number;
  species_alignment_fraction: number;
  species_reference_sha256: string;
  fastani_version: string;
  pipeline_status: string;
  raw_sequences_returned: boolean;
  sequence_persisted: boolean;
  disclaimer: string;
};

export type IsolateEmbedding = {
  assembly_sha256: string;
  locus: string;
  species_status: string;
  species_ani_percent: number;
  species_alignment_fraction: number;
  protein_count: number;
  protein_set_sha256: string;
  model: string;
  dimensions: number;
  embedding_cache_key: string;
  embedding_sha256: string;
  pipeline_status: string;
  raw_embedding_returned: boolean;
  sequence_persisted: boolean;
  disclaimer: string;
};

export type NovelIsolateRank = {
  assembly_sha256: string;
  locus: string;
  species_status: string;
  species_ani_percent: number;
  model_version: string;
  feature_source: string;
  feature_sha256: string;
  distribution_status: string;
  nearest_reference_cosine: number;
  candidates: ResearchRank["candidates"];
  cocktail_status: string;
  cocktail_members: string[];
  cocktail_objective_score: number | null;
  cocktail_mean_compatibility: number | null;
  cocktail_family_diversity: number | null;
  cocktail_receptor_diversity: number | null;
  cocktail_redundancy: number | null;
  cocktail_blockers: string[];
  disclaimer: string;
};
