from fabric_reference_node import ReferenceNode, digest

TS = "2026-09-01T00:00:00Z"
AUTH = {
    "definition":"CLOSED",
    "paper_proof":"NONE",
    "formal_check":"NONE",
    "executable":"NONE",
    "numerical":"NONE",
    "empirical":"NONE",
    "kernel":"INACTIVE",
}

def artifact(aid="ART-1"):
    return {
        "id": aid,
        "kind": "DECISION_CASE",
        "state_ref": f"STATE-{aid}",
        "created_at": TS,
        "provenance_refs": ["synthetic://case"],
        "metadata": {"synthetic": True},
    }

def claim(cid="CLM-1", aid="ART-1", deps=None, contradictions=None):
    return {
        "id": cid,
        "artifact_id": aid,
        "statement": f"Synthetic statement {cid}",
        "public_statuses": ["AA"],
        "kind": "DEF",
        "authority": dict(AUTH),
        "sources": ["synthetic://case"],
        "dependencies": list(deps or []),
        "contradictions": list(contradictions or []),
        "lifecycle": "ACTIVE",
        "promotion_receipts": [],
    }

def evidence(eid="EVD-1", aid="ART-1", claims=None):
    return {
        "id": eid,
        "artifact_id": aid,
        "claim_ids": list(claims or ["CLM-1"]),
        "evidence_class": "SOURCE",
        "source_ref": "synthetic://case",
        "content_hash": digest({"synthetic": eid}),
        "created_at": TS,
        "metadata": {"synthetic": True},
    }

def policy(pid="POL-1"):
    return {
        "id": pid,
        "version": "1",
        "scope": ["scope:a"],
        "rule_ref": "synthetic://policy/1",
        "effect": "REQUIRE",
        "external_standard_refs": [],
    }

def authority(auth_id="AUTH-1"):
    return {
        "id": auth_id,
        "actor_id": "actor:synthetic-reviewer",
        "role": "REVIEWER",
        "jurisdiction": "synthetic",
        "scopes": ["scope:a"],
        "delegated_by": None,
        "credential_refs": [],
        "valid_from": TS,
        "valid_until": None,
        "status": "ACTIVE",
    }

def invariant(iid="INV-1"):
    return {
        "id": iid,
        "type": "AUTHORIZATION_JURISDICTION",
        "statement": "Declared scope must be preserved",
        "check_ref": "builtin://scope-preserved",
        "severity": "HIGH",
    }

def setup_node(node_id="NODE-TEST"):
    n = ReferenceNode(node_id)
    n.add_artifact(artifact())
    n.add_claim(claim())
    n.add_evidence(evidence())
    n.add_policy(policy())
    n.add_authority(authority())
    n.add_invariant(invariant())
    return n
