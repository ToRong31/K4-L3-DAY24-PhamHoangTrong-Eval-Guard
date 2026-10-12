from __future__ import annotations

"""Setup cache and checkpoint helpers for setup_answers.py.

Provides safe persistent caching of:
1. Enriched chunks (keyed on corpus + config + code fingerprints)
2. Dense index manifest (for verified reuse of existing Qdrant collection)
3. Incremental query answers checkpoint (per-query atomic saves, source order preservation)

Guarantees:
- Atomic file operations to prevent corruptions during interruption
- Strict fingerprint validations forcing rebuild on any mismatch
- Complete 50-row validation before writing final answers_50q.json
- No API keys, credentials, or secrets in manifests or logs
"""

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def get_cache_dir(root_dir: str | None = None) -> str:
    base = root_dir or getattr(config, "ROOT_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    cache_dir = os.path.join(base, ".setup_cache")
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def save_json_atomic(path: str, data: Any) -> None:
    """Write JSON data atomically using a temporary file and os.replace."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp_path = f"{path}.tmp.{os.getpid()}"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        raise


def compute_corpus_fingerprint(data_dir: str | None = None) -> str:
    """Compute sha256 hash of all files in data_dir (sorted by relative path)."""
    dir_path = data_dir or getattr(config, "DATA_DIR", "")
    if not os.path.exists(dir_path):
        return "empty_corpus"
    hasher = hashlib.sha256()
    for root, _, files in sorted(os.walk(dir_path)):
        for fname in sorted(files):
            fpath = os.path.join(root, fname)
            rel = os.path.relpath(fpath, dir_path)
            hasher.update(rel.encode("utf-8"))
            try:
                with open(fpath, "rb") as f:
                    while chunk := f.read(65536):
                        hasher.update(chunk)
            except OSError:
                pass
    return hasher.hexdigest()


def compute_config_fingerprint() -> str:
    """Compute sha256 hash of chunking, embedding, and generation configuration.
    
    CRITICAL: Never includes OPENAI_API_KEY or any credentials!
    """
    settings = {
        "HIERARCHICAL_PARENT_SIZE": getattr(config, "HIERARCHICAL_PARENT_SIZE", 2048),
        "HIERARCHICAL_CHILD_SIZE": getattr(config, "HIERARCHICAL_CHILD_SIZE", 256),
        "SEMANTIC_THRESHOLD": getattr(config, "SEMANTIC_THRESHOLD", 0.85),
        "EMBEDDING_MODEL": getattr(config, "EMBEDDING_MODEL", "BAAI/bge-m3"),
        "EMBEDDING_DIM": getattr(config, "EMBEDDING_DIM", 1024),
        "GENERATION_MODEL": getattr(config, "GENERATION_MODEL", "gpt-4o-mini"),
    }
    payload = json.dumps(settings, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def compute_code_fingerprint(code_files: list[str]) -> str:
    """Compute sha256 hash of implementation files."""
    hasher = hashlib.sha256()
    for fp in sorted(code_files):
        if os.path.exists(fp):
            hasher.update(os.path.basename(fp).encode("utf-8"))
            with open(fp, "rb") as f:
                hasher.update(f.read())
    return hasher.hexdigest()


def compute_test_set_fingerprint(test_set_path: str | None = None) -> str:
    """Compute sha256 hash of test set JSON file."""
    path = test_set_path or getattr(config, "TEST_SET_PATH", "")
    if not os.path.exists(path):
        return "missing_test_set"
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


# ─── Enriched Chunks Cache ───────────────────────────────────────────────────

def get_chunks_cache_path(cache_dir: str) -> str:
    return os.path.join(cache_dir, "enriched_chunks.json")


def load_cached_enriched_chunks(
    cache_dir: str,
    expected_corpus_fp: str,
    expected_config_fp: str,
    expected_code_fp: str,
) -> list[dict] | None:
    """Load cached enriched chunks if manifest matches all fingerprints."""
    path = get_chunks_cache_path(cache_dir)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        manifest = payload.get("manifest", {})
        if (
            manifest.get("corpus_fingerprint") == expected_corpus_fp
            and manifest.get("config_fingerprint") == expected_config_fp
            and manifest.get("code_fingerprint") == expected_code_fp
        ):
            chunks = payload.get("chunks")
            if isinstance(chunks, list) and chunks:
                # Basic validation of chunk shape
                if all(isinstance(c, dict) and "text" in c and "metadata" in c for c in chunks):
                    return chunks
    except Exception:
        pass
    return None


def save_cached_enriched_chunks(
    cache_dir: str,
    chunks: list[dict],
    corpus_fp: str,
    config_fp: str,
    code_fp: str,
) -> None:
    """Persist enriched chunks with their manifest atomically."""
    path = get_chunks_cache_path(cache_dir)
    payload = {
        "manifest": {
            "corpus_fingerprint": corpus_fp,
            "config_fingerprint": config_fp,
            "code_fingerprint": code_fp,
            "chunk_count": len(chunks),
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        "chunks": chunks,
    }
    save_json_atomic(path, payload)


# ─── Dense Index Manifest ────────────────────────────────────────────────────

def get_index_manifest_path(cache_dir: str) -> str:
    return os.path.join(cache_dir, "dense_index_manifest.json")


def load_dense_index_manifest(
    cache_dir: str,
    expected_collection: str,
    expected_model: str,
    expected_dim: int,
    expected_chunks_hash: str,
) -> bool:
    """Check if existing dense index manifest matches all expectations."""
    path = get_index_manifest_path(cache_dir)
    if not os.path.exists(path):
        return False
    try:
        with open(path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        return (
            manifest.get("collection_name") == expected_collection
            and manifest.get("embedding_model") == expected_model
            and manifest.get("embedding_dim") == expected_dim
            and manifest.get("chunks_hash") == expected_chunks_hash
            and manifest.get("status") == "success"
        )
    except Exception:
        return False


def save_dense_index_manifest(
    cache_dir: str,
    collection_name: str,
    embedding_model: str,
    embedding_dim: int,
    chunks_hash: str,
    chunk_count: int,
) -> None:
    """Save dense index manifest indicating successful indexing."""
    path = get_index_manifest_path(cache_dir)
    payload = {
        "collection_name": collection_name,
        "embedding_model": embedding_model,
        "embedding_dim": embedding_dim,
        "chunks_hash": chunks_hash,
        "chunk_count": chunk_count,
        "status": "success",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    save_json_atomic(path, payload)


# ─── Incremental Query Answers Checkpoint ────────────────────────────────────

def get_answers_checkpoint_path(cache_dir: str) -> str:
    return os.path.join(cache_dir, "answers_checkpoint.json")


def load_answers_checkpoint(
    checkpoint_path: str,
    test_set: list[dict],
    expected_test_fp: str,
    expected_model: str,
) -> dict[int, dict]:
    """Load validated answers from checkpoint, mapping question_id -> answer record.
    
    Discards any mismatched, stale, or corrupt records.
    """
    if not os.path.exists(checkpoint_path):
        return {}
    try:
        with open(checkpoint_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        manifest = payload.get("manifest", {})
        if (
            manifest.get("test_set_fingerprint") != expected_test_fp
            or manifest.get("generation_model") != expected_model
        ):
            return {}

        raw_answers = payload.get("answers", {})
        by_test_id = {item["id"]: item for item in test_set}
        valid_answers: dict[int, dict] = {}

        for k, rec in raw_answers.items():
            try:
                qid = int(k)
            except (ValueError, TypeError):
                continue
            if qid not in by_test_id or not isinstance(rec, dict):
                continue
            orig = by_test_id[qid]
            # Validate provenance
            if (
                rec.get("question") == orig["question"]
                and rec.get("distribution") == orig["distribution"]
                and rec.get("ground_truth") == orig["ground_truth"]
                and isinstance(rec.get("answer"), str)
                and rec["answer"].strip()
                and isinstance(rec.get("contexts"), list)
                and rec.get("generation_mode") in ("llm", "extractive_fallback")
            ):
                valid_answers[qid] = rec
        return valid_answers
    except Exception:
        return {}


def save_answers_checkpoint(
    checkpoint_path: str,
    answers_by_id: dict[int, dict],
    test_fp: str,
    model: str,
) -> None:
    """Save answers checkpoint atomically."""
    payload = {
        "manifest": {
            "test_set_fingerprint": test_fp,
            "generation_model": model,
            "completed_count": len(answers_by_id),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
        "answers": {str(qid): rec for qid, rec in answers_by_id.items()},
    }
    save_json_atomic(checkpoint_path, payload)


def validate_final_answers(answers: list[dict], test_set: list[dict]) -> None:
    """Strictly validate final answers list before committing to answers_50q.json.
    
    Must have exact match with test_set IDs, length, and provenance.
    """
    if len(answers) != len(test_set):
        raise ValueError(f"Incomplete answers: expected {len(test_set)} rows, got {len(answers)}.")
    by_test = {item["id"]: item for item in test_set}
    ids = [a.get("id") for a in answers]
    if ids != [item["id"] for item in test_set]:
        raise ValueError("Answers order or IDs do not match original test set sequence.")
    for a in answers:
        qid = a["id"]
        orig = by_test[qid]
        for field in ("question", "distribution", "ground_truth"):
            if a.get(field) != orig[field]:
                raise ValueError(f"Answer {qid}: mismatch in {field}.")
        if not isinstance(a.get("answer"), str) or not a["answer"].strip():
            raise ValueError(f"Answer {qid}: empty or missing answer text.")
        if not isinstance(a.get("contexts"), list):
            raise ValueError(f"Answer {qid}: contexts must be a list.")
        mode = a.get("generation_mode")
        if mode not in ("llm", "extractive_fallback"):
            raise ValueError(f"Answer {qid}: invalid generation_mode '{mode}'.")
        if mode == "llm" and not a.get("generation_model"):
            raise ValueError(f"Answer {qid}: generation_mode='llm' requires generation_model.")
