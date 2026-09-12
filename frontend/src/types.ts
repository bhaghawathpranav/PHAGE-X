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
