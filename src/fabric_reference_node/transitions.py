#!/usr/bin/env python3
"""Durable event-sourced effective-state overlay for Reference Node retractions.

Canonical design:
- base Claim objects are immutable;
- retraction changes only an effective governance-state overlay;
- propagation follows declared dependency edges only;
- transition history is append-hash-chained and is never erased by rollback;
- rollback can restore the predecessor *effective* root while the full state/audit root
  continues forward because history has advanced;
- stale composite state roots and overlapping active overlays fail closed.

Bounded local executable semantics only; not production transaction/security evidence.
"""
from __future__ import annotations
from contextlib import contextmanager
import json
import sqlite3
import threading
from pathlib import Path
from typing import Any

from .core import ReferenceNode, canonical_json, digest, utc_now

GENESIS_HISTORY_ROOT = digest({"journal":"DFT-R1D-TRANSITION","version":"0.3.0","events":[]})

class TransitionError(ValueError): pass
class TransitionConflict(TransitionError): pass

class DurableTransitionStore:
    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        self._init()

    def _init(self):
        with self.conn:
            self.conn.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS transition_events(
                event_id TEXT PRIMARY KEY,
                node_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                parent_event_id TEXT,
                target_claim_id TEXT NOT NULL,
                reason_code TEXT NOT NULL,
                defeating_ref TEXT NOT NULL,
                node_bundle_hash TEXT NOT NULL,
                before_state_root TEXT NOT NULL,
                after_state_root TEXT NOT NULL,
                event_status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                receipt_json TEXT NOT NULL,
                event_hash TEXT,
                before_history_root TEXT,
                after_history_root TEXT,
                before_effective_state_root TEXT,
                after_effective_state_root TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_transition_parent ON transition_events(parent_event_id);
            CREATE TABLE IF NOT EXISTS transition_items(
                event_id TEXT NOT NULL,
                claim_id TEXT NOT NULL,
                role TEXT NOT NULL,
                before_state TEXT NOT NULL,
                after_state TEXT NOT NULL,
                PRIMARY KEY(event_id, claim_id)
            );
            CREATE TABLE IF NOT EXISTS claim_state_overlays(
                node_id TEXT NOT NULL,
                claim_id TEXT NOT NULL,
                effective_state TEXT NOT NULL,
                source_event_id TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY(node_id, claim_id)
            );
            """)
        cols={r["name"] for r in self.conn.execute("PRAGMA table_info(transition_events)").fetchall()}
        for name in ["event_hash","before_history_root","after_history_root","before_effective_state_root","after_effective_state_root"]:
            if name not in cols:
                with self.conn:
                    self.conn.execute(f"ALTER TABLE transition_events ADD COLUMN {name} TEXT")

    @contextmanager
    def _tx(self):
        with self._lock:
            try:
                self.conn.execute("BEGIN IMMEDIATE")
                yield
                self.conn.commit()
            except Exception:
                self.conn.rollback(); raise

    def _base_state(self, node: ReferenceNode, claim_id: str) -> str:
        if claim_id not in node.claims: raise TransitionError(f"unknown claim: {claim_id}")
        return str(node.claims[claim_id].get("lifecycle", "HOLD"))

    def _overlay_row(self, node_id: str, claim_id: str):
        return self.conn.execute("SELECT * FROM claim_state_overlays WHERE node_id=? AND claim_id=?",(node_id,claim_id)).fetchone()

    def effective_claim_state(self, node: ReferenceNode, claim_id: str) -> dict[str, Any]:
        base=self._base_state(node,claim_id); row=self._overlay_row(node.node_id,claim_id)
        return {"node_id":node.node_id,"claim_id":claim_id,"base_lifecycle":base,
                "effective_state":row["effective_state"] if row else base,"overlay_active":bool(row),
                "source_event_id":row["source_event_id"] if row else None}

    def overlay_manifest(self, node: ReferenceNode) -> list[dict[str,str]]:
        rows=self.conn.execute("SELECT claim_id,effective_state,source_event_id FROM claim_state_overlays WHERE node_id=? ORDER BY claim_id",(node.node_id,)).fetchall()
        return [dict(r) for r in rows]

    def history_root(self, node_id: str) -> str:
        row=self.conn.execute("SELECT after_history_root FROM transition_events WHERE node_id=? AND after_history_root IS NOT NULL ORDER BY rowid DESC LIMIT 1",(node_id,)).fetchone()
        return row["after_history_root"] if row else GENESIS_HISTORY_ROOT

    def state_root(self, node: ReferenceNode) -> dict[str, Any]:
        node_hash=digest(node.export_bundle()); overlay=self.overlay_manifest(node); overlay_hash=digest(overlay)
        effective_root=digest({"node_bundle_hash":node_hash,"overlay_hash":overlay_hash})
        hist=self.history_root(node.node_id)
        composite=digest({"effective_state_root":effective_root,"history_root":hist})
        return {"node_id":node.node_id,"node_bundle_hash":node_hash,"overlay_hash":overlay_hash,
                "effective_state_root":effective_root,"history_root":hist,"state_root":composite,
                "active_overlay_count":len(overlay)}

    def get_event(self,event_id:str)->dict[str,Any]:
        row=self.conn.execute("SELECT * FROM transition_events WHERE event_id=?",(event_id,)).fetchone()
        if row is None: raise KeyError(event_id)
        items=self.conn.execute("SELECT claim_id,role,before_state,after_state FROM transition_items WHERE event_id=? ORDER BY claim_id",(event_id,)).fetchall()
        out=dict(row); out["receipt"]=json.loads(out.pop("receipt_json")); out["transitions"]=[dict(x) for x in items]; return out

    def _same_active_retraction(self,node,claim_id,reason_code,defeating_ref):
        row=self._overlay_row(node.node_id,claim_id)
        if not row:return None
        ev=self.conn.execute("SELECT * FROM transition_events WHERE event_id=?",(row["source_event_id"],)).fetchone()
        if ev and ev["event_type"]=="RETRACTION" and ev["event_status"]=="ACTIVE" and ev["target_claim_id"]==claim_id and ev["reason_code"]==reason_code and ev["defeating_ref"]==defeating_ref:
            return self.get_event(ev["event_id"])
        return None

    def apply_retraction(self,node:ReferenceNode,claim_id:str,reason_code:str,defeating_ref:str,*,expected_state_root:str|None=None,created_at:str|None=None)->dict[str,Any]:
        if not reason_code or not defeating_ref: raise TransitionError("reason_code and defeating_ref are required")
        self._base_state(node,claim_id)
        existing=self._same_active_retraction(node,claim_id,reason_code,defeating_ref)
        if existing: existing["idempotent_replay"]=True; return existing
        current=self.state_root(node)
        if expected_state_root is not None and expected_state_root!=current["state_root"]: raise TransitionConflict("expected_state_root mismatch")
        downstream=node.dependency_closure(claim_id)["downstream"]; affected=[claim_id]+downstream
        conflicts=[]
        for cid in affected:
            row=self._overlay_row(node.node_id,cid)
            if row: conflicts.append({"claim_id":cid,"source_event_id":row["source_event_id"],"effective_state":row["effective_state"]})
        if conflicts: raise TransitionConflict("active overlay conflict: "+canonical_json(conflicts))
        transitions=[]
        for cid in affected:
            transitions.append({"claim_id":cid,"role":"TARGET" if cid==claim_id else "DEPENDENT",
                                "before_state":self._base_state(node,cid),
                                "after_state":"RETRACTED" if cid==claim_id else "SUSPENDED_BY_DEPENDENCY"})
        now=created_at or utc_now()
        seed={"node_id":node.node_id,"event_type":"RETRACTION","target_claim_id":claim_id,"reason_code":reason_code,
              "defeating_ref":defeating_ref,"node_bundle_hash":current["node_bundle_hash"],
              "before_state_root":current["state_root"],"before_history_root":current["history_root"],"transitions":transitions}
        event_hash=digest(seed); event_id="RTX-"+event_hash[:20].upper(); after_history=digest({"previous":current["history_root"],"event_hash":event_hash})
        with self._tx():
            for cid in affected:
                if self._overlay_row(node.node_id,cid): raise TransitionConflict(f"active overlay conflict during commit: {cid}")
            for t in transitions:
                self.conn.execute("INSERT INTO claim_state_overlays(node_id,claim_id,effective_state,source_event_id,updated_at) VALUES(?,?,?,?,?)",(node.node_id,t["claim_id"],t["after_state"],event_id,now))
            node_hash=digest(node.export_bundle()); overlay_hash=digest(self.overlay_manifest(node)); post_eff=digest({"node_bundle_hash":node_hash,"overlay_hash":overlay_hash})
            post_state=digest({"effective_state_root":post_eff,"history_root":after_history})
            receipt={"contract_version":"0.3.0","event_id":event_id,"event_type":"RETRACTION","event_hash":event_hash,
                     "node_id":node.node_id,"target_claim_id":claim_id,"reason_code":reason_code,"defeating_ref":defeating_ref,
                     "transitions":transitions,"node_bundle_hash":current["node_bundle_hash"],
                     "before_effective_state_root":current["effective_state_root"],"after_effective_state_root":post_eff,
                     "before_history_root":current["history_root"],"after_history_root":after_history,
                     "before_state_root":current["state_root"],"after_state_root":post_state,
                     "base_claims_mutated":False,"history_preserved":True,"dependency_only_propagation":True,
                     "contradictions_propagated":False,"rollback_supported":True,"authority_effect":"EFFECTIVE_GOVERNANCE_STATE_ONLY",
                     "non_implications":["NO_DELETION_OF_CANONICAL_CLAIM","NO_SCIENTIFIC_TRUTH_DETERMINATION","NO_FORMAL_PROOF_DETERMINATION","NO_INSTITUTIONAL_DECISION_CREATED"],"created_at":now}
            self.conn.execute("INSERT INTO transition_events(event_id,node_id,event_type,parent_event_id,target_claim_id,reason_code,defeating_ref,node_bundle_hash,before_state_root,after_state_root,event_status,created_at,receipt_json,event_hash,before_history_root,after_history_root,before_effective_state_root,after_effective_state_root) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                              (event_id,node.node_id,"RETRACTION",None,claim_id,reason_code,defeating_ref,current["node_bundle_hash"],current["state_root"],post_state,"ACTIVE",now,canonical_json(receipt),event_hash,current["history_root"],after_history,current["effective_state_root"],post_eff))
            for t in transitions:self.conn.execute("INSERT INTO transition_items(event_id,claim_id,role,before_state,after_state) VALUES(?,?,?,?,?)",(event_id,t["claim_id"],t["role"],t["before_state"],t["after_state"]))
        return self.get_event(event_id)

    def rollback(self,node:ReferenceNode,event_id:str,*,expected_state_root:str|None=None,reason_code:str="ROLLBACK_REQUESTED",created_at:str|None=None)->dict[str,Any]:
        original=self.get_event(event_id)
        if original["event_type"]!="RETRACTION":raise TransitionError("only RETRACTION events are rollback targets")
        if original["event_status"]=="ROLLED_BACK":
            row=self.conn.execute("SELECT event_id FROM transition_events WHERE parent_event_id=? AND event_type='ROLLBACK' ORDER BY rowid DESC LIMIT 1",(event_id,)).fetchone()
            if row: out=self.get_event(row["event_id"]);out["idempotent_replay"]=True;return out
            raise TransitionConflict("event already rolled back")
        if original["event_status"]!="ACTIVE":raise TransitionConflict(f"event not active: {original['event_status']}")
        current=self.state_root(node)
        if expected_state_root is not None and expected_state_root!=current["state_root"]:raise TransitionConflict("expected_state_root mismatch")
        for t in original["transitions"]:
            row=self._overlay_row(node.node_id,t["claim_id"])
            if not row or row["source_event_id"]!=event_id or row["effective_state"]!=t["after_state"]:raise TransitionConflict(f"rollback conflict on {t['claim_id']}")
        now=created_at or utc_now(); rtrans=[{"claim_id":t["claim_id"],"role":t["role"],"before_state":t["after_state"],"after_state":t["before_state"]} for t in original["transitions"]]
        seed={"node_id":node.node_id,"event_type":"ROLLBACK","parent_event_id":event_id,"target_claim_id":original["target_claim_id"],
              "reason_code":reason_code,"defeating_ref":original["defeating_ref"],"node_bundle_hash":current["node_bundle_hash"],
              "before_state_root":current["state_root"],"before_history_root":current["history_root"],"transitions":rtrans}
        event_hash=digest(seed); rollback_id="RBK-"+event_hash[:20].upper(); after_history=digest({"previous":current["history_root"],"event_hash":event_hash})
        with self._tx():
            for t in original["transitions"]:
                row=self._overlay_row(node.node_id,t["claim_id"])
                if not row or row["source_event_id"]!=event_id:raise TransitionConflict(f"rollback conflict during commit on {t['claim_id']}")
            for t in original["transitions"]:self.conn.execute("DELETE FROM claim_state_overlays WHERE node_id=? AND claim_id=?",(node.node_id,t["claim_id"]))
            node_hash=digest(node.export_bundle()); overlay_hash=digest(self.overlay_manifest(node)); post_eff=digest({"node_bundle_hash":node_hash,"overlay_hash":overlay_hash}); post_state=digest({"effective_state_root":post_eff,"history_root":after_history})
            receipt={"contract_version":"0.3.0","event_id":rollback_id,"event_type":"ROLLBACK","event_hash":event_hash,"parent_event_id":event_id,
                     "node_id":node.node_id,"target_claim_id":original["target_claim_id"],"reason_code":reason_code,"defeating_ref":original["defeating_ref"],
                     "transitions":rtrans,"node_bundle_hash":current["node_bundle_hash"],
                     "before_effective_state_root":current["effective_state_root"],"after_effective_state_root":post_eff,
                     "before_history_root":current["history_root"],"after_history_root":after_history,
                     "before_state_root":current["state_root"],"after_state_root":post_state,"base_claims_mutated":False,"history_preserved":True,
                     "restored_predecessor_effective_states":True,"authority_effect":"EFFECTIVE_GOVERNANCE_STATE_ONLY","created_at":now}
            self.conn.execute("INSERT INTO transition_events(event_id,node_id,event_type,parent_event_id,target_claim_id,reason_code,defeating_ref,node_bundle_hash,before_state_root,after_state_root,event_status,created_at,receipt_json,event_hash,before_history_root,after_history_root,before_effective_state_root,after_effective_state_root) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                              (rollback_id,node.node_id,"ROLLBACK",event_id,original["target_claim_id"],reason_code,original["defeating_ref"],current["node_bundle_hash"],current["state_root"],post_state,"APPLIED",now,canonical_json(receipt),event_hash,current["history_root"],after_history,current["effective_state_root"],post_eff))
            for t in rtrans:self.conn.execute("INSERT INTO transition_items(event_id,claim_id,role,before_state,after_state) VALUES(?,?,?,?,?)",(rollback_id,t["claim_id"],t["role"],t["before_state"],t["after_state"]))
            self.conn.execute("UPDATE transition_events SET event_status='ROLLED_BACK' WHERE event_id=?",(event_id,))
        return self.get_event(rollback_id)

    def close(self):self.conn.close()
