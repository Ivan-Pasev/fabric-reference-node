#!/usr/bin/env python3
"""Persistent HTTP transport candidate for the DFT 2.0 Reference Node v0.3.

Adds local SQLite-backed node persistence and durable event-sourced retraction/rollback
semantics without changing the immutable base Claim objects.
"""
from __future__ import annotations
import json
import pathlib
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from .core import ContractError
from .transitions import TransitionError, TransitionConflict
from .runtime import PersistentReferenceRuntime


def json_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


class PersistentReferenceNodeHTTPHandler(BaseHTTPRequestHandler):
    runtime: PersistentReferenceRuntime | None = None
    server_version = "FabricReferenceNode/0.1"

    def log_message(self, fmt, *args):
        return

    @property
    def rt(self) -> PersistentReferenceRuntime:
        if self.runtime is None:
            raise RuntimeError("runtime not bound")
        return self.runtime

    def _send(self, status, value):
        blob = json_bytes(value)
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(blob)))
        self.end_headers()
        self.wfile.write(blob)

    def _body(self):
        n = int(self.headers.get("Content-Length", "0"))
        if n == 0:
            return {}
        return json.loads(self.rfile.read(n).decode("utf-8"))

    def _error(self, exc):
        if isinstance(exc, KeyError):
            code = 404
        elif isinstance(exc, (ContractError, TransitionError, TransitionConflict)):
            code = 409
        else:
            code = 400
        self._send(code, {"status":"HOLD", "error":type(exc).__name__, "reason":str(exc)})

    def do_GET(self):
        try:
            path = urlparse(self.path).path
            if path == "/v1/capabilities":
                caps = self.rt.node.capabilities()
                caps.update({
                    "transport_version":"0.3.0",
                    "persistence":"SQLITE_LOCAL_CANDIDATE",
                    "retraction_model":"IMMUTABLE_BASE_PLUS_EFFECTIVE_STATE_OVERLAY",
                    "rollback":"SUPPORTED_BOUNDED_LOCAL",
                })
                return self._send(200, caps)
            if path == "/v1/schemas":
                return self._send(200, {
                    "reference_node":"1.0.0", "transport":"0.3.0", "openapi":"3.1.0",
                    "transition_contract":"0.3.0", "transfer_governance":"0.3.0"
                })
            if path == "/v1/health":
                root = self.rt.state_root()
                return self._send(200, {
                    "status":"PASS", "node_id":self.rt.node.node_id,
                    "maturity":"LOCAL_PERSISTENT_HTTP_REFERENCE_CANDIDATE",
                    "state_root":root["state_root"], "active_overlay_count":root["active_overlay_count"]
                })
            if path == "/v1/state/root":
                return self._send(200, self.rt.state_root())
            m = re.fullmatch(r"/v1/claims/([^/]+)/effective-state", path)
            if m:
                return self._send(200, self.rt.effective_claim_state(m.group(1)))
            m = re.fullmatch(r"/v1/claims/([^/]+)", path)
            if m:
                cid=m.group(1)
                if cid not in self.rt.node.claims: raise KeyError(cid)
                return self._send(200, self.rt.node.claims[cid])
            m = re.fullmatch(r"/v1/claims/([^/]+)/dependencies", path)
            if m:
                return self._send(200, self.rt.node.dependency_closure(m.group(1)))
            m = re.fullmatch(r"/v1/claims/([^/]+)/impact", path)
            if m:
                cid=m.group(1)
                closure=self.rt.node.dependency_closure(cid)
                return self._send(200, {
                    "claim_id":cid, **closure,
                    "contradictions":self.rt.node.claims[cid].get("contradictions",[]),
                    "effective_state":self.rt.effective_claim_state(cid)
                })
            m = re.fullmatch(r"/v1/retractions/([^/]+)", path)
            if m:
                return self._send(200, self.rt.get_transition_event(m.group(1)))
            m = re.fullmatch(r"/v1/traces/([^/]+)", path)
            if m:
                tid=m.group(1)
                if tid not in self.rt.node.traces: raise KeyError(tid)
                return self._send(200, self.rt.node.traces[tid])
            m = re.fullmatch(r"/v1/receipts/([^/]+)/verify", path)
            if m:
                rid=m.group(1)
                receipt=self.rt.node.receipts.get(rid)
                if not receipt: raise KeyError(rid)
                stores={"ARTIFACT":self.rt.node.artifacts,"CLAIM":self.rt.node.claims,"EVIDENCE":self.rt.node.evidence,
                        "ASSESSMENT":self.rt.node.assessments,"DECISION":self.rt.node.decisions,"TRACE":self.rt.node.traces}
                obj=stores.get(receipt["object_type"],{}).get(receipt["object_id"])
                if obj is None:
                    return self._send(200,{"receipt_id":rid,"verified":False,"reason":"BOUND_OBJECT_NOT_PRESENT"})
                return self._send(200,{"receipt_id":rid,"verified":self.rt.node.verify_receipt(receipt,obj)})
            m = re.fullmatch(r"/v1/continuations/([^/]+)", path)
            if m:
                oid=m.group(1)
                links=[x for x in self.rt.node.continuations.values() if x["source_ref"]==oid or x["target_ref"]==oid]
                return self._send(200,{"object_id":oid,"links":links})
            return self._send(404,{"status":"HOLD","reason":"UNKNOWN_ROUTE"})
        except Exception as exc:
            self._error(exc)

    def do_POST(self):
        try:
            path=urlparse(self.path).path
            body=self._body()
            if path == "/v1/artifacts": return self._send(200,self.rt.mutate("add_artifact",body))
            if path == "/v1/claims": return self._send(200,self.rt.mutate("add_claim",body))
            if path == "/v1/evidence": return self._send(200,self.rt.mutate("add_evidence",body))
            if path == "/v1/policies": return self._send(200,self.rt.mutate("add_policy",body))
            if path == "/v1/authorities": return self._send(200,self.rt.mutate("add_authority",body))
            if path == "/v1/invariants": return self._send(200,self.rt.mutate("add_invariant",body))
            if path == "/v1/workflows/evaluate": return self._send(200,self.rt.mutate("evaluate",body))
            if path == "/v1/decisions": return self._send(200,self.rt.mutate("decide",body))
            if path == "/v1/traces": return self._send(200,self.rt.mutate("create_trace",body))
            if path == "/v1/retractions/simulate":
                return self._send(200,self.rt.node.simulate_retraction(body["claim_id"],body["reason_code"],body["defeating_ref"]))
            if path == "/v1/retractions/apply":
                return self._send(200,self.rt.apply_retraction(
                    body["claim_id"],body["reason_code"],body["defeating_ref"],body.get("expected_state_root")
                ))
            m = re.fullmatch(r"/v1/retractions/([^/]+)/rollback", path)
            if m:
                return self._send(200,self.rt.rollback_retraction(
                    m.group(1),body.get("expected_state_root"),body.get("reason_code","ROLLBACK_REQUESTED")
                ))
            return self._send(404,{"status":"HOLD","reason":"UNKNOWN_ROUTE"})
        except Exception as exc:
            self._error(exc)


def make_server(runtime: PersistentReferenceRuntime, host="127.0.0.1", port=0):
    handler = type("BoundPersistentReferenceNodeHTTPHandler", (PersistentReferenceNodeHTTPHandler,), {"runtime": runtime})
    return ThreadingHTTPServer((host, port), handler)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fabric Reference Node local HTTP server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--db", default="./fabric-reference-node.sqlite")
    parser.add_argument("--node-id", default="NODE-LOCAL")
    args = parser.parse_args()
    rt=PersistentReferenceRuntime(args.db, args.node_id)
    server=make_server(rt, host=args.host, port=args.port)
    print(f"Fabric Reference Node listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    finally:
        rt.close()

if __name__ == "__main__":
    main()
