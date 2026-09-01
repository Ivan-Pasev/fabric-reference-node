import pathlib, tempfile, unittest
from fabric_reference_node import PersistentReferenceRuntime

class PersistenceTests(unittest.TestCase):
    def test_node_snapshot_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            db=pathlib.Path(td)/"node.sqlite"
            rt=PersistentReferenceRuntime(db,"N")
            rt.node.add_artifact({"id":"ART-1"}); rt.persist(); rt.close()
            rt2=PersistentReferenceRuntime(db,"N")
            self.assertIn("ART-1",rt2.node.artifacts)
            rt2.close()

if __name__=='__main__': unittest.main()
