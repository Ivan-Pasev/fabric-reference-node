import json
from pathlib import Path
import unittest
from jsonschema import Draft202012Validator, FormatChecker

from tests.fixtures import setup_node, TS

SCHEMA = json.loads((Path(__file__).resolve().parents[1] / "schemas" / "reference-node.schema.json").read_text())

class ConformanceTests(unittest.TestCase):
    def test_canonical_runtime_export_validates_full_interchange_schema(self):
        n=setup_node("NODE-CONFORMANCE")
        assessment=n.evaluate({
            "assessment_id":"ASM-1", "artifact_id":"ART-1", "claim_ids":["CLM-1"],
            "evidence_refs":["EVD-1"], "policy_refs":["POL-1"], "invariant_refs":["INV-1"],
            "scope":"scope:a", "invariant_results":{"INV-1":True}, "created_at":TS,
        })
        decision=n.decide({
            "id":"DEC-1", "assessment_id":assessment["id"], "authority_ref":"AUTH-1",
            "outcome":"APPROVE", "reason_code":"SCHEMA_CONFORMANCE", "scope":"scope:a", "created_at":TS,
        })
        trace=n.create_trace({
            "id":"TRC-1", "artifact_id":"ART-1", "prior_state_ref":"STATE-ART-1", "transform_id":"TRANSFORM-CONFORMANCE",
            "policy_refs":["POL-1"], "authority_ref":"AUTH-1", "invariants_checked":["INV-1"],
            "evidence_refs":["EVD-1"], "validator_refs":[], "assessment_ref":assessment["id"],
            "decision_ref":decision["id"], "reason_code":"SCHEMA_CONFORMANCE", "result_state_ref":"STATE-1",
            "created_at":TS, "continuation_links":[],
        })
        n.make_receipt("TRACE", trace["id"], trace, receipt_id="RCP-TRACE-1")
        Draft202012Validator(SCHEMA, format_checker=FormatChecker()).validate(n.export_bundle())

if __name__ == '__main__': unittest.main()
