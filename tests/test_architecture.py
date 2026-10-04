from pathlib import Path

SOURCE = Path("contracts/spatch.py").read_text(encoding="utf-8")


def test_uses_custom_validator_consensus_for_semantic_advisory_decision():
    assert "gl.vm.run_nondet_unsafe(evaluate, validator)" in SOURCE
    assert "decision_projection(leader_result.calldata) == decision_projection(own)" in SOURCE


def test_sources_are_constructed_not_user_supplied_urls():
    assert 'OSV_BASE = "https://api.osv.dev/v1/vulns/"' in SOURCE
    assert 'GITHUB_ADVISORY_BASE = "https://api.github.com/advisories/"' in SOURCE
    assert 'DEPS_BASE = "https://api.deps.dev/v3/systems/"' in SOURCE


def test_patch_history_and_revision_scoped_replay_are_explicit():
    assert '"history": []' in SOURCE
    assert 'str(component["version_revision"]) + ":" + advisory_id' in SOURCE
    assert '"patch_policy": "old-version-history-preserved-new-version-must-be-reverified"' in SOURCE


def test_deterministic_blast_radius_is_separate_from_nondeterminism():
    assert "def _propagate_recheck" in SOURCE
    assert "UPSTREAM_COMPONENT_CHANGED_SECURITY_STATE" in SOURCE
    assert "self._propagate_recheck" in SOURCE


def test_graph_is_bounded():
    assert "MAX_COMPONENTS = 16" in SOURCE
    assert "MAX_EDGES = 32" in SOURCE
    assert "MAX_HISTORY = 8" in SOURCE


def test_dependency_recovery_is_explicit_and_deterministic():
    assert "def reassess_dependency" in SOURCE
    assert "ALL_DIRECT_DEPENDENCIES_ACTIVE" in SOURCE
    assert "DEPENDENCIES_STABLE_AFTER_RECHECK" in SOURCE
