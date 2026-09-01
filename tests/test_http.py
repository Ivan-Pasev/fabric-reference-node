import json, pathlib, tempfile, threading, time, unittest
from urllib.request import urlopen, Request
from fabric_reference_node import PersistentReferenceRuntime
from fabric_reference_node.http import make_server

class HTTPTests(unittest.TestCase):
    def test_health(self):
        with tempfile.TemporaryDirectory() as td:
            rt=PersistentReferenceRuntime(pathlib.Path(td)/"n.sqlite","HTTP")
            srv=make_server(rt,port=0); t=threading.Thread(target=srv.serve_forever,daemon=True); t.start()
            try:
                host,port=srv.server_address
                with urlopen(f"http://{host}:{port}/v1/health",timeout=2) as r:
                    data=json.loads(r.read())
                self.assertEqual(data["status"],"PASS")
            finally:
                srv.shutdown(); srv.server_close(); rt.close(); t.join(timeout=2)

if __name__=='__main__': unittest.main()
