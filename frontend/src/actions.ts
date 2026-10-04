export type Counts = { projects: number; components: number; edges: number; assessments: number };
export type Project = {
  id: number;
  creator: string;
  title: string;
  status: string;
  revision: number;
  component_ids: number[];
  edge_ids: number[];
  last_assessment_id: number;
};
export type Component = {
  id: number;
  project_id: number;
  ecosystem: string;
  name: string;
  version: string;
  status: string;
  revision: number;
  version_revision: number;
  verified_version_revision: number;
  identity_status: string;
  last_assessment_id: number;
  last_advisory_id: string;
  reason: string;
  history: Array<{ version: string; revision: number; status: string; advisory_id: string; assessment_id: number }>;
};
export type Edge = { id: number; dependent_id: number; dependency_id: number; status: string };

export function statusLabel(status: string) {
  return status.replaceAll('_', ' ').toLowerCase().replace(/\b\w/g, (m) => m.toUpperCase());
}

export function statusTone(status: string) {
  if (status === 'VULNERABLE') return 'danger';
  if (status === 'ACTIVE' || status === 'VERIFIED' || status === 'SEALED') return 'success';
  if (status === 'UNRESOLVED' || status === 'RECHECK_REQUIRED' || status === 'PATCH_PENDING') return 'warning';
  return 'neutral';
}

export function parsePositiveInt(value: string, label: string) {
  const n = Number(value);
  if (!Number.isInteger(n) || n < 1) throw new Error(`${label} must be a positive integer.`);
  return n;
}
