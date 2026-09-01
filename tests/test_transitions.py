import pathlib, tempfile, unittest
from fabric_reference_node import ReferenceNode, DurableTransitionStore, TransitionConflict, digest

AUTH={"definition":"CLOSED","paper_proof":"NONE","formal_check":"NONE","executable":"NONE","numerical":"NONE","empirical":"NONE","kernel":"INACTIVE"}

def claim(cid,deps=None,contr=None):
    return {"id":cid,"artifact_id":"ART","statement":cid,"public_statuses":["AA"],"kind":"DEF","authority":dict(AUTH),"sources":["synthetic://x"],"dependencies":list(deps or []),"contradictions":list(contr or []),"lifecycle":"ACTIVE","promotion_receipts":[]}

def node():
    n=ReferenceNode("NODE-TX")
    n.add_claim(claim("A")); n.add_claim(claim("B",["A"])); n.add_claim(claim("C",contr=["A"])); n.add_claim(claim("D",["B"]))
    return n

class TransitionTests(unittest.TestCase):
    def test_dependency_only_retraction_and_append_only_rollback(self):
        with tempfile.TemporaryDirectory() as td:
            n=node(); base=digest(n.claims); s=DurableTransitionStore(pathlib.Path(td)/"s.sqlite")
            r0=s.state_root(n)
            ev=s.apply_retraction(n,"A","DEFEATED","synthetic://counter",expected_state_root=r0["state_root"])
            self.assertEqual(s.effective_claim_state(n,"A")["effective_state"],"RETRACTED")
            self.assertEqual(s.effective_claim_state(n,"D")["effective_state"],"SUSPENDED_BY_DEPENDENCY")
            self.assertEqual(s.effective_claim_state(n,"C")["effective_state"],"ACTIVE")
            r1=s.state_root(n)
            s.rollback(n,ev["event_id"],expected_state_root=r1["state_root"])
            r2=s.state_root(n)
            self.assertEqual(r2["effective_state_root"],r0["effective_state_root"])
            self.assertNotEqual(r2["history_root"],r0["history_root"])
            self.assertEqual(base,digest(n.claims))
            s.close()

    def test_stale_state_root_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            n=node(); s=DurableTransitionStore(pathlib.Path(td)/"s.sqlite")
            with self.assertRaises(TransitionConflict):
                s.apply_retraction(n,"A","DEFEATED","x",expected_state_root="0"*64)
            self.assertEqual(s.state_root(n)["active_overlay_count"],0)
            s.close()

if __name__=='__main__': unittest.main()
