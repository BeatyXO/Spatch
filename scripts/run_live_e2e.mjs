#!/usr/bin/env node
/**
 * Spatch live Studionet lifecycle runner.
 *
 * Uses the pinned genlayer-js 1.1.8 API from frontend dependencies. Never treat
 * output as evidence unless every finalized readback assertion passes on the
 * final deployed contract.
 */
import { createAccount, createClient } from '../frontend/node_modules/genlayer-js/dist/index.js';
import { studionet } from '../frontend/node_modules/genlayer-js/dist/chains/index.js';
import {
  ExecutionResult,
  TransactionHashVariant,
  TransactionStatus,
} from '../frontend/node_modules/genlayer-js/dist/types/index.js';

const [,, contractAddress] = process.argv;
if (!/^0x[0-9a-fA-F]{40}$/.test(contractAddress || '')) {
  throw new Error('Usage: node scripts/run_live_e2e.mjs <contract-address>');
}

const required = [
  'SPATCH_AUTHOR_KEY', 'SPATCH_OBSERVER_KEY', 'SPATCH_GHSA',
  'SPATCH_DEP_ECOSYSTEM', 'SPATCH_DEP_NAME', 'SPATCH_VULN_VERSION', 'SPATCH_FIXED_VERSION',
  'SPATCH_APP_ECOSYSTEM', 'SPATCH_APP_NAME', 'SPATCH_APP_VERSION',
];
for (const key of required) if (!process.env[key]) throw new Error(`Missing ${key}`);

const author = createAccount(process.env.SPATCH_AUTHOR_KEY.startsWith('0x') ? process.env.SPATCH_AUTHOR_KEY : `0x${process.env.SPATCH_AUTHOR_KEY}`);
const observer = createAccount(process.env.SPATCH_OBSERVER_KEY.startsWith('0x') ? process.env.SPATCH_OBSERVER_KEY : `0x${process.env.SPATCH_OBSERVER_KEY}`);
if (author.address.toLowerCase() === observer.address.toLowerCase()) throw new Error('Use two distinct wallets.');

const authorClient = createClient({ chain: studionet, account: author });
const observerClient = createClient({ chain: studionet, account: observer });
const reader = createClient({ chain: studionet });

const read = (name, args = []) => reader.readContract({
  address: contractAddress,
  functionName: name,
  args,
  transactionHashVariant: TransactionHashVariant.LATEST_FINAL,
  jsonSafeReturn: true,
});

async function write(client, account, label, name, args) {
  const hash = await client.writeContract({ address: contractAddress, functionName: name, args, value: 0n });
  console.log(`${label}.submitted=${hash}`);
  const receipt = await client.waitForTransactionReceipt({
    hash,
    status: TransactionStatus.FINALIZED,
    interval: 3000,
    retries: 240,
  });
  if (receipt.txExecutionResultName !== ExecutionResult.FINISHED_WITH_RETURN) {
    throw new Error(`${label} finalized with ${receipt.txExecutionResultName || 'no execution result'}`);
  }
  console.log(`${label}.finalized=${hash}`);
  return hash;
}

function assert(ok, label, data) {
  if (!ok) throw new Error(`${label}: ${JSON.stringify(data)}`);
  console.log(`${label}.readback=${JSON.stringify(data)}`);
}

const protocol = await read('get_protocol');
assert(Number(protocol.chain_id) === 61999 && protocol.name === 'Spatch', 'protocol', protocol);
const initial = await read('get_counts');
assert(Number(initial.projects) === 0 && Number(initial.components) === 0, 'fresh deployment', initial);

await write(authorClient, author, 'create_project', 'create_project', ['Spatch live evidence fixture']);
let counts = await read('get_counts');
const projectId = Number(counts.projects);
const dependencyId = Number(counts.components) + 1;

// An observer cannot mutate the creator's draft graph.
const beforeUnauthorizedEdit = await read('get_counts');
await write(observerClient, observer, 'unauthorized_add_component', 'add_component', [
  projectId,
  process.env.SPATCH_DEP_ECOSYSTEM,
  'spatch-unauthorized-probe',
  '0.0.1',
]);
counts = await read('get_counts');
assert(Number(counts.components) === Number(beforeUnauthorizedEdit.components), 'creator-only mutation', counts);

await write(authorClient, author, 'add_dependency_component', 'add_component', [projectId, process.env.SPATCH_DEP_ECOSYSTEM, process.env.SPATCH_DEP_NAME, process.env.SPATCH_VULN_VERSION]);
const appId = dependencyId + 1;
await write(authorClient, author, 'add_app_component', 'add_component', [projectId, process.env.SPATCH_APP_ECOSYSTEM, process.env.SPATCH_APP_NAME, process.env.SPATCH_APP_VERSION]);
await write(authorClient, author, 'add_dependency_edge', 'add_dependency', [appId, dependencyId]);

let dep = await read('get_component', [dependencyId]);
let app = await read('get_component', [appId]);
await write(observerClient, observer, 'verify_dependency', 'verify_component', [dependencyId, Number(dep.revision)]);
await write(observerClient, observer, 'verify_app', 'verify_component', [appId, Number(app.revision)]);
dep = await read('get_component', [dependencyId]);
app = await read('get_component', [appId]);
assert(dep.status === 'ACTIVE' && app.status === 'ACTIVE', 'identity verification', { dep, app });

// A stale identity revision must be rejected without changing the component.
const beforeStaleAttempt = dep;
await write(observerClient, observer, 'stale_identity_revision', 'verify_component', [
  dependencyId,
  Math.max(0, Number(dep.revision) - 1),
]);
dep = await read('get_component', [dependencyId]);
assert(
  Number(dep.revision) === Number(beforeStaleAttempt.revision) && dep.status === beforeStaleAttempt.status,
  'stale revision leaves component unchanged',
  dep,
);

await write(authorClient, author, 'seal_project', 'seal_project', [projectId]);
let project = await read('get_project', [projectId]);
assert(project.status === 'SEALED', 'sealed graph', project);

await write(observerClient, observer, 'assess_vulnerable_version', 'assess_advisory', [projectId, process.env.SPATCH_GHSA]);
dep = await read('get_component', [dependencyId]);
app = await read('get_component', [appId]);
assert(dep.status === 'VULNERABLE' && app.status === 'RECHECK_REQUIRED', 'vulnerability blast radius', { dep, app });
const vulnerableAssessment = await read('get_assessment', [Number(dep.last_assessment_id)]);
const vulnerableResult = vulnerableAssessment.results?.find(
  (result) => Number(result.component_id) === dependencyId,
);
assert(
  vulnerableAssessment.advisory_id === process.env.SPATCH_GHSA && vulnerableResult &&
    Number(vulnerableResult.version_revision) === Number(dep.version_revision),
  'assessment bound to vulnerable version revision',
  vulnerableAssessment,
);

// Same version revision must be replay-blocked without creating another assessment.
counts = await read('get_counts');
const stateBeforeReplay = { status: dep.status, revision: Number(dep.revision), lastAssessment: Number(dep.last_assessment_id) };
await write(observerClient, observer, 'replay_same_version', 'assess_advisory', [projectId, process.env.SPATCH_GHSA]);
const afterReplay = await read('get_counts');
assert(Number(afterReplay.assessments) === Number(counts.assessments), 'same-version replay blocked', afterReplay);
dep = await read('get_component', [dependencyId]);
assert(
  dep.status === stateBeforeReplay.status && Number(dep.revision) === stateBeforeReplay.revision &&
    Number(dep.last_assessment_id) === stateBeforeReplay.lastAssessment,
  'replay leaves vulnerable state unchanged',
  dep,
);

await write(authorClient, author, 'stage_patch', 'patch_component', [dependencyId, process.env.SPATCH_FIXED_VERSION, Number(dep.revision)]);
dep = await read('get_component', [dependencyId]);
assert(
  dep.status === 'PATCH_PENDING' && dep.history?.length >= 1 &&
    dep.history.at(-1)?.version === process.env.SPATCH_VULN_VERSION &&
    dep.history.at(-1)?.status === 'VULNERABLE' && !dep.identity_evidence_digest,
  'patch preserves history and clears identity evidence',
  dep,
);
await write(observerClient, observer, 'verify_patch_identity', 'verify_patch', [dependencyId, Number(dep.revision)]);
dep = await read('get_component', [dependencyId]);
assert(dep.status === 'ACTIVE', 'patch identity current', dep);

await write(observerClient, observer, 'reassess_same_ghsa_new_version', 'assess_advisory', [projectId, process.env.SPATCH_GHSA]);
dep = await read('get_component', [dependencyId]);
assert(dep.status === 'ACTIVE', 'patched version outside advisory', dep);
const patchedAssessment = await read('get_assessment', [Number(dep.last_assessment_id)]);
const patchedResult = patchedAssessment.results?.find(
  (result) => Number(result.component_id) === dependencyId,
);
assert(
  patchedAssessment.advisory_id === process.env.SPATCH_GHSA && patchedResult &&
    Number(patchedResult.version_revision) === Number(dep.version_revision) &&
    Number(dep.version_revision) === Number(vulnerableResult.version_revision) + 1,
  'same GHSA reassessed only for new version revision',
  patchedAssessment,
);

app = await read('get_component', [appId]);
await write(observerClient, observer, 'clear_downstream_recheck', 'reassess_dependency', [appId, Number(app.revision)]);
app = await read('get_component', [appId]);
assert(app.status === 'ACTIVE', 'downstream recovery', app);

project = await read('get_project', [projectId]);
counts = await read('get_counts');
assert(Number(counts.projects) === 1 && Number(counts.components) === 2 && Number(counts.edges) === 1, 'final graph counts', counts);
console.log(`e2e.final.project=${JSON.stringify(project)}`);
console.log(`e2e.final.dependency=${JSON.stringify(dep)}`);
console.log(`e2e.final.app=${JSON.stringify(app)}`);
console.log(`e2e.final.counts=${JSON.stringify(counts)}`);
console.log('e2e.result=PASS');
