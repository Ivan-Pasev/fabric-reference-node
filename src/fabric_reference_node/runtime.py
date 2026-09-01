#!/usr/bin/env python3
"""Persistent local runtime wrapper for ReferenceNode + durable effective-state overlay."""
from __future__ import annotations
from copy import deepcopy
import threading
from pathlib import Path
from typing import Any

from .core import ReferenceNode
from .persistence import ReferenceStore
from .transitions import DurableTransitionStore

class PersistentReferenceRuntime:
    def __init__(self, db_path: str | Path, node_id: str = "NODE-PERSISTENT-LOCAL"):
        self.db_path = str(db_path)
        self.lock = threading.RLock()
        self.store = ReferenceStore(self.db_path)
        try:
            self.node = self.store.load_node(node_id)
        except KeyError:
            self.node = ReferenceNode(node_id)
            self.store.save_node(self.node)
        self.transitions = DurableTransitionStore(self.db_path)

    def persist(self) -> str:
        with self.lock:
            return self.store.save_node(self.node)

    def mutate(self, method_name: str, *args, **kwargs):
        with self.lock:
            before = self.node.export_bundle()
            try:
                out = getattr(self.node, method_name)(*args, **kwargs)
                self.store.save_node(self.node)
                return out
            except Exception:
                self.node = ReferenceNode.from_bundle(before)
                raise

    def state_root(self):
        with self.lock:
            return self.transitions.state_root(self.node)

    def effective_claim_state(self, claim_id: str):
        with self.lock:
            return self.transitions.effective_claim_state(self.node, claim_id)

    def apply_retraction(self, claim_id: str, reason_code: str, defeating_ref: str, expected_state_root: str | None = None):
        with self.lock:
            return self.transitions.apply_retraction(self.node, claim_id, reason_code, defeating_ref, expected_state_root=expected_state_root)

    def rollback_retraction(self, event_id: str, expected_state_root: str | None = None, reason_code: str = "ROLLBACK_REQUESTED"):
        with self.lock:
            return self.transitions.rollback(self.node, event_id, expected_state_root=expected_state_root, reason_code=reason_code)

    def get_transition_event(self, event_id: str):
        with self.lock:
            return self.transitions.get_event(event_id)

    def close(self):
        self.transitions.close()
        self.store.close()
