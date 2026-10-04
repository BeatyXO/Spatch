import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest

CREATOR = "0x1111111111111111111111111111111111111111"
OBSERVER = "0x2222222222222222222222222222222222222222"
OUTSIDER = "0x3333333333333333333333333333333333333333"
GHSA = "GHSA-2g3v-6x4w-9r2p"


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
            payload = {
                "id": GHSA,
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
            payload = {
                "ghsa_id": GHSA,
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
    assert patched["status"] == "ACTIVE"
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
    assert contract.get_component(U256(1))["status"] == "ACTIVE"


def test_protocol_declares_revision_scoped_replay_and_stable_studionet(runtime):
    contract, _, _ = runtime
    protocol = contract.get_protocol()
    assert protocol["name"] == "Spatch"
    assert protocol["chain_id"] == 61999
    assert protocol["replay_scope"] == "project:component:version_revision:advisory"
    assert "old-version-history-preserved" in protocol["patch_policy"]
