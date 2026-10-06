"""Official genlayer-test Direct Mode coverage for the deployed contract runtime."""

import json

import pytest

GHSA = "GHSA-GMJ6-6F8F-6699"
OSV_GHSA = "GHSA-" + GHSA[5:].lower()
GHSA_B = "GHSA-3P2H-W9Q8-4V6R"


def web_json(vm, pattern, value, status=200):
    vm.mock_web(pattern, {"method": "GET", "status": status, "body": json.dumps(value)})


def identity(vm, name, version):
    web_json(vm, rf"api\.deps\.dev/.*/{name}/versions/{version}", {
        "versionKey": {"system": "PYPI", "name": name, "version": version}
    })


def advisory_sources(vm, advisory_id=GHSA):
    osv_id = "GHSA-" + advisory_id[5:].lower()
    web_json(vm, rf"api\.osv\.dev/v1/vulns/{osv_id}", {
        "id": advisory_id,
        "affected": [{
            "package": {"ecosystem": "PyPI", "name": "jinja2"},
            "ranges": [{"type": "ECOSYSTEM", "events": [{"introduced": "3.0.0"}, {"fixed": "3.1.5"}]}],
        }],
    })
    web_json(vm, rf"api\.github\.com/advisories/{advisory_id}", {
        "ghsa_id": advisory_id,
        "summary": "Jinja sandbox breakout through malicious filenames",
        "description": "Jinja2 releases through 3.1.4 are affected.",
        "vulnerabilities": [{
            "package": {"ecosystem": "pip", "name": "jinja2"},
            "vulnerable_version_range": ">= 3.0.0, <= 3.1.4",
            "first_patched_version": {"identifier": "3.1.5"},
        }],
    })


def judgment(rows):
    return json.dumps({"results": rows})


def row(cid, revision, version_revision, verdict, reason, fixed=""):
    return {
        "component_id": cid,
        "component_revision": revision,
        "version_revision": version_revision,
        "verdict": verdict,
        "reason_code": reason,
        "fixed_version": fixed,
    }


def bounded_ghsa(index):
    alphabet = "23456789CFGHJMPQRVWX"
    digits = ["2"] * 12
    value = index
    for position in range(11, -1, -1):
        digits[position] = alphabet[value % len(alphabet)]
        value //= len(alphabet)
    return "GHSA-" + "".join(digits[:4]) + "-" + "".join(digits[4:8]) + "-" + "".join(digits[8:])


def draft(contract, vm, creator):
    vm.sender = creator
    project_id = int(contract.create_project("Direct Mode Spatch graph"))
    dep_id = int(contract.add_component(project_id, "pypi", "jinja2", "3.1.4"))
    app_id = int(contract.add_component(project_id, "pypi", "flask", "3.0.0"))
    assert int(contract.add_dependency(app_id, dep_id)) > 0
    return project_id, dep_id, app_id


def verified_sealed(contract, vm, project_id, dep_id, app_id, observer):
    for cid, package, version in ((dep_id, "jinja2", "3.1.4"), (app_id, "flask", "3.0.0")):
        identity(vm, package, version)
        vm.sender = observer
        component = contract.get_component(cid)
        assert int(contract.verify_component(cid, component["revision"])) > 0
        assert contract.get_component(cid)["status"] == "ACTIVE"
    project = contract.get_project(project_id)
    vm.sender = project["creator"]
    assert contract.seal_project(project_id) == "SEALED"


def test_direct_full_lifecycle_replay_patch_and_dependency_recovery(direct_deploy, direct_vm, direct_alice, direct_bob):
    contract = direct_deploy("contracts/spatch.py", sdk_version="v0.2.16")
    project_id, dep_id, app_id = draft(contract, direct_vm, direct_alice)
    assert contract.seal_project(project_id) == "COMPONENT_IDENTITY_NOT_CURRENT"
    verified_sealed(contract, direct_vm, project_id, dep_id, app_id, direct_bob)

    dep = contract.get_component(dep_id)
    app = contract.get_component(app_id)
    rows = [
        row(dep_id, dep["revision"], dep["version_revision"], "AFFECTED", "VERSION_IN_AFFECTED_RANGE", "3.1.5"),
        row(app_id, app["revision"], app["version_revision"], "NOT_AFFECTED", "PACKAGE_NOT_TARGETED"),
    ]
    direct_vm.clear_mocks()
    direct_vm.clear_mocks()
    advisory_sources(direct_vm)
    direct_vm.mock_llm(".*", judgment(rows))
    direct_vm.sender = direct_bob
    assessment_id = int(contract.assess_advisory(project_id, GHSA))
    assessment = contract.get_assessment(assessment_id)
    assert assessment["status"] == "ASSESSED", assessment
    assert direct_vm.run_validator() is True
    conflicting = json.dumps({"kind": "ASSESSED", "advisory_id": GHSA, "results": [
        row(dep_id, dep["revision"], dep["version_revision"], "NOT_AFFECTED", "PACKAGE_NOT_TARGETED"),
        row(app_id, app["revision"], app["version_revision"], "NOT_AFFECTED", "PACKAGE_NOT_TARGETED"),
    ]})
    assert direct_vm.run_validator(leader_result=conflicting) is False
    fixed_conflict = json.dumps({"kind": "ASSESSED", "advisory_id": GHSA, "results": [
        row(dep_id, dep["revision"], dep["version_revision"], "AFFECTED", "VERSION_IN_AFFECTED_RANGE", "9.9.9"),
        rows[1],
    ]})
    assert direct_vm.run_validator(leader_result=fixed_conflict) is False
    assert contract.get_component(dep_id)["status"] == "VULNERABLE"
    dep = contract.get_component(dep_id)
    assert contract.verify_component(dep_id, dep["revision"]) == "COMPONENT_IDENTITY_ALREADY_CURRENT"
    assert contract.get_component(dep_id)["status"] == "VULNERABLE"
    assert contract.get_component(app_id)["status"] == "RECHECK_REQUIRED"
    app = contract.get_component(app_id)
    assert contract.verify_component(app_id, app["revision"]) == "COMPONENT_IDENTITY_ALREADY_CURRENT"
    assert contract.get_component(app_id)["status"] == "RECHECK_REQUIRED"
    assert contract.get_findings(dep_id)["current"][0]["verdict"] == "AFFECTED"
    count = contract.get_counts()["assessments"]
    assert contract.assess_advisory(project_id, GHSA) == "ADVISORY_ALREADY_ASSESSED_FOR_CURRENT_REVISIONS"
    assert contract.get_counts()["assessments"] == count

    app = contract.get_component(app_id)
    assert contract.reassess_dependency(app_id, app["revision"]) == "UPSTREAM_STILL_VULNERABLE"
    dep = contract.get_component(dep_id)
    direct_vm.sender = direct_alice
    assert contract.patch_component(dep_id, "3.1.5", dep["revision"]) == "PATCH_VERSION_STAGED"
    staged = contract.get_component(dep_id)
    assert staged["history"][-1]["version"] == "3.1.4"
    assert staged["history"][-1]["status"] == "VULNERABLE"
    assert staged["identity_evidence_digest"] == ""
    assert staged["status"] == "PATCH_PENDING"
    app = contract.get_component(app_id)
    app_revision = app["revision"]
    assert contract.reassess_dependency(app_id, app_revision) == "UPSTREAM_NOT_STABLE"
    assert contract.get_component(app_id)["revision"] == app_revision

    identity(direct_vm, "jinja2", "3.1.5")
    direct_vm.sender = direct_bob
    assert int(contract.verify_patch(dep_id, staged["revision"])) > 0
    patched = contract.get_component(dep_id)
    assert patched["version_revision"] == 2
    assert patched["status"] == "SECURITY_REASSESS_REQUIRED"
    assert patched["security_status"] == "SECURITY_REASSESS_REQUIRED"
    assert contract.get_findings(dep_id)["pending_advisories"] == [GHSA]
    assert contract.reassess_dependency(app_id, app_revision) == "UPSTREAM_NOT_STABLE"
    assert contract.get_component(app_id)["revision"] == app_revision

    direct_vm.clear_mocks()
    advisory_sources(direct_vm)
    direct_vm.mock_llm(".*", judgment([
        row(dep_id, patched["revision"], patched["version_revision"], "NOT_AFFECTED", "VERSION_OUTSIDE_AFFECTED_RANGE", "3.1.5"),
    ]))
    next_assessment = int(contract.assess_advisory(project_id, GHSA))
    assert next_assessment > assessment_id
    next_record = contract.get_assessment(next_assessment)
    assert contract.get_component(dep_id)["status"] == "ACTIVE", {
        "assessment": {key: next_record.get(key) for key in ("status", "reason", "diagnostic", "results")},
        "findings": contract.get_findings(dep_id),
        "component": contract.get_component(dep_id),
    }
    assert contract.get_findings(dep_id)["pending_advisories"] == []
    app = contract.get_component(app_id)
    assert int(contract.reassess_dependency(app_id, app["revision"])) > next_assessment
    assert contract.get_component(app_id)["status"] == "ACTIVE"


def test_direct_creator_only_order_bounds_and_validation(direct_deploy, direct_vm, direct_alice, direct_bob):
    contract = direct_deploy("contracts/spatch.py", sdk_version="v0.2.16")
    direct_vm.sender = direct_alice
    project_id = int(contract.create_project("Bounded graph validation"))
    direct_vm.sender = direct_bob
    assert contract.add_component(project_id, "pypi", "jinja2", "3.1.4") == "ONLY_PROJECT_CREATOR"
    direct_vm.sender = direct_alice
    assert contract.add_component(project_id, "unknown", "bad", "1") == "UNSUPPORTED_ECOSYSTEM"
    assert contract.add_component(project_id, "pypi", "", "1") == "INVALID_COMPONENT"
    dep = int(contract.add_component(project_id, "pypi", "jinja2", "3.1.4"))
    app = int(contract.add_component(project_id, "pypi", "flask", "3.0.0"))
    assert contract.add_dependency(dep, app) == "DEPENDENCY_ORDER_INVALID"
    assert contract.add_dependency(app, dep) > 0
    assert contract.add_dependency(app, dep) == "DEPENDENCY_ALREADY_EXISTS"
    assert contract.assess_advisory(project_id, GHSA) == "PROJECT_NOT_SEALED"
    assert contract.patch_component(dep, "3.1.6", 1) == "PROJECT_NOT_SEALED"


def test_direct_identity_source_failure_and_stale_revision_fail_closed(direct_deploy, direct_vm, direct_alice, direct_bob):
    contract = direct_deploy("contracts/spatch.py", sdk_version="v0.2.16")
    project_id, dep_id, app_id = draft(contract, direct_vm, direct_alice)
    direct_vm.sender = direct_bob
    dep = contract.get_component(dep_id)
    assert contract.verify_component(dep_id, dep["revision"] + 1) == "STALE_COMPONENT_REVISION"
    direct_vm.mock_web(r"api\.deps\.dev", {"method": "GET", "status": 503, "body": "offline"})
    assert int(contract.verify_component(dep_id, dep["revision"])) > 0
    assert contract.get_component(dep_id)["status"] == "UNRESOLVED"
    direct_vm.sender = direct_alice
    assert contract.seal_project(project_id) == "COMPONENT_IDENTITY_NOT_CURRENT"


def test_direct_malformed_model_output_fails_closed(direct_deploy, direct_vm, direct_alice, direct_bob):
    contract = direct_deploy("contracts/spatch.py", sdk_version="v0.2.16")
    project_id, dep_id, app_id = draft(contract, direct_vm, direct_alice)
    verified_sealed(contract, direct_vm, project_id, dep_id, app_id, direct_bob)
    advisory_sources(direct_vm)
    direct_vm.mock_llm(".*", '{"unexpected":true}')
    direct_vm.sender = direct_bob
    assessment_id = int(contract.assess_advisory(project_id, GHSA))
    assessment = contract.get_assessment(assessment_id)
    assert assessment["status"] == "UNRESOLVED"
    assert assessment["reason"] == "MODEL_TOP_LEVEL_SCHEMA_INVALID", assessment
    assert contract.get_component(dep_id)["status"] == "UNRESOLVED"
    assert contract.get_findings(dep_id)["current"][0]["verdict"] == "UNRESOLVED"
    assert contract.verify_component(dep_id, contract.get_component(dep_id)["revision"]) == "COMPONENT_IDENTITY_ALREADY_CURRENT"
    assert contract.get_component(dep_id)["status"] == "UNRESOLVED"


def test_direct_cross_advisory_not_affected_preserves_vulnerability(
    direct_deploy, direct_vm, direct_alice, direct_bob,
):
    contract = direct_deploy("contracts/spatch.py", sdk_version="v0.2.16")
    project_id, dep_id, app_id = draft(contract, direct_vm, direct_alice)
    verified_sealed(contract, direct_vm, project_id, dep_id, app_id, direct_bob)
    dep = contract.get_component(dep_id)
    app = contract.get_component(app_id)
    advisory_sources(direct_vm, GHSA)
    direct_vm.mock_llm(".*", judgment([
        row(dep_id, dep["revision"], dep["version_revision"], "AFFECTED", "VERSION_IN_AFFECTED_RANGE", "3.1.5"),
        row(app_id, app["revision"], app["version_revision"], "NOT_AFFECTED", "PACKAGE_NOT_TARGETED"),
    ]))
    assert int(contract.assess_advisory(project_id, GHSA)) > 0
    assert contract.get_component(dep_id)["status"] == "VULNERABLE"
    direct_vm.clear_mocks()
    advisory_sources(direct_vm, GHSA_B)
    dep = contract.get_component(dep_id)
    app = contract.get_component(app_id)
    direct_vm.mock_llm(".*", judgment([
        row(dep_id, dep["revision"], dep["version_revision"], "NOT_AFFECTED", "VERSION_OUTSIDE_AFFECTED_RANGE", "3.1.5"),
        row(app_id, app["revision"], app["version_revision"], "NOT_AFFECTED", "PACKAGE_NOT_TARGETED"),
    ]))
    assert int(contract.assess_advisory(project_id, GHSA_B)) > 0
    assert contract.get_component(dep_id)["status"] == "VULNERABLE"
    findings = contract.get_findings(dep_id)["current"]
    assert {finding["advisory_id"]: finding["verdict"] for finding in findings} == {
        GHSA: "AFFECTED", GHSA_B: "NOT_AFFECTED",
    }


def test_direct_finding_capacity_and_version_change_keep_relevant_advisory_assessable(
    direct_deploy, direct_vm, direct_alice, direct_bob,
):
    contract = direct_deploy("contracts/spatch.py", sdk_version="v0.2.16")
    project_id, dep_id, app_id = draft(contract, direct_vm, direct_alice)
    verified_sealed(contract, direct_vm, project_id, dep_id, app_id, direct_bob)

    benign_ids = [bounded_ghsa(index) for index in range(1, 33)]
    for advisory_id in benign_ids:
        direct_vm.clear_mocks()
        advisory_sources(direct_vm, advisory_id)
        dep = contract.get_component(dep_id)
        app = contract.get_component(app_id)
        direct_vm.mock_llm(".*", judgment([
            row(dep_id, dep["revision"], dep["version_revision"], "NOT_AFFECTED", "VERSION_OUTSIDE_AFFECTED_RANGE"),
            row(app_id, app["revision"], app["version_revision"], "NOT_AFFECTED", "PACKAGE_NOT_TARGETED"),
        ]))
        direct_vm.sender = direct_bob
        assert int(contract.assess_advisory(project_id, advisory_id)) > 0

    dep = contract.get_component(dep_id)
    assert len(contract.get_findings(dep_id)["current"]) == 32
    assert all(item["verdict"] == "NOT_AFFECTED" for item in contract.get_findings(dep_id)["current"])

    # A public new GHSA is still evaluated and its affected verdict is retained
    # by evicting only a benign entry when the per-version cap is full.
    direct_vm.clear_mocks()
    advisory_sources(direct_vm, GHSA)
    dep = contract.get_component(dep_id)
    app = contract.get_component(app_id)
    direct_vm.mock_llm(".*", judgment([
        row(dep_id, dep["revision"], dep["version_revision"], "AFFECTED", "VERSION_IN_AFFECTED_RANGE", "3.1.5"),
        row(app_id, app["revision"], app["version_revision"], "NOT_AFFECTED", "PACKAGE_NOT_TARGETED"),
    ]))
    direct_vm.sender = direct_bob
    first_assessment = int(contract.assess_advisory(project_id, GHSA))
    assert contract.get_component(dep_id)["status"] == "VULNERABLE"
    assert len(contract.get_findings(dep_id)["current"]) == 32
    assert any(item["advisory_id"] == GHSA and item["verdict"] == "AFFECTED" for item in contract.get_findings(dep_id)["current"])
    assert contract.assess_advisory(project_id, benign_ids[0]) == "ADVISORY_ALREADY_ASSESSED_FOR_CURRENT_REVISIONS"

    dep = contract.get_component(dep_id)
    direct_vm.sender = direct_alice
    assert contract.patch_component(dep_id, "3.1.5", dep["revision"]) == "PATCH_VERSION_STAGED"
    staged = contract.get_component(dep_id)
    assert staged["findings"] == []
    assert any(item["advisory_id"] == GHSA and item["verdict"] == "AFFECTED" for item in staged["history"][-1]["findings"])

    identity(direct_vm, "jinja2", "3.1.5")
    direct_vm.sender = direct_bob
    assert int(contract.verify_patch(dep_id, staged["revision"])) > 0
    patched = contract.get_component(dep_id)
    direct_vm.clear_mocks()
    advisory_sources(direct_vm, GHSA)
    direct_vm.mock_llm(".*", judgment([
        row(dep_id, patched["revision"], patched["version_revision"], "NOT_AFFECTED", "VERSION_OUTSIDE_AFFECTED_RANGE", "3.1.5"),
    ]))
    next_assessment = int(contract.assess_advisory(project_id, GHSA))
    assert next_assessment > first_assessment
    assert contract.get_component(dep_id)["status"] == "ACTIVE"
    findings = contract.get_findings(dep_id)
    assert findings["current"][0]["advisory_id"] == GHSA
    assert findings["current"][0]["verdict"] == "NOT_AFFECTED"
    assert any(item["advisory_id"] == GHSA and item["verdict"] == "AFFECTED" for item in findings["historical"])


def test_direct_patch_identity_does_not_claim_safety_until_all_findings_reassessed(
    direct_deploy, direct_vm, direct_alice, direct_bob,
):
    contract = direct_deploy("contracts/spatch.py", sdk_version="v0.2.16")
    project_id, dep_id, app_id = draft(contract, direct_vm, direct_alice)
    verified_sealed(contract, direct_vm, project_id, dep_id, app_id, direct_bob)
    for advisory_id in (GHSA, GHSA_B):
        if advisory_id != GHSA:
            direct_vm.clear_mocks()
        advisory_sources(direct_vm, advisory_id)
        dep = contract.get_component(dep_id)
        app = contract.get_component(app_id)
        direct_vm.mock_llm(".*", judgment([
            row(dep_id, dep["revision"], dep["version_revision"], "AFFECTED", "VERSION_IN_AFFECTED_RANGE", "3.1.5"),
            row(app_id, app["revision"], app["version_revision"], "NOT_AFFECTED", "PACKAGE_NOT_TARGETED"),
        ]))
        contract.assess_advisory(project_id, advisory_id)
    direct_vm.sender = direct_alice
    dep = contract.get_component(dep_id)
    contract.patch_component(dep_id, "3.1.5", dep["revision"])
    staged = contract.get_component(dep_id)
    direct_vm.clear_mocks()
    identity(direct_vm, "jinja2", "3.1.5")
    direct_vm.sender = direct_bob
    contract.verify_patch(dep_id, staged["revision"])
    assert contract.get_component(dep_id)["status"] == "SECURITY_REASSESS_REQUIRED"
    assert set(contract.get_findings(dep_id)["pending_advisories"]) == {GHSA, GHSA_B}


@pytest.mark.parametrize(("source_response", "expected_diagnostic"), [
    ({"method": "GET", "status": 503, "body": "offline"}, "OSV_HTTP_503"),
    ({"method": "GET", "status": 200, "body": "{not-json}"}, "OSV_INVALID_JSON_10"),
], ids=["osv-outage", "malformed-osv-json"])
def test_direct_advisory_source_failures_fail_closed(
    direct_deploy, direct_vm, direct_alice, direct_bob, source_response, expected_diagnostic,
):
    contract = direct_deploy("contracts/spatch.py", sdk_version="v0.2.16")
    project_id, dep_id, app_id = draft(contract, direct_vm, direct_alice)
    verified_sealed(contract, direct_vm, project_id, dep_id, app_id, direct_bob)
    direct_vm.mock_web(rf"api\.osv\.dev/v1/vulns/{OSV_GHSA}", source_response)
    web_json(direct_vm, rf"api\.github\.com/advisories/{GHSA}", {
        "ghsa_id": GHSA,
        "summary": "Jinja sandbox breakout through malicious filenames",
        "description": "Jinja2 releases through 3.1.4 are affected.",
        "vulnerabilities": [{
            "package": {"ecosystem": "pip", "name": "jinja2"},
            "vulnerable_version_range": ">= 3.0.0, <= 3.1.4",
            "first_patched_version": {"identifier": "3.1.5"},
        }],
    })
    direct_vm.sender = direct_bob
    assessment_id = int(contract.assess_advisory(project_id, GHSA))
    assessment = contract.get_assessment(assessment_id)
    assert assessment["status"] == "UNRESOLVED"
    assert assessment["reason"] == "ADVISORY_SOURCE_UNAVAILABLE"
    assert assessment["diagnostic"] == expected_diagnostic
    assert contract.get_component(dep_id)["status"] == "UNRESOLVED"
    assert contract.get_component(app_id)["status"] == "UNRESOLVED"
    assert len(assessment["results"]) == 2

    direct_vm.clear_mocks()
    advisory_sources(direct_vm)
    dep = contract.get_component(dep_id)
    app = contract.get_component(app_id)
    direct_vm.mock_llm(".*", judgment([
        row(dep_id, dep["revision"], dep["version_revision"], "AFFECTED", "VERSION_IN_AFFECTED_RANGE", "3.1.5"),
        row(app_id, app["revision"], app["version_revision"], "NOT_AFFECTED", "PACKAGE_NOT_TARGETED"),
    ]))
    retry_id = int(contract.assess_advisory(project_id, GHSA))
    assert retry_id > assessment_id
    assert contract.get_component(dep_id)["status"] == "VULNERABLE"
    assert contract.get_findings(dep_id)["current"][0]["attempts"] == 2


def test_direct_component_and_edge_bounds(direct_deploy, direct_vm, direct_alice):
    contract = direct_deploy("contracts/spatch.py", sdk_version="v0.2.16")
    direct_vm.sender = direct_alice
    project_id = int(contract.create_project("Graph bound checks"))
    component_ids = [int(contract.add_component(project_id, "pypi", f"pkg-{i}", "1.0.0")) for i in range(16)]
    assert contract.add_component(project_id, "pypi", "pkg-over-limit", "1.0.0") == "COMPONENT_LIMIT"

    edges = 0
    for dependent_index in range(1, len(component_ids)):
        for dependency_index in range(dependent_index):
            contract.add_dependency(component_ids[dependent_index], component_ids[dependency_index])
            edges += 1
            if edges == 32:
                assert contract.add_dependency(component_ids[-1], component_ids[-2]) == "EDGE_LIMIT"
                return
    raise AssertionError("The test graph did not reach MAX_EDGES")


def test_direct_history_bound_rejects_patch_without_mutation(
    direct_deploy, direct_vm, direct_alice, direct_bob,
):
    contract = direct_deploy("contracts/spatch.py", sdk_version="v0.2.16")
    project_id, dep_id, app_id = draft(contract, direct_vm, direct_alice)
    verified_sealed(contract, direct_vm, project_id, dep_id, app_id, direct_bob)
    component = contract.get_component(dep_id)
    component["status"] = "VULNERABLE"
    component["security_status"] = "VULNERABLE"
    component["findings"] = [{"advisory_id": GHSA, "version_revision": component["version_revision"], "verdict": "AFFECTED", "component_id": dep_id, "reason_code": "VERSION_IN_AFFECTED_RANGE", "assessment_id": 1, "fixed_version": "3.1.5", "attempts": 1}]
    component["history"] = [
        {"version": f"0.0.{index}", "status": "VULNERABLE"}
        for index in range(8)
    ]
    contract._save_component(component)
    direct_vm.sender = direct_alice
    before = contract.get_component(dep_id)
    assert contract.patch_component(dep_id, "3.1.5", before["revision"]) == "VERSION_HISTORY_LIMIT"
    assert contract.get_component(dep_id) == before
