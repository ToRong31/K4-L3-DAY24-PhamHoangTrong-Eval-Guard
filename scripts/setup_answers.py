"""
Setup script: chạy Day 18 pipeline trên 50 câu hỏi → lưu artifacts/answers_50q.json

Chạy TRƯỚC khi bắt đầu Phase A:
    python scripts/setup_answers.py --live

Yêu cầu:
    1. Có 5 module m1-m5 với giao diện trong doc/PIPELINE_INTERFACE.md
       Script tự lắp module; không gọi src/pipeline.py.
    2. docker compose -f infra/docker-compose.yml up -d  (Qdrant đang chạy trên port 6333)
    3. .env có OPENAI_API_KEY
"""
from __future__ import annotations

import json
import argparse
import os
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hashlib
from config import ROOT_DIR, TEST_SET_PATH, ANSWERS_PATH, GENERATION_MODEL
from src.setup_cache import (
    get_cache_dir,
    save_json_atomic,
    compute_corpus_fingerprint,
    compute_config_fingerprint,
    compute_code_fingerprint,
    compute_test_set_fingerprint,
    load_cached_enriched_chunks,
    save_cached_enriched_chunks,
    load_dense_index_manifest,
    save_dense_index_manifest,
    get_answers_checkpoint_path,
    load_answers_checkpoint,
    save_answers_checkpoint,
    validate_final_answers,
)


def check_day18_files() -> bool:
    required = [
        "src/m1_chunking.py", "src/m2_search.py", "src/m3_rerank.py",
        "src/m4_eval.py",     "src/m5_enrichment.py",
    ]
    missing = [f for f in required if not os.path.exists(os.path.join(ROOT_DIR, f))]
    if missing:
        print("\n❌ Thiếu files từ Day 18. Copy chúng vào src/ trước:\n")
        for f in missing:
            print(f"   cp <Day18>/src/{os.path.basename(f)} src/")
        return False
    print(f"✓ Day 18 source files: {len(required)}/{len(required)} found")
    return True


def build_pipeline(resume: bool = False, refresh_cache: bool = False):
    # This assembler calls m1/m2/m3/m5 directly, NOT src.pipeline.py.
    from src.m1_chunking import load_documents, chunk_hierarchical
    from src.m2_search import HybridSearch
    from src.m3_rerank import CrossEncoderReranker
    from src.m5_enrichment import enrich_chunks
    from config import RERANK_TOP_K, DATA_DIR, COLLECTION_NAME, EMBEDDING_MODEL, EMBEDDING_DIM

    cache_dir = get_cache_dir()
    corpus_fp = compute_corpus_fingerprint(DATA_DIR)
    config_fp = compute_config_fingerprint()
    code_fp = compute_code_fingerprint([
        os.path.join(ROOT_DIR, "src/m1_chunking.py"),
        os.path.join(ROOT_DIR, "src/m5_enrichment.py"),
    ])

    print("\n[1/3] Chunking + enriching documents...")
    t0 = time.time()
    all_chunks = None

    if resume and not refresh_cache:
        cached = load_cached_enriched_chunks(cache_dir, corpus_fp, config_fp, code_fp)
        if cached:
            all_chunks = cached
            print(f"  ✓ Reused {len(all_chunks)} cached enriched chunks ({time.time()-t0:.1f}s)")
        else:
            print("  ℹ️  No valid enriched chunks cache found (or fingerprints changed); computing...")

    if all_chunks is None:
        docs = load_documents()
        all_chunks = []
        for doc in docs:
            parents, children = chunk_hierarchical(doc["text"], metadata=doc["metadata"])
            for child in children:
                all_chunks.append({
                    "text": child.text,
                    "metadata": {**child.metadata, "parent_id": child.parent_id},
                })

        enriched = enrich_chunks(all_chunks)
        if enriched:
            if len(enriched) != len(all_chunks):
                raise ValueError("enrich_chunks must preserve chunk count/order; see doc/PIPELINE_INTERFACE.md")
            all_chunks = [{"text": e.enriched_text,
                           "metadata": {**original["metadata"], **e.auto_metadata}}
                          for original, e in zip(all_chunks, enriched)]
            print(f"  ✓ Enriched {len(enriched)} chunks ({time.time()-t0:.1f}s)")
        else:
            print(f"  ✓ Using {len(all_chunks)} raw chunks (M5 not implemented or no API key)")

        save_cached_enriched_chunks(cache_dir, all_chunks, corpus_fp, config_fp, code_fp)

    print("\n[2/3] Indexing (BM25 + Dense)...")
    t0 = time.time()
    search = HybridSearch()
    chunks_hash = hashlib.sha256(json.dumps(all_chunks, sort_keys=True).encode("utf-8")).hexdigest()

    can_reuse_dense = False
    if resume and not refresh_cache:
        has_manifest = load_dense_index_manifest(
            cache_dir, COLLECTION_NAME, EMBEDDING_MODEL, EMBEDDING_DIM, chunks_hash
        )
        if has_manifest:
            try:
                if search.dense.client.collection_exists(COLLECTION_NAME):
                    can_reuse_dense = True
            except Exception:
                can_reuse_dense = False

    if can_reuse_dense:
        search.index(all_chunks, reuse_dense=True)
        print(f"  ✓ Reused existing Qdrant collection '{COLLECTION_NAME}' & rebuilt BM25 index ({time.time()-t0:.1f}s)")
    else:
        search.index(all_chunks, reuse_dense=False)
        save_dense_index_manifest(
            cache_dir, COLLECTION_NAME, EMBEDDING_MODEL, EMBEDDING_DIM, chunks_hash, len(all_chunks)
        )
        print(f"  ✓ Indexed {len(all_chunks)} chunks (BM25 + Dense) ({time.time()-t0:.1f}s)")

    print("\n[3/3] Loading reranker...")
    t0 = time.time()
    reranker = CrossEncoderReranker()
    print(f"  ✓ Reranker ready ({time.time()-t0:.1f}s)")

    return search, reranker, RERANK_TOP_K


def run_query(q: str, search, reranker, top_k: int, client=None) -> tuple[str, list[str], str, str | None]:
    from config import OPENAI_API_KEY

    results = search.search(q)
    docs    = [{"text": r.text, "score": r.score, "metadata": r.metadata} for r in results]
    reranked = reranker.rerank(q, docs, top_k=top_k)
    contexts = [r.text for r in reranked] if reranked else [r.text for r in results[:3]]

    if (OPENAI_API_KEY or client is not None) and contexts:
        try:
            if client is None:
                from openai import OpenAI
                client = OpenAI()
            ctx = "\n\n".join(contexts)
            resp = client.chat.completions.create(
                model=GENERATION_MODEL,
                messages=[
                    {"role": "system", "content": "Trả lời CHỈ dựa trên context. Nếu không có → nói 'Không tìm thấy.'"},
                    {"role": "user",   "content": f"Context:\n{ctx}\n\nCâu hỏi: {q}"},
                ],
            )
            reported_model = getattr(resp, "model", None)
            used_model = reported_model if isinstance(reported_model, str) and reported_model.strip() else GENERATION_MODEL
            return resp.choices[0].message.content, contexts, "llm", used_model
        except Exception as e:
            print(f"  ⚠️  LLM generation failed: {e}")

    return (contexts[0] if contexts else "Không tìm thấy thông tin."), contexts, "extractive_fallback", None


def main(argv=None):
    parser = argparse.ArgumentParser(description="Assemble previous modules and generate 50 answers (API cost).")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--resume", action="store_true", help="Resume from cached chunks/index and query checkpoints")
    parser.add_argument("--refresh-cache", action="store_true", help="Force rebuild chunks cache and reindex")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("Generation/enrichment may call APIs. Pass --live after completing pre-class setup.")
    print("=" * 60)
    print("K4 / TRACK 3B SETUP — Generating answers for 50 questions")
    if args.resume:
        print("  [Mode: --resume enabled]")
    if args.refresh_cache:
        print("  [Mode: --refresh-cache enabled]")
    print("=" * 60)

    if not check_day18_files():
        sys.exit(1)

    with open(TEST_SET_PATH, encoding="utf-8") as f:
        test_set = json.load(f)
    print(f"✓ Loaded {len(test_set)} questions (factual/multi_hop/adversarial)")

    cache_dir = get_cache_dir()
    test_fp = compute_test_set_fingerprint(TEST_SET_PATH)
    checkpoint_path = get_answers_checkpoint_path(cache_dir)

    try:
        search, reranker, top_k = build_pipeline(resume=args.resume, refresh_cache=args.refresh_cache)
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("→ Đảm bảo bạn đã copy src/ từ Day 18 và đã pip install -r requirements/requirements.txt")
        sys.exit(1)

    completed_answers: dict[int, dict] = {}
    if args.resume and not args.refresh_cache:
        completed_answers = load_answers_checkpoint(
            checkpoint_path, test_set, test_fp, GENERATION_MODEL
        )
        if completed_answers:
            print(f"✓ Found valid checkpoint with {len(completed_answers)} completed queries.")
            remaining_count = len(test_set) - len(completed_answers)
            if remaining_count > 0:
                print(f"  Resuming remaining {remaining_count} queries...")
            else:
                print("  All 50 queries already completed in checkpoint!")

    print(f"\nRunning {len(test_set)} queries...")
    from config import OPENAI_API_KEY
    client = None
    if OPENAI_API_KEY:
        from openai import OpenAI
        client = OpenAI()
    t_start = time.time()

    for i, item in enumerate(test_set):
        qid = item["id"]
        if qid in completed_answers:
            continue

        answer, contexts, generation_mode, generation_model = run_query(
            item["question"], search, reranker, top_k, client
        )
        rec = {
            "id":           qid,
            "distribution": item["distribution"],
            "question":     item["question"],
            "answer":       answer,
            "contexts":     contexts,
            "ground_truth": item["ground_truth"],
            "generation_mode": generation_mode,
            "generation_model": generation_model,
        }
        completed_answers[qid] = rec

        if args.resume:
            save_answers_checkpoint(checkpoint_path, completed_answers, test_fp, GENERATION_MODEL)

        count_done = len(completed_answers)
        if count_done % 10 == 0 or count_done == len(test_set):
            print(f"  [{count_done}/{len(test_set)}] done ({time.time()-t_start:.0f}s elapsed)")

    # Build final list preserving strict source test_set order
    answers = [completed_answers[item["id"]] for item in test_set]

    # Validate complete 50 rows before writing final file!
    validate_final_answers(answers, test_set)

    # Atomic write to final answers_50q.json
    save_json_atomic(ANSWERS_PATH, answers)

    print(f"\n✓ Saved {len(answers)} answers → artifacts/answers_50q.json")
    print(f"  Total time: {time.time()-t_start:.1f}s")
    print("\n→ Bây giờ bắt đầu Phase A:")
    print("     python scripts/run_experiments.py --phase a --live")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
