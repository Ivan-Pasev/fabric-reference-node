import unittest
from fabric_reference_node import ReferenceNode, ContractError

AUTH={"definition":"CLOSED","paper_proof":"NONE","formal_check":"NONE","executable":"NONE","numerical":"NONE","empirical":"NONE","kernel":"INACTIVE"}

def setup_node():
    n=ReferenceNode("NODE-TEST")
    n.add_artifact({"id":"ART-1"})
    n.add_claim({"id":"CLM-1","artifact_id":"ART-1","statement":"x","public_statuses":["AA"],"kind":"DEF","authority":dict(AUTH),"sources":["synthetic://x"],"dependencies":[],"contradictions":[],"lifecycle":"ACTIVE","promotion_receipts":[]})
    n.add_evidence({"id":"EV-1"})
    n.add_policy({"id":"POL-1"})
    n.add_authority({"id":"AUTH-1","status":"ACTIVE","scopes":["scope:a"]})
    n.add_invariant({"id":"INV-1"})
    return n

class CoreTests(unittest.TestCase):
    def test_happy_path_keeps_machine_and_human_separate(self):
        n=setup_node()
        a=n.evaluate({"assessment_id":"ASM-1","artifact_id":"ART-1","claim_ids":["CLM-1"],"evidence_refs":["EV-1"],"policy_refs":["POL-1"],"invariant_refs":["INV-1"],"scope":"scope:a","invariant_results":{"INV-1":True}})
        self.assertEqual(a["machine_outcome"],"PASS")
        d=n.decide({"id":"DEC-1","assessment_id":"ASM-1","authority_ref":"AUTH-1","outcome":"RESTRICT","scope":"scope:a"})
        self.assertEqual(d["outcome"],"RESTRICT")
        self.assertEqual(a["machine_outcome"],"PASS")

    def test_missing_evidence_holds(self):
        n=setup_node()
        a=n.evaluate({"artifact_id":"ART-1","claim_ids":["CLM-1"],"evidence_refs":[],"policy_refs":["POL-1"],"invariant_refs":["INV-1"],"scope":"scope:a","invariant_results":{"INV-1":True}})
        self.assertEqual(a["machine_outcome"],"HOLD")

    def test_invariant_failure_fails(self):
        n=setup_node()
        a=n.evaluate({"artifact_id":"ART-1","claim_ids":["CLM-1"],"evidence_refs":["EV-1"],"policy_refs":["POL-1"],"invariant_refs":["INV-1"],"scope":"scope:a","invariant_results":{"INV-1":False}})
        self.assertEqual(a["machine_outcome"],"FAIL")

    def test_authority_scope_mismatch_fails_closed(self):
        n=setup_node()
        a=n.evaluate({"assessment_id":"ASM-1","artifact_id":"ART-1","claim_ids":["CLM-1"],"evidence_refs":["EV-1"],"policy_refs":["POL-1"],"invariant_refs":["INV-1"],"scope":"scope:a","invariant_results":{"INV-1":True}})
        with self.assertRaises(ContractError):
            n.decide({"assessment_id":a["id"],"authority_ref":"AUTH-1","outcome":"APPROVE","scope":"scope:b"})

    def test_receipt_rejects_changed_object(self):
        n=setup_node(); obj={"id":"X","value":1}
        r=n.make_receipt("ARTIFACT","X",obj)
        self.assertTrue(n.verify_receipt(r,obj))
        self.assertFalse(n.verify_receipt(r,{"id":"X","value":2}))

    def test_retraction_simulation_is_nonmutating(self):
        n=setup_node(); before=dict(n.claims["CLM-1"])
        n.simulate_retraction("CLM-1","DEFEATED","synthetic://counter")
        self.assertEqual(before,n.claims["CLM-1"])

if __name__=='__main__': unittest.main()
