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

node = ReferenceNode("NODE-DEMO")
node.add_artifact({
    "id":"ART-1", "kind":"DECISION_CASE", "state_ref":"STATE-0", "created_at":TS,
    "provenance_refs":["synthetic://case"], "metadata":{"title":"Synthetic access request"}
})
node.add_claim({
    "id":"CLM-1", "artifact_id":"ART-1", "statement":"Request is within declared project scope",
    "public_statuses":["AA"], "kind":"DEF", "authority":dict(AUTH), "sources":["synthetic://case"],
    "dependencies":[], "contradictions":[], "lifecycle":"ACTIVE", "promotion_receipts":[]
})
node.add_evidence({
    "id":"EVD-1", "artifact_id":"ART-1", "claim_ids":["CLM-1"], "evidence_class":"SOURCE",
    "source_ref":"synthetic://case", "content_hash":digest({"case":"synthetic"}), "created_at":TS,
    "metadata":{"synthetic":True}
})
node.add_policy({
    "id":"POL-1", "version":"1", "scope":["demo:access"], "rule_ref":"synthetic://policy/1",
    "effect":"REQUIRE", "external_standard_refs":[]
})
node.add_authority({
    "id":"AUTH-1", "actor_id":"actor:synthetic-reviewer", "role":"REVIEWER", "jurisdiction":"synthetic",
    "scopes":["demo:access"], "delegated_by":None, "credential_refs":[], "valid_from":TS,
    "valid_until":None, "status":"ACTIVE"
})
node.add_invariant({
    "id":"INV-1", "type":"AUTHORIZATION_JURISDICTION", "statement":"Declared scope must be preserved",
    "check_ref":"builtin://scope-preserved", "severity":"HIGH"
})

assessment = node.evaluate({
    "assessment_id":"ASM-1", "artifact_id":"ART-1", "claim_ids":["CLM-1"],
    "evidence_refs":["EVD-1"], "policy_refs":["POL-1"], "invariant_refs":["INV-1"],
    "scope":"demo:access", "invariant_results":{"INV-1": True}, "created_at":TS
})

decision = node.decide({
    "id":"DEC-1", "assessment_id":assessment["id"], "authority_ref":"AUTH-1",
    "outcome":"APPROVE", "reason_code":"SYNTHETIC_DEMO", "scope":"demo:access", "created_at":TS
})

trace = node.create_trace({
    "id":"TRC-1", "artifact_id":"ART-1", "prior_state_ref":"STATE-0", "transform_id":"TRANSFORM-DEMO",
    "policy_refs":["POL-1"], "authority_ref":"AUTH-1", "invariants_checked":["INV-1"],
    "evidence_refs":["EVD-1"], "validator_refs":[], "assessment_ref":assessment["id"],
    "decision_ref":decision["id"], "reason_code":"SYNTHETIC_DEMO", "result_state_ref":"STATE-1",
    "created_at":TS, "continuation_links":[]
})
receipt = node.make_receipt("TRACE", trace["id"], trace, receipt_id="RCP-TRACE-1")

print("machine_outcome:", assessment["machine_outcome"])
print("institutional_decision:", decision["outcome"])
print("trace_receipt_verified:", node.verify_receipt(receipt, trace))
print("important: machine PASS is not institutional approval; both are recorded separately")
