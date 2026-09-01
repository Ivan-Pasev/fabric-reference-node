#!/usr/bin/env python3
"""Lossless SQLite staging and local node persistence.

Raw upstream rows are stored before semantic projection. Staging has zero authority effect.
The source-system identifier is explicit so adapters can preserve provenance without
pretending that external vocabularies are equivalent to local Reference Node types.
"""
from __future__ import annotations
import hashlib
import json
import sqlite3
import threading
from pathlib import Path
from typing import Any, Mapping

from .core import canonical_json, digest, ReferenceNode


def row_hash(row: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json(row).encode("utf-8")).hexdigest()


class ReferenceStore:
    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        self._init()

    def _init(self):
        self.conn.executescript("""
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS source_snapshots(
            snapshot_hash TEXT PRIMARY KEY,
            source_title TEXT NOT NULL,
            source_id TEXT NOT NULL,
            captured_at TEXT NOT NULL,
            manifest_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS source_records(
            source_system TEXT NOT NULL,
            partition_name TEXT NOT NULL,
            source_key TEXT NOT NULL,
            row_hash TEXT NOT NULL,
            row_json TEXT NOT NULL,
            staged_status TEXT NOT NULL,
            authority_effect TEXT NOT NULL,
            PRIMARY KEY(source_system, partition_name, source_key)
        );
        CREATE TABLE IF NOT EXISTS transfer_receipts(
            receipt_hash TEXT PRIMARY KEY,
            source_object_id TEXT NOT NULL,
            target_object_id TEXT,
            mode TEXT NOT NULL,
            verdict TEXT NOT NULL,
            receipt_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS node_snapshots(
            node_id TEXT PRIMARY KEY,
            bundle_hash TEXT NOT NULL,
            bundle_json TEXT NOT NULL
        );
        """)
        self.conn.commit()

    @staticmethod
    def _key_for(partition: str, row: Mapping[str, Any]) -> str:
        preferred = {
            "CLAIMS":"claim_id", "SOURCES":"source_id", "DOCUMENTS":"document_id",
            "DERIVATIONS":"derivation_id", "EXPERIMENTS":"experiment_id",
            "OPEN_DEBTS":"debt_id", "RELEASES":"release_id"
        }
        key = row.get(preferred[partition])
        if not key:
            raise ValueError(f"{partition}: missing primary source key")
        return str(key)

    def stage_snapshot(self, snapshot: Mapping[str, Any], source_system: str = "UPSTREAM", captured_at: str | None = None) -> dict[str, Any]:
        snapshot_hash = digest(snapshot)
        counts = {}
        source = snapshot["source"]
        captured_at = captured_at or source.get("captured_at") or "UNSPECIFIED"
        for partition, rows in snapshot["sheets"].items():
            counts[partition] = len(rows)
            for row in rows:
                key = self._key_for(partition, row)
                rh = row_hash(row)
                self.conn.execute(
                    """INSERT INTO source_records(source_system,partition_name,source_key,row_hash,row_json,staged_status,authority_effect)
                       VALUES(?,?,?,?,?,?,?)
                       ON CONFLICT(source_system,partition_name,source_key) DO UPDATE SET
                         row_hash=excluded.row_hash,row_json=excluded.row_json,staged_status=excluded.staged_status,authority_effect=excluded.authority_effect""",
                    (source_system, partition, key, rh, canonical_json(row), "STAGED_RAW", "NONE")
                )
        manifest = {"snapshot_hash": snapshot_hash, "counts": counts, "total_records": sum(counts.values())}
        self.conn.execute(
            """INSERT OR REPLACE INTO source_snapshots(snapshot_hash,source_title,source_id,captured_at,manifest_json)
               VALUES(?,?,?,?,?)""",
            (snapshot_hash, source.get("title",""), source.get("spreadsheet_id",""), captured_at, canonical_json(manifest))
        )
        self.conn.commit()
        return manifest

    def get_record(self, partition: str, source_key: str, source_system: str = "UPSTREAM") -> dict[str, Any]:
        row = self.conn.execute(
            "SELECT * FROM source_records WHERE source_system=? AND partition_name=? AND source_key=?",
            (source_system, partition, source_key)
        ).fetchone()
        if row is None:
            raise KeyError((partition, source_key))
        return {**dict(row), "row": json.loads(row["row_json"])}

    def counts(self) -> dict[str, int]:
        rows = self.conn.execute(
            "SELECT partition_name, COUNT(*) n FROM source_records GROUP BY partition_name ORDER BY partition_name"
        ).fetchall()
        return {r["partition_name"]: r["n"] for r in rows}

    def preview_claim(self, claim_id: str, source_system: str = "UPSTREAM") -> dict[str, Any]:
        record = self.get_record("CLAIMS", claim_id, source_system=source_system)
        return {
            "source_system": source_system,
            "source_partition": "CLAIMS",
            "source_object_id": claim_id,
            "source_row_hash": record["row_hash"],
            "source_authority_raw": record["row"].get("authority"),
            "source_status_raw": record["row"].get("status"),
            "verdict": "HOLD_CROSSWALK_REQUIRED",
            "reason": "UPSTREAM_DOMAIN_VOCABULARY_NOT_COERCED_INTO_REFERENCE_NODE_CLAIM_ENUMS",
            "authority_effect": "NONE"
        }

    def put_transfer_receipt(self, receipt: Mapping[str, Any]) -> str:
        rh = digest(receipt)
        self.conn.execute(
            "INSERT OR REPLACE INTO transfer_receipts(receipt_hash,source_object_id,target_object_id,mode,verdict,receipt_json) VALUES(?,?,?,?,?,?)",
            (rh, receipt.get("source_object_id",""), receipt.get("proposed_target",{}).get("claim_id"), receipt.get("mode",""), receipt.get("verdict",""), canonical_json(receipt))
        )
        self.conn.commit()
        return rh

    def save_node(self, node: ReferenceNode) -> str:
        with self._lock:
            bundle = node.export_bundle()
            bh = digest(bundle)
            self.conn.execute(
                "INSERT OR REPLACE INTO node_snapshots(node_id,bundle_hash,bundle_json) VALUES(?,?,?)",
                (node.node_id, bh, canonical_json(bundle))
            )
            self.conn.commit()
            return bh

    def load_node(self, node_id: str) -> ReferenceNode:
        with self._lock:
            row = self.conn.execute("SELECT bundle_json FROM node_snapshots WHERE node_id=?", (node_id,)).fetchone()
            if row is None:
                raise KeyError(node_id)
            return ReferenceNode.from_bundle(json.loads(row["bundle_json"]))

    def close(self):
        self.conn.close()


# Backwards-compatible local alias used by the original R1 working package.
EvidenceRouterStore = ReferenceStore
