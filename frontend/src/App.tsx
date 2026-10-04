import { useCallback, useMemo, useState } from 'react';
import {
  Activity,
  ArrowDown,
  Boxes,
  Bug,
  CheckCircle2,
  ExternalLink,
  GitBranch,
  LoaderCircle,
  PackageCheck,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  Wrench,
} from 'lucide-react';
import { Component, Counts, Edge, parsePositiveInt, Project, statusLabel, statusTone } from './actions';
import { CHAIN_ID, CONTRACT, configured, connectWallet, explorerAddress, readFinalized, short, txUrl, writeFinalized } from './genlayer';

const emptyCounts: Counts = { projects: 0, components: 0, edges: 0, assessments: 0 };

function Pill({ status }: { status: string }) {
  return <span className={`pill ${statusTone(status)}`}>{statusLabel(status)}</span>;
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <label className="field"><span>{label}</span>{children}</label>;
}

function ActionCard({ icon, title, text, children }: { icon: React.ReactNode; title: string; text: string; children: React.ReactNode }) {
  return (
    <section className="action-card glass">
      <div className="action-head"><span className="icon-box">{icon}</span><div><h3>{title}</h3><p>{text}</p></div></div>
      {children}
    </section>
  );
}

export default function App() {
  const [account, setAccount] = useState('');
  const [busy, setBusy] = useState('');
  const [notice, setNotice] = useState('');
  const [lastTx, setLastTx] = useState('');
  const [counts, setCounts] = useState<Counts>(emptyCounts);
  const [projectId, setProjectId] = useState('1');
  const [project, setProject] = useState<Project | null>(null);
  const [components, setComponents] = useState<Component[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);

  const [projectTitle, setProjectTitle] = useState('Production dependency graph');
  const [componentForm, setComponentForm] = useState({ ecosystem: 'pypi', name: 'jinja2', version: '3.1.4' });
  const [dependencyForm, setDependencyForm] = useState({ dependent: '2', dependency: '1' });
  const [verifyId, setVerifyId] = useState('1');
  const [advisoryId, setAdvisoryId] = useState('');
  const [patchForm, setPatchForm] = useState({ component: '1', version: '' });
  const [recheckId, setRecheckId] = useState('2');

  const selectedProjectId = useMemo(() => {
    const n = Number(projectId);
    return Number.isInteger(n) && n > 0 ? n : 0;
  }, [projectId]);

  const loadProject = useCallback(async (target = selectedProjectId) => {
    if (!configured || !target) return;
    setBusy('refresh');
    setNotice('');
    try {
      const [nextCounts, nextProject] = await Promise.all([
        readFinalized<Counts>('get_counts'),
        readFinalized<Project>('get_project', [target]),
      ]);
      setCounts(nextCounts);
      if (!nextProject?.id) {
        setProject(null); setComponents([]); setEdges([]); setNotice(`Project ${target} was not found.`); return;
      }
      const nextComponents = await Promise.all((nextProject.component_ids || []).map((id) => readFinalized<Component>('get_component', [id])));
      const nextEdges = await Promise.all((nextProject.edge_ids || []).map((id) => readFinalized<Edge>('get_edge', [id])));
      setProject(nextProject);
      setComponents(nextComponents);
      setEdges(nextEdges);
      setNotice(`Loaded finalized state for project ${target}.`);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : String(error));
    } finally { setBusy(''); }
  }, [selectedProjectId]);

  async function transact(key: string, method: string, args: unknown[], after?: () => void) {
    setBusy(key); setNotice(''); setLastTx('');
    try {
      if (!account) throw new Error('Connect your wallet first.');
      const hash = await writeFinalized(account, method, args);
      setLastTx(hash);
      setNotice(`${method} finalized. Verifying contract state…`);
      after?.();
      await loadProject(selectedProjectId || 1);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : String(error));
    } finally { setBusy(''); }
  }

  async function onConnect() {
    setBusy('connect'); setNotice('');
    try { const address = await connectWallet(); setAccount(address); setNotice('Wallet connected to Studionet.'); }
    catch (error) { setNotice(error instanceof Error ? error.message : String(error)); }
    finally { setBusy(''); }
  }

  const rootNames = new Map(components.map((c) => [c.id, `${c.name}@${c.version}`]));

  return (
    <div className="app-shell">
      <div className="aurora a1" /><div className="aurora a2" /><div className="grid-overlay" />
      <header className="topbar glass">
        <div className="brand">
          <div className="logo-mark"><Sparkles size={22} /><span>S</span></div>
          <div><strong>Spatch</strong><small>Security patch intelligence on GenLayer</small></div>
        </div>
        <div className="header-actions">
          <span className="network"><span className="dot" /> Studionet · {CHAIN_ID}</span>
          <button className="secondary" onClick={onConnect} disabled={!!busy}>{busy === 'connect' ? <LoaderCircle className="spin" size={16} /> : null}{account ? short(account) : 'Connect wallet'}</button>
        </div>
      </header>

      <main>
        <section className="hero">
          <div className="hero-copy">
            <span className="eyebrow">VERSION-AWARE · EVIDENCE-BOUND · REVISION-SCOPED</span>
            <h1>Patch the package.<br /><span>Preserve the proof.</span></h1>
            <p>Spatch tracks exact software versions, verifies their identities, evaluates GHSA advisories against live evidence, and deterministically pushes recheck state through dependency chains without erasing vulnerable history.</p>
            <div className="hero-buttons">
              <button className="primary" onClick={() => loadProject()} disabled={!configured || !!busy}><RefreshCw size={17} className={busy === 'refresh' ? 'spin' : ''} /> Load project</button>
              {configured && <a className="ghost-link" href={explorerAddress} target="_blank" rel="noreferrer">Contract <ExternalLink size={15} /></a>}
            </div>
          </div>
          <div className="hero-visual glass">
            <div className="flow-node safe"><PackageCheck size={20} /><span>Exact version</span><b>verified</b></div>
            <ArrowDown size={20} />
            <div className="flow-node watch"><ShieldCheck size={20} /><span>GHSA evidence</span><b>cross-checked</b></div>
            <ArrowDown size={20} />
            <div className="flow-row">
              <div className="flow-node danger-mini"><Bug size={18} /><b>affected</b></div>
              <GitBranch size={25} />
              <div className="flow-node info-mini"><Activity size={18} /><b>cascade</b></div>
            </div>
            <div className="visual-note">Old versions stay in history. New versions must earn fresh identity proof.</div>
          </div>
        </section>

        {!configured && (
          <div className="banner warning-banner">
            <strong>Pre-deployment build.</strong> Set <code>VITE_CONTRACT_ADDRESS</code> after Codex deploys Spatch to stable Studionet.
          </div>
        )}
        {notice && <div className="banner"><span>{notice}</span>{lastTx && <a href={txUrl(lastTx)} target="_blank" rel="noreferrer">View transaction <ExternalLink size={14} /></a>}</div>}

        <section className="stats">
          <div className="stat glass"><span>Projects</span><strong>{counts.projects}</strong></div>
          <div className="stat glass"><span>Components</span><strong>{counts.components}</strong></div>
          <div className="stat glass"><span>Edges</span><strong>{counts.edges}</strong></div>
          <div className="stat glass"><span>Assessments</span><strong>{counts.assessments}</strong></div>
        </section>

        <section className="workspace-grid">
          <div className="workspace-main">
            <div className="section-title"><div><span className="eyebrow">FINALIZED STATE</span><h2>Dependency workspace</h2></div><div className="load-row"><input value={projectId} onChange={(e) => setProjectId(e.target.value)} inputMode="numeric" aria-label="Project ID" /><button className="mini" onClick={() => loadProject()} disabled={!configured || !!busy}>Load</button></div></div>
            <section className="project-card glass">
              <div className="project-top"><div><span className="muted">Project {project?.id || '—'}</span><h3>{project?.title || 'No project loaded yet'}</h3></div>{project?.status ? <Pill status={project.status} /> : <Pill status="DRAFT" />}</div>
              <div className="project-meta"><span>Revision <b>{project?.revision || '—'}</b></span><span>Latest assessment <b>{project?.last_assessment_id || '—'}</b></span><span>Creator <b>{project?.creator ? short(project.creator) : '—'}</b></span></div>
            </section>

            <div className="component-list">
              {components.length === 0 ? <div className="empty glass"><Boxes size={28} /><b>No finalized components loaded</b><span>Create a project and add exact package versions.</span></div> : components.map((component) => (
                <article className="component-card glass" key={component.id}>
                  <div className="component-icon"><Boxes size={21} /></div>
                  <div className="component-body">
                    <div className="component-title"><div><small>#{component.id} · {component.ecosystem}</small><h3>{component.name}<span>@{component.version}</span></h3></div><Pill status={component.status} /></div>
                    <p>{statusLabel(component.reason || 'No reason')}</p>
                    <div className="component-meta"><span>state rev {component.revision}</span><span>version rev {component.version_revision}</span><span>verified version rev {component.verified_version_revision || '—'}</span><span>{component.last_advisory_id || 'no advisory'}</span></div>
                    {component.history?.length > 0 && <div className="history"><b>Retired versions</b>{component.history.map((h, i) => <span key={`${h.version}-${i}`}>{h.version} · {statusLabel(h.status)} {h.advisory_id ? `· ${h.advisory_id}` : ''}</span>)}</div>}
                  </div>
                </article>
              ))}
            </div>

            {edges.length > 0 && <section className="edge-panel glass"><div className="edge-title"><GitBranch size={18} /><b>Dependency edges</b></div>{edges.map((edge) => <div className="edge-row" key={edge.id}><span>#{edge.dependent_id} {rootNames.get(edge.dependent_id)}</span><b>depends on</b><span>#{edge.dependency_id} {rootNames.get(edge.dependency_id)}</span></div>)}</section>}
          </div>

          <aside className="actions-column">
            <ActionCard icon={<Sparkles size={19} />} title="1 · Create project" text="Start an owner-controlled dependency workspace.">
              <Field label="Project title"><input value={projectTitle} onChange={(e) => setProjectTitle(e.target.value)} /></Field>
              <button className="primary full" disabled={!!busy || !configured} onClick={() => transact('create', 'create_project', [projectTitle], () => setProjectId(String(counts.projects + 1)))}>{busy === 'create' ? <LoaderCircle className="spin" size={16} /> : null}Create project</button>
            </ActionCard>

            <ActionCard icon={<Boxes size={19} />} title="2 · Add exact component" text="Pin ecosystem, package name and installed version.">
              <div className="two-col"><Field label="Ecosystem"><select value={componentForm.ecosystem} onChange={(e) => setComponentForm({ ...componentForm, ecosystem: e.target.value })}><option value="pypi">PyPI</option><option value="npm">npm</option><option value="cargo">Cargo</option><option value="maven">Maven</option><option value="go">Go</option><option value="nuget">NuGet</option><option value="rubygems">RubyGems</option></select></Field><Field label="Project ID"><input value={projectId} onChange={(e) => setProjectId(e.target.value)} /></Field></div>
              <Field label="Package name"><input value={componentForm.name} onChange={(e) => setComponentForm({ ...componentForm, name: e.target.value })} /></Field>
              <Field label="Exact version"><input value={componentForm.version} onChange={(e) => setComponentForm({ ...componentForm, version: e.target.value })} /></Field>
              <button className="primary full" disabled={!!busy || !configured} onClick={() => { try { transact('component', 'add_component', [parsePositiveInt(projectId, 'Project ID'), componentForm.ecosystem, componentForm.name, componentForm.version]); } catch (e) { setNotice(e instanceof Error ? e.message : String(e)); } }}>Add component</button>
            </ActionCard>

            <ActionCard icon={<GitBranch size={19} />} title="3 · Link dependency" text="The dependency must have an older component ID, keeping the graph acyclic.">
              <div className="two-col"><Field label="Dependent"><input value={dependencyForm.dependent} onChange={(e) => setDependencyForm({ ...dependencyForm, dependent: e.target.value })} /></Field><Field label="Depends on"><input value={dependencyForm.dependency} onChange={(e) => setDependencyForm({ ...dependencyForm, dependency: e.target.value })} /></Field></div>
              <button className="secondary full" disabled={!!busy || !configured} onClick={() => { try { transact('edge', 'add_dependency', [parsePositiveInt(dependencyForm.dependent, 'Dependent ID'), parsePositiveInt(dependencyForm.dependency, 'Dependency ID')]); } catch (e) { setNotice(e instanceof Error ? e.message : String(e)); } }}>Add dependency edge</button>
            </ActionCard>

            <ActionCard icon={<PackageCheck size={19} />} title="4 · Verify component" text="Permissionless deps.dev identity verification before sealing.">
              <Field label="Component ID"><input value={verifyId} onChange={(e) => setVerifyId(e.target.value)} /></Field>
              <button className="secondary full" disabled={!!busy || !configured} onClick={() => { try { const id = parsePositiveInt(verifyId, 'Component ID'); const component = components.find((c) => c.id === id); if (!component) throw new Error('Load the project so Spatch can bind the current component revision.'); transact('verify', 'verify_component', [id, component.revision]); } catch (e) { setNotice(e instanceof Error ? e.message : String(e)); } }}>Verify exact version</button>
              <button className="ghost full" disabled={!!busy || !configured} onClick={() => { try { transact('seal', 'seal_project', [parsePositiveInt(projectId, 'Project ID')]); } catch (e) { setNotice(e instanceof Error ? e.message : String(e)); } }}><CheckCircle2 size={16} /> Seal verified graph</button>
            </ActionCard>

            <ActionCard icon={<ShieldCheck size={19} />} title="5 · Assess GHSA" text="OSV + GitHub evidence, custom validator consensus, deterministic blast radius.">
              <Field label="GHSA advisory ID"><input placeholder="GHSA-xxxx-xxxx-xxxx" value={advisoryId} onChange={(e) => setAdvisoryId(e.target.value.toUpperCase())} /></Field>
              <button className="danger-button full" disabled={!!busy || !configured} onClick={() => { try { transact('advisory', 'assess_advisory', [parsePositiveInt(projectId, 'Project ID'), advisoryId]); } catch (e) { setNotice(e instanceof Error ? e.message : String(e)); } }}><Bug size={16} /> Run advisory consensus</button>
            </ActionCard>

            <ActionCard icon={<Wrench size={19} />} title="6 · Stage patch" text="Retire the vulnerable version into immutable history, then verify the replacement.">
              <div className="two-col"><Field label="Component"><input value={patchForm.component} onChange={(e) => setPatchForm({ ...patchForm, component: e.target.value })} /></Field><Field label="New version"><input value={patchForm.version} onChange={(e) => setPatchForm({ ...patchForm, version: e.target.value })} /></Field></div>
              <button className="primary full" disabled={!!busy || !configured} onClick={() => { try { const id = parsePositiveInt(patchForm.component, 'Component ID'); const component = components.find((c) => c.id === id); if (!component) throw new Error('Load the project so Spatch can bind the current component revision.'); transact('patch', 'patch_component', [id, patchForm.version, component.revision]); } catch (e) { setNotice(e instanceof Error ? e.message : String(e)); } }}>Stage replacement version</button>
              <button className="secondary full" disabled={!!busy || !configured} onClick={() => { try { const id = parsePositiveInt(patchForm.component, 'Component ID'); const component = components.find((c) => c.id === id); if (!component) throw new Error('Reload the project after staging the patch.'); transact('verify-patch', 'verify_patch', [id, component.revision]); } catch (e) { setNotice(e instanceof Error ? e.message : String(e)); } }}>Verify patch identity</button>
              <Field label="Downstream recheck component"><input value={recheckId} onChange={(e) => setRecheckId(e.target.value)} /></Field>
              <button className="ghost full" disabled={!!busy || !configured} onClick={() => { try { const id = parsePositiveInt(recheckId, 'Recheck component ID'); const component = components.find((c) => c.id === id); if (!component) throw new Error('Load the project so Spatch can bind the current recheck revision.'); transact('dependency-recheck', 'reassess_dependency', [id, component.revision]); } catch (e) { setNotice(e instanceof Error ? e.message : String(e)); } }}><RefreshCw size={16} /> Clear downstream recheck</button>
            </ActionCard>
          </aside>
        </section>
      </main>

      <footer><span>Spatch · GenLayer Studionet</span><span>Contract {configured ? short(CONTRACT) : 'pending deployment'}</span></footer>
    </div>
  );
}
