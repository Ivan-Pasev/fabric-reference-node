from fabric_reference_node import ReferenceNode

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
node.add_artifact({"id":"ART-1", "type":"DECISION_CASE", "title":"Synthetic access request"})
node.add_claim({
    "id":"CLM-1", "artifact_id":"ART-1", "statement":"Request is within declared project scope",
    "public_statuses":["AA"], "kind":"DEF", "authority":dict(AUTH), "sources":["synthetic://case"],
    "dependencies":[], "contradictions":[], "lifecycle":"ACTIVE", "promotion_receipts":[]
})
node.add_evidence({"id":"EV-1", "type":"SYNTHETIC", "source":"synthetic://case"})
node.add_policy({"id":"POL-1", "name":"Demo policy", "version":"1"})
node.add_authority({"id":"AUTH-1", "actor":"reviewer@example.invalid", "status":"ACTIVE", "scopes":["demo:access"]})
node.add_invariant({"id":"INV-1", "name":"Declared scope must be preserved"})

assessment = node.evaluate({
    "assessment_id":"ASM-1", "artifact_id":"ART-1", "claim_ids":["CLM-1"],
    "evidence_refs":["EV-1"], "policy_refs":["POL-1"], "invariant_refs":["INV-1"],
    "scope":"demo:access", "invariant_results":{"INV-1": True}
})

decision = node.decide({
    "id":"DEC-1", "assessment_id":assessment["id"], "authority_ref":"AUTH-1",
    "outcome":"APPROVE", "reason_code":"SYNTHETIC_DEMO", "scope":"demo:access"
})

trace = node.create_trace({
    "id":"TRC-1", "assessment_ref":assessment["id"], "decision_ref":decision["id"],
    "artifact_ref":"ART-1", "evidence_refs":["EV-1"], "policy_refs":["POL-1"],
    "authority_ref":"AUTH-1", "invariant_refs":["INV-1"]
})
receipt = node.make_receipt("TRACE", trace["id"], trace)

print("machine_outcome:", assessment["machine_outcome"])
print("institutional_decision:", decision["outcome"])
print("trace_receipt_verified:", node.verify_receipt(receipt, trace))
print("important: machine PASS is not institutional approval; both are recorded separately")
