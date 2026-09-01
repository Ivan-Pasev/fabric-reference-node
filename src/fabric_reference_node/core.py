#!/usr/bin/env python3
"""DFT 2.0 Reference Node — bounded local executable candidate.

Authority boundary:
- Implements finite reference semantics for evidence/authority/invariant/trace workflows.
- Does NOT establish legal compliance, scientific validity, formal proof, security, fairness,
  production readiness, or active CodexStation/Crystal authority.
- CodexStation integration is by typed transfer/binding only; no Crystal authority is inherited.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Dict, Iterable, List, Mapping, Optional

SCHEMA_VERSION = "1.0.0"
MACHINE = {"PASS", "HOLD", "FAIL"}
DECISIONS = {"APPROVE", "REJECT", "ESCALATE", "RESTRICT", "CONTEXTUALIZE", "DEFER", "UNKNOWN"}
AUTH_KEYS = {"definition","paper_proof","formal_check","executable","numerical","empirical","kernel"}

class ContractError(ValueError):
    pass

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)

def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()

@dataclass(frozen=True)
class Obligation:
    obligation_id: str
    status: str
    reason_code: str
    evidence_refs: tuple[str, ...] = ()
    details: Mapping[str, Any] | None = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["evidence_refs"] = list(self.evidence_refs)
        d["details"] = dict(self.details or {})
        return d

class ReferenceNode:
    def __init__(self, node_id: str = "NODE-LOCAL"):
        self.node_id = node_id
        self.artifacts: Dict[str, Dict[str, Any]] = {}
        self.claims: Dict[str, Dict[str, Any]] = {}
        self.evidence: Dict[str, Dict[str, Any]] = {}
        self.policies: Dict[str, Dict[str, Any]] = {}
        self.authorities: Dict[str, Dict[str, Any]] = {}
        self.invariants: Dict[str, Dict[str, Any]] = {}
        self.assessments: Dict[str, Dict[str, Any]] = {}
        self.decisions: Dict[str, Dict[str, Any]] = {}
        self.traces: Dict[str, Dict[str, Any]] = {}
        self.continuations: Dict[str, Dict[str, Any]] = {}
        self.receipts: Dict[str, Dict[str, Any]] = {}
        self.retractions: Dict[str, Dict[str, Any]] = {}

    def capabilities(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "schema_version": SCHEMA_VERSION,
            "machine_outcomes": sorted(MACHINE),
            "institutional_decisions": sorted(DECISIONS),
            "authority_boundary": [
                "EXECUTABLE_REFERENCE_ONLY",
                "NO_LEGAL_COMPLIANCE_INFERENCE",
                "NO_SCIENTIFIC_VALIDITY_INFERENCE",
                "NO_FORMAL_PROOF_INFERENCE",
                "NO_SECURITY_CERTIFICATION_INFERENCE",
                "NO_CRYSTAL_AUTHORITY_INHERITANCE",
            ],
        }

    def _register_unique(self, store: Dict[str, Dict[str, Any]], obj: Mapping[str, Any]) -> Dict[str, Any]:
        oid = str(obj.get("id", ""))
        if not oid:
            raise ContractError("missing id")
        if oid in store:
            if store[oid] != dict(obj):
                raise ContractError(f"immutable id collision: {oid}")
            return deepcopy(store[oid])
        store[oid] = deepcopy(dict(obj))
        return deepcopy(store[oid])

    def add_artifact(self, obj): return self._register_unique(self.artifacts, obj)
    def add_evidence(self, obj): return self._register_unique(self.evidence, obj)
    def add_policy(self, obj): return self._register_unique(self.policies, obj)
    def add_authority(self, obj): return self._register_unique(self.authorities, obj)
    def add_invariant(self, obj): return self._register_unique(self.invariants, obj)
    def add_continuation(self, obj): return self._register_unique(self.continuations, obj)

    def add_claim(self, obj: Mapping[str, Any]) -> Dict[str, Any]:
        authority = obj.get("authority", {})
        if set(authority) != AUTH_KEYS:
            raise ContractError("authority vector incomplete")
        known = set(self.claims)
        missing = set(obj.get("dependencies", ())) - known
        if missing:
            raise ContractError(f"unknown dependencies: {sorted(missing)}")
        if authority["formal_check"] == "PASS" and not obj.get("promotion_receipts"):
            raise ContractError("formal PASS without replayable receipt")
        if obj.get("kind") == "TARGET" and authority["empirical"] == "SUPPORTED":
            raise ContractError("TARGET cannot self-promote to empirically SUPPORTED")
        return self._register_unique(self.claims, obj)

    def _hold(self, oid: str, reason: str, refs: Iterable[str] = ()) -> Obligation:
        return Obligation(oid, "HOLD", reason, tuple(refs))

    def _pass(self, oid: str, reason: str, refs: Iterable[str] = ()) -> Obligation:
        return Obligation(oid, "PASS", reason, tuple(refs))

    def _fail(self, oid: str, reason: str, refs: Iterable[str] = ()) -> Obligation:
        return Obligation(oid, "FAIL", reason, tuple(refs))

    def evaluate(self, request: Mapping[str, Any]) -> Dict[str, Any]:
        aid = request.get("artifact_id")
        claim_ids = list(request.get("claim_ids", []))
        evidence_refs = list(request.get("evidence_refs", []))
        policy_refs = list(request.get("policy_refs", []))
        invariant_refs = list(request.get("invariant_refs", []))
        scope = request.get("scope")
        checks = dict(request.get("invariant_results", {}))

        obligations: List[Obligation] = []
        if aid not in self.artifacts:
            obligations.append(self._hold("OBL-ARTIFACT", "MISSING_ARTIFACT"))
        missing_claims = [x for x in claim_ids if x not in self.claims]
        if missing_claims:
            obligations.append(self._hold("OBL-CLAIMS", "UNKNOWN_CLAIM", missing_claims))
        else:
            obligations.append(self._pass("OBL-CLAIMS", "CLAIMS_RESOLVED", claim_ids))
        missing_ev = [x for x in evidence_refs if x not in self.evidence]
        if not evidence_refs or missing_ev:
            obligations.append(self._hold("OBL-EVIDENCE", "MISSING_EVIDENCE", missing_ev))
        else:
            obligations.append(self._pass("OBL-EVIDENCE", "EVIDENCE_RESOLVED", evidence_refs))
        missing_pol = [x for x in policy_refs if x not in self.policies]
        if not policy_refs or missing_pol:
            obligations.append(self._hold("OBL-POLICY", "MISSING_POLICY", missing_pol))
        else:
            obligations.append(self._pass("OBL-POLICY", "POLICY_RESOLVED", policy_refs))
        if not scope:
            obligations.append(self._hold("OBL-SCOPE", "MISSING_SCOPE"))
        else:
            obligations.append(self._pass("OBL-SCOPE", "SCOPE_DECLARED"))
        missing_inv = [x for x in invariant_refs if x not in self.invariants]
        if not invariant_refs or missing_inv:
            obligations.append(self._hold("OBL-INVARIANTS", "MISSING_INVARIANT_DECLARATION", missing_inv))
        else:
            failed = [x for x in invariant_refs if checks.get(x) is False]
            unknown = [x for x in invariant_refs if x not in checks]
            if failed:
                obligations.append(self._fail("OBL-INVARIANTS", "INVARIANT_VIOLATION", failed))
            elif unknown:
                obligations.append(self._hold("OBL-INVARIANTS", "INVARIANT_UNRESOLVED", unknown))
            else:
                obligations.append(self._pass("OBL-INVARIANTS", "INVARIANTS_PRESERVED", invariant_refs))

        statuses = {o.status for o in obligations}
        machine = "FAIL" if "FAIL" in statuses else ("HOLD" if "HOLD" in statuses else "PASS")
        payload = {
            "id": request.get("assessment_id", f"ASM-{digest(request)[:16].upper()}"),
            "artifact_id": aid,
            "claim_ids": claim_ids,
            "policy_refs": policy_refs,
            "invariant_refs": invariant_refs,
            "obligations": [o.to_dict() for o in obligations],
            "machine_outcome": machine,
            "created_at": request.get("created_at", utc_now()),
            "evidence_refs": evidence_refs,
            "scope": scope,
        }
        self.assessments[payload["id"]] = deepcopy(payload)
        return deepcopy(payload)

    def decide(self, request: Mapping[str, Any]) -> Dict[str, Any]:
        assessment_id = request.get("assessment_id")
        auth_id = request.get("authority_ref")
        outcome = request.get("outcome")
        scope = request.get("scope")
        if assessment_id not in self.assessments:
            raise ContractError("unknown assessment")
        auth = self.authorities.get(auth_id)
        if not auth:
            raise ContractError("unknown authority")
        if auth.get("status") != "ACTIVE":
            raise ContractError("authority not active")
        if scope not in set(auth.get("scopes", [])):
            raise ContractError("authority scope mismatch")
        if outcome not in DECISIONS:
            raise ContractError("invalid institutional decision")
        payload = {
            "id": request.get("id", f"DEC-{digest(request)[:16].upper()}"),
            "assessment_id": assessment_id,
            "authority_ref": auth_id,
            "outcome": outcome,
            "reason_code": request.get("reason_code", "UNSPECIFIED"),
            "rationale_ref": request.get("rationale_ref"),
            "created_at": request.get("created_at", utc_now()),
            "scope": scope,
        }
        self.decisions[payload["id"]] = deepcopy(payload)
        return deepcopy(payload)

    def create_trace(self, request: Mapping[str, Any]) -> Dict[str, Any]:
        if request.get("assessment_ref") not in self.assessments:
            raise ContractError("unknown assessment")
        if request.get("decision_ref") not in self.decisions:
            raise ContractError("unknown decision")
        payload = dict(request)
        payload.setdefault("id", f"TRC-{digest(request)[:16].upper()}")
        payload.setdefault("created_at", utc_now())
        self.traces[payload["id"]] = deepcopy(payload)
        return deepcopy(payload)

    def make_receipt(self, object_type: str, object_id: str, obj: Mapping[str, Any], receipt_id: Optional[str] = None) -> Dict[str, Any]:
        rid = receipt_id or f"RCP-{digest(obj)[:16].upper()}"
        payload = {
            "id": rid,
            "object_type": object_type,
            "object_id": object_id,
            "canonical_hash": digest(obj),
            "schema_version": SCHEMA_VERSION,
            "created_at": utc_now(),
        }
        self.receipts[rid] = deepcopy(payload)
        return deepcopy(payload)

    def verify_receipt(self, receipt: Mapping[str, Any], obj: Mapping[str, Any]) -> bool:
        return receipt.get("schema_version") == SCHEMA_VERSION and receipt.get("canonical_hash") == digest(obj)

    def dependency_closure(self, claim_id: str) -> Dict[str, List[str]]:
        if claim_id not in self.claims:
            raise ContractError("unknown claim")
        upstream = set()
        def up(cid):
            for dep in self.claims[cid].get("dependencies", []):
                if dep not in upstream:
                    upstream.add(dep); up(dep)
        up(claim_id)
        downstream = set()
        def down(cid):
            for other_id, claim in self.claims.items():
                if cid in claim.get("dependencies", []) and other_id not in downstream:
                    downstream.add(other_id); down(other_id)
        down(claim_id)
        return {"upstream": sorted(upstream), "downstream": sorted(downstream)}

    def simulate_retraction(self, claim_id: str, reason_code: str, defeating_ref: str) -> Dict[str, Any]:
        before = digest(self.claims)
        impact = self.dependency_closure(claim_id)["downstream"]
        event = {
            "id": f"RTX-{digest([claim_id,reason_code,defeating_ref,impact])[:16].upper()}",
            "claim_id": claim_id,
            "reason_code": reason_code,
            "defeating_ref": defeating_ref,
            "affected_claims": impact,
            "mode": "SIMULATED",
            "created_at": utc_now(),
        }
        after = digest(self.claims)
        if before != after:
            raise AssertionError("retraction simulation mutated registry")
        return event

    def supersede(self, old_claim_id: str, new_claim: Mapping[str, Any], link_id: Optional[str] = None) -> Dict[str, Any]:
        if old_claim_id not in self.claims:
            raise ContractError("unknown predecessor claim")
        self.add_claim(new_claim)
        link = {
            "id": link_id or f"CON-{digest([old_claim_id,new_claim['id']])[:16].upper()}",
            "source_ref": new_claim["id"],
            "relation": "SUPERSEDES",
            "target_ref": old_claim_id,
            "created_at": utc_now(),
        }
        self.add_continuation(link)
        return deepcopy(link)

    def export_bundle(self) -> Dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "node_id": self.node_id,
            "objects": {
                "artifacts": list(self.artifacts.values()),
                "claims": list(self.claims.values()),
                "evidence": list(self.evidence.values()),
                "policies": list(self.policies.values()),
                "authorities": list(self.authorities.values()),
                "invariants": list(self.invariants.values()),
                "assessments": list(self.assessments.values()),
                "decisions": list(self.decisions.values()),
                "traces": list(self.traces.values()),
                "continuations": list(self.continuations.values()),
                "receipts": list(self.receipts.values()),
                "retractions": list(self.retractions.values()),
            }
        }

    @classmethod
    def from_bundle(cls, bundle: Mapping[str, Any]) -> "ReferenceNode":
        node = cls(bundle["node_id"])
        objects = bundle["objects"]
        for key in ["artifacts","claims","evidence","policies","authorities","invariants","assessments","decisions","traces","continuations","receipts","retractions"]:
            store = getattr(node, key)
            for obj in objects.get(key, []):
                store[obj["id"]] = deepcopy(obj)
        return node
