import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest

CREATOR = "0x1111111111111111111111111111111111111111"
OBSERVER = "0x2222222222222222222222222222222222222222"
OUTSIDER = "0x3333333333333333333333333333333333333333"
GHSA = "GHSA-2G3V-6X4W-9R2P"
GHSA_B = "GHSA-3P2H-W9Q8-4V6R"


class TreeMap(dict):
    @classmethod
    def __class_getitem__(cls, _):
        return cls


class U256(int):
    pass


class ContractBase:
    def __init_subclass__(cls, **kwargs):
        original = cls.__dict__.get("__init__")

        def init(self, *args, **kw):
            for name, kind in cls.__annotations__.items():
                if kind is TreeMap:
                    setattr(self, name, TreeMap())
            original(self, *args, **kw)

        cls.__init__ = init


class Write:
    def __call__(self, fn):
        return fn


class Public:
    write = Write()
    view = staticmethod(lambda fn: fn)


class Response:
    def __init__(self, status=200, body=b""):
        self.status = status
        self.body = body


class Return:
    def __init__(self, calldata):
        self.calldata = calldata


class VM:
    Return = Return

    @staticmethod
    def run_nondet_unsafe(leader_fn, validator_fn):
        result = leader_fn()
        if not validator_fn(Return(result)):
            raise RuntimeError("validator disagreement")
        return result


class Eq:
    @staticmethod
    def strict_eq(fn):
        return fn()


class Nondet:
    def __init__(self):
        self.web = types.SimpleNamespace(get=self.get)
        self.answer = {
            "results": [
                {
                    "component_id": 1,
                    "component_revision": 1,
                    "version_revision": 1,
                    "verdict": "AFFECTED",
                    "reason_code": "VERSION_IN_AFFECTED_RANGE",
                    "fixed_version": "3.1.6",
                },
                {
                    "component_id": 2,
                    "component_revision": 1,
                    "version_revision": 1,
                    "verdict": "NOT_AFFECTED",
                    "reason_code": "PACKAGE_NOT_TARGETED",
                    "fixed_version": "",
                },
            ]
        }
        self.override = {}

    def get(self, url, headers=None):
        for key, response in self.override.items():
            if key in url:
                return response
        if "api.deps.dev" in url:
            if "/jinja2/versions/3.1.4" in url:
                payload = {"versionKey": {"system": "PYPI", "name": "jinja2", "version": "3.1.4"}}
            elif "/jinja2/versions/3.1.6" in url:
                payload = {"versionKey": {"system": "PYPI", "name": "jinja2", "version": "3.1.6"}}
            elif "/flask/versions/3.0.0" in url:
                payload = {"versionKey": {"system": "PYPI", "name": "flask", "version": "3.0.0"}}
            else:
                return Response(404, b"{}")
            return Response(200, json.dumps(payload).encode())
        if "api.osv.dev" in url:
            advisory_id = url.rsplit("/", 1)[-1].upper()
            payload = {
                "id": advisory_id,
                "aliases": ["CVE-2026-12345"],
                "affected": [
                    {
                        "package": {"ecosystem": "PyPI", "name": "jinja2"},
                        "ranges": [
                            {
                                "type": "ECOSYSTEM",
                                "events": [
                                    {"introduced": "0"},
                                    {"fixed": "3.1.6"},
                                ],
                            }
                        ],
                    }
                ],
            }
            return Response(200, json.dumps(payload).encode())
        if "api.github.com/advisories" in url:
            advisory_id = url.rsplit("/", 1)[-1].upper()
            payload = {
                "ghsa_id": advisory_id,
                "cve_id": "CVE-2026-12345",
                "summary": "Template rendering vulnerability",
                "description": "Versions before 3.1.6 are affected in a specific rendering path.",
                "vulnerabilities": [
                    {
                        "package": {"ecosystem": "pip", "name": "jinja2"},
                        "vulnerable_version_range": "< 3.1.6",
                        "first_patched_version": {"identifier": "3.1.6"},
                    }
                ],
            }
            return Response(200, json.dumps(payload).encode())
        return Response(404, b"{}")

    def exec_prompt(self, *args, **kwargs):
        return self.answer


@pytest.fixture
def runtime(monkeypatch):
    nondet = Nondet()
    gl = types.ModuleType("genlayer")
    gl.__all__ = ["gl", "u256", "TreeMap", "typing"]
    gl.gl = gl
    gl.Contract = ContractBase
    gl.public = Public()
    gl.nondet = nondet
    gl.eq_principle = Eq()
    gl.vm = VM()
    gl.message = types.SimpleNamespace(sender_address=CREATOR)
    gl.message_raw = {"datetime": "2026-10-04T12:00:00+00:00"}
    gl.u256 = U256
    gl.TreeMap = TreeMap
    gl.typing = types.SimpleNamespace(Any=object)
    monkeypatch.setitem(sys.modules, "genlayer", gl)
    spec = importlib.util.spec_from_file_location("spatch_test", Path("contracts/spatch.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Spatch(), gl, nondet


def build_draft(contract):
    assert int(contract.create_project("Blue dependency security graph")) == 1
    # Dependencies must be older IDs than the components that consume them.
    assert int(contract.add_component(U256(1), "pypi", "jinja2", "3.1.4")) == 1
    assert int(contract.add_component(U256(1), "pypi", "flask", "3.0.0")) == 2
    assert int(contract.add_dependency(U256(2), U256(1))) == 1


def verify_and_seal(contract):
    build_draft(contract)
    for cid in (1, 2):
        component = contract.get_component(U256(cid))
        aid = contract.verify_component(U256(cid), U256(component["revision"]))
        assert int(aid) == cid
        assert contract.get_component(U256(cid))["status"] == "ACTIVE"
    assert contract.seal_project(U256(1)) == "SEALED"


def advisory_rows(contract, dep_verdict, dep_reason, app_verdict="NOT_AFFECTED", app_reason="PACKAGE_NOT_TARGETED"):
    dep = contract.get_component(U256(1))
    app = contract.get_component(U256(2))
    return {"results": [
        {"component_id": 1, "component_revision": dep["revision"], "version_revision": dep["version_revision"], "verdict": dep_verdict, "reason_code": dep_reason, "fixed_version": "3.1.6"},
        {"component_id": 2, "component_revision": app["revision"], "version_revision": app["version_revision"], "verdict": app_verdict, "reason_code": app_reason, "fixed_version": ""},
    ]}


def ghsa_for_index(index):
    alphabet = "23456789cfghjmpqrvwx"
    digits = ["2"] * 12
    value = index
    for position in range(11, -1, -1):
        digits[position] = alphabet[value % len(alphabet)]
        value //= len(alphabet)
    return ("GHSA-" + "".join(digits[:4]) + "-" + "".join(digits[4:8]) + "-" + "".join(digits[8:])).upper()


def test_components_start_unverified_and_seal_fails(runtime):
    contract, _, _ = runtime
    build_draft(contract)
    assert contract.get_component(U256(1))["status"] == "PENDING_IDENTITY"
    assert contract.seal_project(U256(1)) == "COMPONENT_IDENTITY_NOT_CURRENT"


def test_identity_verification_is_exact_and_permissionless(runtime):
    contract, gl, _ = runtime
    build_draft(contract)
    gl.message.sender_address = OBSERVER
    component = contract.get_component(U256(1))
    aid = contract.verify_component(U256(1), U256(component["revision"]))
    assert int(aid) == 1
    current = contract.get_component(U256(1))
    assert current["identity_status"] == "VERIFIED"
    assert current["verified_version_revision"] == current["version_revision"]
    assert current["identity_evidence_digest"].startswith("sha256:")


def test_creator_only_graph_mutation(runtime):
    contract, gl, _ = runtime
    assert int(contract.create_project("Creator controlled graph")) == 1
    gl.message.sender_address = OUTSIDER
    assert contract.add_component(U256(1), "pypi", "jinja2", "3.1.4") == "ONLY_PROJECT_CREATOR"


def test_seal_requires_real_dependency(runtime):
    contract, _, _ = runtime
    assert int(contract.create_project("No edge graph")) == 1
    assert int(contract.add_component(U256(1), "pypi", "jinja2", "3.1.4")) == 1
    assert int(contract.add_component(U256(1), "pypi", "flask", "3.0.0")) == 2
    for cid in (1, 2):
        component = contract.get_component(U256(cid))
        contract.verify_component(U256(cid), U256(component["revision"]))
    assert contract.seal_project(U256(1)) == "GRAPH_MISSING_DEPENDENCY"


def test_advisory_marks_affected_component_and_propagates(runtime):
    contract, _, nondet = runtime
    verify_and_seal(contract)
    # Component revisions remain 1 after identity verification because verification binds rather than edits identity.
    nondet.answer = {
        "results": [
            {"component_id": 1, "component_revision": 1, "version_revision": 1, "verdict": "AFFECTED", "reason_code": "VERSION_IN_AFFECTED_RANGE", "fixed_version": "3.1.6"},
            {"component_id": 2, "component_revision": 1, "version_revision": 1, "verdict": "NOT_AFFECTED", "reason_code": "PACKAGE_NOT_TARGETED", "fixed_version": ""},
        ]
    }
    aid = contract.assess_advisory(U256(1), GHSA)
    assert int(aid) == 3
    root = contract.get_component(U256(1))
    dependent = contract.get_component(U256(2))
    assert root["status"] == "VULNERABLE"
    assert dependent["status"] == "RECHECK_REQUIRED"
    assert dependent["last_assessment_id"] == 3
    assert contract.get_project(U256(1))["last_assessment_id"] == 3


def test_replay_is_version_scoped_and_blocks_same_version(runtime):
    contract, _, nondet = runtime
    verify_and_seal(contract)
    nondet.answer = {
        "results": [
            {"component_id": 1, "component_revision": 1, "version_revision": 1, "verdict": "AFFECTED", "reason_code": "VERSION_IN_AFFECTED_RANGE", "fixed_version": "3.1.6"},
            {"component_id": 2, "component_revision": 1, "version_revision": 1, "verdict": "NOT_AFFECTED", "reason_code": "PACKAGE_NOT_TARGETED", "fixed_version": ""},
        ]
    }
    contract.assess_advisory(U256(1), GHSA)
    assert contract.assess_advisory(U256(1), GHSA) == "ADVISORY_ALREADY_ASSESSED_FOR_CURRENT_REVISIONS"

def test_patch_preserves_history_requires_fresh_identity_and_allows_reassessment(runtime):
    contract, gl, nondet = runtime
    verify_and_seal(contract)
    nondet.answer = {
        "results": [
            {"component_id": 1, "component_revision": 1, "version_revision": 1, "verdict": "AFFECTED", "reason_code": "VERSION_IN_AFFECTED_RANGE", "fixed_version": "3.1.6"},
            {"component_id": 2, "component_revision": 1, "version_revision": 1, "verdict": "NOT_AFFECTED", "reason_code": "PACKAGE_NOT_TARGETED", "fixed_version": ""},
        ]
    }
    contract.assess_advisory(U256(1), GHSA)
    root = contract.get_component(U256(1))
    dependent = contract.get_component(U256(2))
    assert dependent["status"] == "RECHECK_REQUIRED"

    gl.message.sender_address = CREATOR
    assert contract.patch_component(U256(1), "3.1.6", U256(root["revision"])) == "PATCH_VERSION_STAGED"
    staged = contract.get_component(U256(1))
    assert staged["status"] == "PATCH_PENDING"
    assert staged["version"] == "3.1.6"
    assert staged["version_revision"] == 2
    assert staged["identity_evidence_digest"] == ""
    assert staged["history"][0]["version"] == "3.1.4"
    assert staged["history"][0]["version_revision"] == 1
    assert staged["history"][0]["status"] == "VULNERABLE"

    gl.message.sender_address = OBSERVER
    identity_aid = contract.verify_patch(U256(1), U256(staged["revision"]))
    assert int(identity_aid) == 4
    patched = contract.get_component(U256(1))
    assert patched["status"] == "SECURITY_REASSESS_REQUIRED"
    assert patched["security_status"] == "SECURITY_REASSESS_REQUIRED"
    assert patched["version"] == "3.1.6"
    assert patched["verified_version_revision"] == 2

    # Same GHSA becomes eligible only for the component whose version revision changed.
    nondet.answer = {
        "results": [
            {"component_id": 1, "component_revision": patched["revision"], "version_revision": patched["version_revision"], "verdict": "NOT_AFFECTED", "reason_code": "VERSION_OUTSIDE_AFFECTED_RANGE", "fixed_version": "3.1.6"},
        ]
    }
    reassessment = contract.assess_advisory(U256(1), GHSA)
    assert int(reassessment) == 5
    assert contract.get_component(U256(1))["status"] == "ACTIVE"
    assert contract.get_findings(U256(1))["pending_advisories"] == []

    # The dependent can now deterministically clear its recheck state without another LLM call.
    dependent = contract.get_component(U256(2))
    recovery = contract.reassess_dependency(U256(2), U256(dependent["revision"]))
    assert int(recovery) == 6
    recovered = contract.get_component(U256(2))
    assert recovered["status"] == "ACTIVE"
    assert recovered["reason"] == "DEPENDENCIES_STABLE_AFTER_RECHECK"

def test_source_failure_fails_closed(runtime):
    contract, _, nondet = runtime
    verify_and_seal(contract)
    nondet.override["api.osv.dev"] = Response(503, b"temporarily unavailable")
    aid = contract.assess_advisory(U256(1), GHSA)
    assessment = contract.get_assessment(aid)
    assert assessment["status"] == "UNRESOLVED"
    assert assessment["reason"] == "ADVISORY_SOURCE_UNAVAILABLE"
    assert contract.get_component(U256(1))["status"] == "UNRESOLVED"
    assert contract.get_findings(U256(1))["current"][0]["reason_code"] == "ADVISORY_SOURCE_UNAVAILABLE"


def test_cross_advisory_not_affected_cannot_clear_another_vulnerability(runtime):
    contract, gl, nondet = runtime
    verify_and_seal(contract)
    nondet.answer = advisory_rows(contract, "AFFECTED", "VERSION_IN_AFFECTED_RANGE")
    contract.assess_advisory(U256(1), GHSA)
    assert contract.get_component(U256(1))["status"] == "VULNERABLE"

    nondet.answer = advisory_rows(contract, "NOT_AFFECTED", "VERSION_OUTSIDE_AFFECTED_RANGE")
    gl.message.sender_address = OBSERVER
    contract.assess_advisory(U256(1), GHSA_B)
    root = contract.get_component(U256(1))
    findings = contract.get_findings(U256(1))["current"]
    assert root["status"] == "VULNERABLE"
    assert {f["advisory_id"]: f["verdict"] for f in findings} == {GHSA: "AFFECTED", GHSA_B: "NOT_AFFECTED"}


def test_multiple_findings_require_all_affected_and_unresolved_advisories_resolved(runtime):
    contract, gl, nondet = runtime
    verify_and_seal(contract)
    nondet.answer = advisory_rows(contract, "AFFECTED", "VERSION_IN_AFFECTED_RANGE")
    contract.assess_advisory(U256(1), GHSA)
    nondet.answer = advisory_rows(contract, "AFFECTED", "VERSION_IN_AFFECTED_RANGE")
    contract.assess_advisory(U256(1), GHSA_B)
    assert contract.get_component(U256(1))["status"] == "VULNERABLE"

    gl.message.sender_address = CREATOR
    root = contract.get_component(U256(1))
    assert contract.patch_component(U256(1), "3.1.6", U256(root["revision"])) == "PATCH_VERSION_STAGED"
    staged = contract.get_component(U256(1))
    gl.message.sender_address = OBSERVER
    contract.verify_patch(U256(1), U256(staged["revision"]))
    assert contract.get_component(U256(1))["status"] == "SECURITY_REASSESS_REQUIRED"

    nondet.answer = {"results": [{
        "component_id": 1,
        "component_revision": contract.get_component(U256(1))["revision"],
        "version_revision": 2,
        "verdict": "NOT_AFFECTED",
        "reason_code": "VERSION_OUTSIDE_AFFECTED_RANGE",
        "fixed_version": "3.1.6",
    }]}
    contract.assess_advisory(U256(1), GHSA)
    assert contract.get_component(U256(1))["status"] == "SECURITY_REASSESS_REQUIRED"
    assert contract.get_findings(U256(1))["pending_advisories"] == [GHSA_B]

    nondet.answer = {"results": [{
        "component_id": 1,
        "component_revision": contract.get_component(U256(1))["revision"],
        "version_revision": 2,
        "verdict": "UNRESOLVED",
        "reason_code": "SOURCE_CONFLICT",
        "fixed_version": "",
    }]}
    contract.assess_advisory(U256(1), GHSA_B)
    assert contract.get_component(U256(1))["status"] == "UNRESOLVED"

    nondet.answer = {"results": [{
        "component_id": 1,
        "component_revision": contract.get_component(U256(1))["revision"],
        "version_revision": 2,
        "verdict": "NOT_AFFECTED",
        "reason_code": "VERSION_OUTSIDE_AFFECTED_RANGE",
        "fixed_version": "3.1.6",
    }]}
    contract.assess_advisory(U256(1), GHSA_B)
    assert contract.get_component(U256(1))["status"] == "ACTIVE"
    findings = contract.get_findings(U256(1))
    assert {f["advisory_id"]: f["verdict"] for f in findings["current"]} == {
        GHSA: "NOT_AFFECTED", GHSA_B: "NOT_AFFECTED"
    }


def test_unresolved_advisory_is_retryable_but_terminal_result_replays_are_blocked(runtime):
    contract, gl, nondet = runtime
    verify_and_seal(contract)
    nondet.answer = advisory_rows(contract, "UNRESOLVED", "INSUFFICIENT_RANGE_DETAIL", "UNRESOLVED", "SOURCE_CONFLICT")
    first_id = contract.assess_advisory(U256(1), GHSA)
    assert contract.get_component(U256(1))["status"] == "UNRESOLVED"
    assert not contract.used_advisory.get("1:1:1:" + GHSA)
    unresolved_component = contract.get_component(U256(1))
    assert contract.verify_component(U256(1), U256(unresolved_component["revision"])) == "COMPONENT_IDENTITY_ALREADY_CURRENT"
    assert contract.get_component(U256(1))["status"] == "UNRESOLVED"

    nondet.answer = advisory_rows(contract, "NOT_AFFECTED", "VERSION_OUTSIDE_AFFECTED_RANGE")
    gl.message.sender_address = OBSERVER
    second_id = contract.assess_advisory(U256(1), GHSA)
    assert int(second_id) > int(first_id)
    assert contract.get_component(U256(1))["status"] == "ACTIVE"
    assert contract.get_findings(U256(1))["current"][0]["attempts"] == 2
    count = contract.get_counts()["assessments"]
    assert contract.assess_advisory(U256(1), GHSA) == "ADVISORY_ALREADY_ASSESSED_FOR_CURRENT_REVISIONS"
    assert contract.get_counts()["assessments"] == count


def test_relevant_advisory_survives_finding_capacity_and_version_change(runtime):
    contract, gl, nondet = runtime
    verify_and_seal(contract)

    # Permissionless benign results may fill the bounded display cache, but each
    # complete judgment and terminal replay key remains in its durable ledger.
    benign_ids = [ghsa_for_index(index) for index in range(1, 33)]
    for advisory_id in benign_ids:
        nondet.answer = advisory_rows(
            contract, "NOT_AFFECTED", "VERSION_OUTSIDE_AFFECTED_RANGE"
        )
        assert int(contract.assess_advisory(U256(1), advisory_id)) > 0
    root = contract.get_component(U256(1))
    assert len(root["findings"]) == 32
    assert all(finding["verdict"] == "NOT_AFFECTED" for finding in root["findings"])

    # A relevant GHSA remains assessable at the full boundary by reclaiming a
    # benign slot, without changing terminal replay protection.
    relevant_id = ghsa_for_index(33)
    nondet.answer = advisory_rows(
        contract, "AFFECTED", "VERSION_IN_AFFECTED_RANGE"
    )
    relevant_assessment = contract.assess_advisory(U256(1), relevant_id)
    assert int(relevant_assessment) > 0
    root = contract.get_component(U256(1))
    assert root["status"] == "VULNERABLE"
    assert len(root["findings"]) == 32
    assert any(
        finding["advisory_id"] == relevant_id and finding["verdict"] == "AFFECTED"
        for finding in root["findings"]
    )
    assert contract.get_assessment(3)["advisory_id"] == benign_ids[0]
    assert contract.assess_advisory(U256(1), benign_ids[0]) == "ADVISORY_ALREADY_ASSESSED_FOR_CURRENT_REVISIONS"

    # Patch history preserves the affected GHSA reference while retired-version
    # findings stop consuming the replacement version's bounded capacity.
    gl.message.sender_address = CREATOR
    assert contract.patch_component(U256(1), "3.1.6", U256(root["revision"])) == "PATCH_VERSION_STAGED"
    staged = contract.get_component(U256(1))
    assert staged["version_revision"] == 2
    assert staged["findings"] == []
    assert staged["history"][0]["findings"][-1]["advisory_id"] == relevant_id
    assert staged["history"][0]["findings"][-1]["verdict"] == "AFFECTED"

    gl.message.sender_address = OBSERVER
    assert int(contract.verify_patch(U256(1), U256(staged["revision"]))) > 0
    patched = contract.get_component(U256(1))
    nondet.answer = {"results": [{
        "component_id": 1,
        "component_revision": patched["revision"],
        "version_revision": 2,
        "verdict": "NOT_AFFECTED",
        "reason_code": "VERSION_OUTSIDE_AFFECTED_RANGE",
        "fixed_version": "3.1.6",
    }]}
    reassessment = contract.assess_advisory(U256(1), relevant_id)
    assert int(reassessment) > 0
    final_root = contract.get_component(U256(1))
    assert final_root["status"] == "ACTIVE"
    assert final_root["version_revision"] == 2
    findings = contract.get_findings(U256(1))
    assert findings["current"][0]["advisory_id"] == relevant_id
    assert findings["current"][0]["verdict"] == "NOT_AFFECTED"
    historical = [row for row in findings["historical"] if row["advisory_id"] == relevant_id]
    assert historical and historical[0]["verdict"] == "AFFECTED"


def test_identity_verification_cannot_clear_security_recheck(runtime):
    contract, gl, nondet = runtime
    verify_and_seal(contract)
    nondet.answer = advisory_rows(contract, "AFFECTED", "VERSION_IN_AFFECTED_RANGE")
    contract.assess_advisory(U256(1), GHSA)
    dependent = contract.get_component(U256(2))
    assert dependent["status"] == "RECHECK_REQUIRED"
    gl.message.sender_address = OBSERVER
    assert contract.verify_component(U256(2), U256(dependent["revision"])) == "COMPONENT_IDENTITY_ALREADY_CURRENT"
    assert contract.get_component(U256(2))["status"] == "RECHECK_REQUIRED"


def test_protocol_declares_revision_scoped_replay_and_stable_studionet(runtime):
    contract, _, _ = runtime
    protocol = contract.get_protocol()
    assert protocol["name"] == "Spatch"
    assert protocol["chain_id"] == 61999
    assert protocol["replay_scope"] == "project:component:version_revision:advisory"
    assert protocol["version"] == 2
    assert "old findings preserved" in protocol["patch_policy"]
