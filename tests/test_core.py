import unittest
from fabric_reference_node import ContractError
from tests.fixtures import setup_node

class CoreTests(unittest.TestCase):
    def test_happy_path_keeps_machine_and_human_separate(self):
        n=setup_node()
        a=n.evaluate({"assessment_id":"ASM-1","artifact_id":"ART-1","claim_ids":["CLM-1"],"evidence_refs":["EVD-1"],"policy_refs":["POL-1"],"invariant_refs":["INV-1"],"scope":"scope:a","invariant_results":{"INV-1":True}})
        self.assertEqual(a["machine_outcome"],"PASS")
        d=n.decide({"id":"DEC-1","assessment_id":"ASM-1","authority_ref":"AUTH-1","outcome":"RESTRICT","reason_code":"SYNTHETIC_RESTRICTION","scope":"scope:a"})
        self.assertEqual(d["outcome"],"RESTRICT")
        self.assertEqual(a["machine_outcome"],"PASS")

    def test_missing_evidence_holds(self):
        n=setup_node()
        a=n.evaluate({"artifact_id":"ART-1","claim_ids":["CLM-1"],"evidence_refs":[],"policy_refs":["POL-1"],"invariant_refs":["INV-1"],"scope":"scope:a","invariant_results":{"INV-1":True}})
        self.assertEqual(a["machine_outcome"],"HOLD")

    def test_invariant_failure_fails(self):
        n=setup_node()
        a=n.evaluate({"artifact_id":"ART-1","claim_ids":["CLM-1"],"evidence_refs":["EVD-1"],"policy_refs":["POL-1"],"invariant_refs":["INV-1"],"scope":"scope:a","invariant_results":{"INV-1":False}})
        self.assertEqual(a["machine_outcome"],"FAIL")

    def test_authority_scope_mismatch_fails_closed(self):
        n=setup_node()
        a=n.evaluate({"assessment_id":"ASM-1","artifact_id":"ART-1","claim_ids":["CLM-1"],"evidence_refs":["EVD-1"],"policy_refs":["POL-1"],"invariant_refs":["INV-1"],"scope":"scope:a","invariant_results":{"INV-1":True}})
        with self.assertRaises(ContractError):
            n.decide({"assessment_id":a["id"],"authority_ref":"AUTH-1","outcome":"APPROVE","reason_code":"TEST","scope":"scope:b"})

    def test_receipt_rejects_changed_object(self):
        n=setup_node(); obj={"id":"X","value":1}
        r=n.make_receipt("ARTIFACT","X",obj)
        self.assertTrue(n.verify_receipt(r,obj))
        self.assertFalse(n.verify_receipt(r,{"id":"X","value":2}))

    def test_retraction_simulation_is_nonmutating(self):
        n=setup_node(); before=dict(n.claims["CLM-1"])
        n.simulate_retraction("CLM-1","DEFEATED","synthetic://counter")
        self.assertEqual(before,n.claims["CLM-1"])

    def test_missing_required_registry_field_fails_closed(self):
        n=setup_node()
        with self.assertRaises(ContractError):
            n.add_policy({"id":"POL-BROKEN"})

    def test_unexpected_registry_field_fails_closed(self):
        n=setup_node()
        broken={"id":"INV-BROKEN","type":"DOMAIN_SPECIFIC","statement":"x","check_ref":"x","severity":"LOW","hidden":True}
        with self.assertRaises(ContractError):
            n.add_invariant(broken)

if __name__=='__main__': unittest.main()
