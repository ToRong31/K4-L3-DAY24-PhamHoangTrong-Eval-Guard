"""Offline unit tests for setup cache and checkpoint resume mechanism.

Tests verify:
1. Atomic file writes and absence of leftover temporary files.
2. Enriched chunks caching, exact match reuse, and stale/mismatched fingerprint invalidation.
3. Corrupt cache JSON handling (graceful fallback without crashes).
4. Dense index manifest matching and collection reuse verification.
5. Incremental query checkpointing, resume of missing items, and provenance checks.
6. Protection of final answers file: never replaces answers_50q.json with partial results.
"""

import json
import os
import pytest

from src.setup_cache import (
    save_json_atomic,
    load_cached_enriched_chunks,
    save_cached_enriched_chunks,
    load_dense_index_manifest,
    save_dense_index_manifest,
    load_answers_checkpoint,
    save_answers_checkpoint,
    validate_final_answers,
    compute_corpus_fingerprint,
    compute_config_fingerprint,
    compute_code_fingerprint,
)


@pytest.fixture
def fake_test_set():
    return [
        {
            "id": i + 1,
            "distribution": "factual" if i < 20 else ("multi_hop" if i < 40 else "adversarial"),
            "question": f"Question {i + 1}?",
            "ground_truth": f"Ground truth {i + 1}.",
        }
        for i in range(50)
    ]


def test_atomic_write_and_replace(tmp_path):
    target = str(tmp_path / "test_data.json")
    payload = {"status": "ok", "items": [1, 2, 3]}
    save_json_atomic(target, payload)

    assert os.path.exists(target)
    with open(target, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded == payload

    # Ensure no temporary files remained
    files = os.listdir(str(tmp_path))
    assert files == ["test_data.json"]


def test_enriched_chunks_cache_and_resume(tmp_path):
    cache_dir = str(tmp_path / "cache")
    chunks = [
        {"text": "Chunk 1", "metadata": {"source": "doc1.md", "parent_id": "p1"}},
        {"text": "Chunk 2", "metadata": {"source": "doc2.md", "parent_id": "p2"}},
    ]
    corpus_fp = "corpus_hash_v1"
    config_fp = "config_hash_v1"
    code_fp = "code_hash_v1"

    save_cached_enriched_chunks(cache_dir, chunks, corpus_fp, config_fp, code_fp)

    # 1. Matching fingerprints -> successful reuse
    loaded = load_cached_enriched_chunks(cache_dir, corpus_fp, config_fp, code_fp)
    assert loaded == chunks

    # 2. Stale corpus fingerprint -> returns None (forces re-enrichment)
    assert load_cached_enriched_chunks(cache_dir, "corpus_hash_v2", config_fp, code_fp) is None

    # 3. Changed model/config -> returns None
    assert load_cached_enriched_chunks(cache_dir, corpus_fp, "config_hash_v2", code_fp) is None

    # 4. Changed code -> returns None
    assert load_cached_enriched_chunks(cache_dir, corpus_fp, config_fp, "code_hash_v2") is None


def test_corrupt_chunks_cache_handling(tmp_path):
    cache_dir = str(tmp_path / "cache")
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = os.path.join(cache_dir, "enriched_chunks.json")
    with open(cache_file, "w", encoding="utf-8") as f:
        f.write("{corrupt json content...")

    # Should not crash; gracefully returns None
    assert load_cached_enriched_chunks(cache_dir, "fp1", "fp2", "fp3") is None


def test_dense_index_manifest(tmp_path):
    cache_dir = str(tmp_path / "cache")
    collection = "lab24_production"
    model = "BAAI/bge-m3"
    dim = 1024
    chunks_hash = "abc123hash"

    save_dense_index_manifest(cache_dir, collection, model, dim, chunks_hash, chunk_count=100)

    # Matching manifest -> True
    assert load_dense_index_manifest(cache_dir, collection, model, dim, chunks_hash) is True

    # Mismatched chunk hash (chunks modified) -> False
    assert load_dense_index_manifest(cache_dir, collection, model, dim, "different_hash") is False

    # Mismatched model/dim -> False
    assert load_dense_index_manifest(cache_dir, collection, "different_model", dim, chunks_hash) is False


def test_answers_checkpoint_incremental_resume(tmp_path, fake_test_set):
    checkpoint_file = str(tmp_path / "checkpoint.json")
    test_fp = "test_fp_v1"
    model = "gpt-4o-mini"

    # Simulate checkpoint with first 2 answers completed
    partial_answers = {
        1: {
            "id": 1,
            "distribution": fake_test_set[0]["distribution"],
            "question": fake_test_set[0]["question"],
            "answer": "Answer 1",
            "contexts": ["Context 1"],
            "ground_truth": fake_test_set[0]["ground_truth"],
            "generation_mode": "llm",
            "generation_model": model,
        },
        2: {
            "id": 2,
            "distribution": fake_test_set[1]["distribution"],
            "question": fake_test_set[1]["question"],
            "answer": "Answer 2",
            "contexts": ["Context 2"],
            "ground_truth": fake_test_set[1]["ground_truth"],
            "generation_mode": "llm",
            "generation_model": model,
        },
    }

    save_answers_checkpoint(checkpoint_file, partial_answers, test_fp, model)

    loaded = load_answers_checkpoint(checkpoint_file, fake_test_set, test_fp, model)
    assert len(loaded) == 2
    assert loaded[1]["answer"] == "Answer 1"
    assert loaded[2]["answer"] == "Answer 2"


def test_corrupt_or_stale_checkpoint_handling(tmp_path, fake_test_set):
    checkpoint_file = str(tmp_path / "checkpoint.json")

    # 1. Corrupted file
    with open(checkpoint_file, "w", encoding="utf-8") as f:
        f.write("{garbage_json")
    assert load_answers_checkpoint(checkpoint_file, fake_test_set, "test_fp", "model") == {}

    # 2. Stale test_set or model mismatch
    save_answers_checkpoint(checkpoint_file, {1: {"id": 1}}, "old_test_fp", "model_v1")
    assert load_answers_checkpoint(checkpoint_file, fake_test_set, "new_test_fp", "model_v1") == {}
    assert load_answers_checkpoint(checkpoint_file, fake_test_set, "old_test_fp", "model_v2") == {}


def test_final_file_protection_rejects_partial(fake_test_set):
    # Only 49 answers instead of 50
    partial = [
        {
            "id": fake_test_set[i]["id"],
            "distribution": fake_test_set[i]["distribution"],
            "question": fake_test_set[i]["question"],
            "answer": f"Answer {i+1}",
            "contexts": ["Ctx"],
            "ground_truth": fake_test_set[i]["ground_truth"],
            "generation_mode": "llm",
            "generation_model": "gpt-4o-mini",
        }
        for i in range(49)
    ]
    with pytest.raises(ValueError, match="Incomplete answers"):
        validate_final_answers(partial, fake_test_set)


def test_final_file_protection_rejects_out_of_order(fake_test_set):
    # Complete 50 but inverted order
    reversed_answers = [
        {
            "id": fake_test_set[i]["id"],
            "distribution": fake_test_set[i]["distribution"],
            "question": fake_test_set[i]["question"],
            "answer": f"Answer {i+1}",
            "contexts": ["Ctx"],
            "ground_truth": fake_test_set[i]["ground_truth"],
            "generation_mode": "llm",
            "generation_model": "gpt-4o-mini",
        }
        for i in range(50)
    ]
    reversed_answers[0], reversed_answers[1] = reversed_answers[1], reversed_answers[0]
    with pytest.raises(ValueError, match="Answers order or IDs do not match"):
        validate_final_answers(reversed_answers, fake_test_set)


def test_final_file_protection_accepts_valid_50(fake_test_set):
    valid = [
        {
            "id": fake_test_set[i]["id"],
            "distribution": fake_test_set[i]["distribution"],
            "question": fake_test_set[i]["question"],
            "answer": f"Answer {i+1}",
            "contexts": ["Ctx"],
            "ground_truth": fake_test_set[i]["ground_truth"],
            "generation_mode": "llm",
            "generation_model": "gpt-4o-mini",
        }
        for i in range(50)
    ]
    # Should not raise
    validate_final_answers(valid, fake_test_set)
