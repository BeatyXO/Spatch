"""Official genlayer-test Direct Mode coverage for the deployed contract runtime."""

import json

import pytest

GHSA = "GHSA-GMJ6-6F8F-6699"


def web_json(vm, pattern, value, status=200):
    vm.mock_web(pattern, {"method": "GET", "status": status, "body": json.dumps(value)})


def identity(vm, name, version):
    web_json(vm, rf"api\.deps\.dev/.*/{name}/versions/{version}", {
        "versionKey": {"system": "PYPI", "name": name, "version": version}
    })


def advisory_sources(vm):
    web_json(vm, rf"api\.osv\.dev/v1/vulns/{GHSA.lower()}", {
        "id": GHSA,
        "affected": [{
            "package": {"ecosystem": "PyPI", "name": "jinja2"},
            "ranges": [{"type": "ECOSYSTEM", "events": [{"introduced": "3.0.0"}, {"fixed": "3.1.5"}]}],
        }],
    })
    web_json(vm, rf"api\.github\.com/advisories/{GHSA}", {
        "ghsa_id": GHSA,
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
    assert contract.get_component(dep_id)["status"] == "VULNERABLE"
    assert contract.get_component(app_id)["status"] == "RECHECK_REQUIRED"
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

    identity(direct_vm, "jinja2", "3.1.5")
    direct_vm.sender = direct_bob
    assert int(contract.verify_patch(dep_id, staged["revision"])) > 0
    patched = contract.get_component(dep_id)
    assert patched["version_revision"] == 2
    assert patched["status"] == "ACTIVE"

    advisory_sources(direct_vm)
    direct_vm.mock_llm(".*", judgment([
        row(dep_id, patched["revision"], patched["version_revision"], "NOT_AFFECTED", "VERSION_OUTSIDE_AFFECTED_RANGE", "3.1.5"),
    ]))
    next_assessment = int(contract.assess_advisory(project_id, GHSA))
    assert next_assessment > assessment_id
    assert contract.get_component(dep_id)["status"] == "ACTIVE"
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
    assert assessment["reason"] == "MODEL_SCHEMA_INVALID", assessment
    assert contract.get_component(dep_id)["status"] == "ACTIVE"


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
    direct_vm.mock_web(rf"api\.osv\.dev/v1/vulns/{GHSA.lower()}", source_response)
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
    assert contract.get_component(dep_id)["status"] == "ACTIVE"
    assert contract.get_component(app_id)["status"] == "ACTIVE"


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
    component["history"] = [
        {"version": f"0.0.{index}", "status": "VULNERABLE"}
        for index in range(8)
    ]
    contract._save_component(component)
    direct_vm.sender = direct_alice
    before = contract.get_component(dep_id)
    assert contract.patch_component(dep_id, "3.1.5", before["revision"]) == "VERSION_HISTORY_LIMIT"
    assert contract.get_component(dep_id) == before
