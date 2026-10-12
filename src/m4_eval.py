from __future__ import annotations

"""Module 4: RAGAS Evaluation — 4 metrics + failure analysis."""

import os, re, sys, json
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
from dataclasses import dataclass, asdict
from math import isfinite

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

TEST_SET_PATH = getattr(config, "TEST_SET_PATH", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fixtures", "test_set_50q.json"))


@dataclass
class EvalResult:
    question: str
    answer: str
    contexts: list[str]
    ground_truth: str
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float


SCORE_BOUND_EPSILON = 1e-12


def _safe_error_message(error: Exception) -> str:
    """Keep useful dependency diagnostics without echoing common credential forms."""
    message = str(error)
    message = re.sub(
        r"(?i)(api[_ -]?key|authorization|bearer|access[_ -]?token|secret)\s*[:=]\s*[^\s,;]+",
        r"\1=[REDACTED]", message,
    )
    message = re.sub(r"\b(?:sk|hf)_[A-Za-z0-9_-]{12,}\b", "[REDACTED]", message)
    return message


def _contract_score(value, name: str) -> float:
    """Validate RAGAS scores, absorbing only floating-point noise at [0, 1]."""
    score = float(value)
    if not isfinite(score):
        raise ValueError(f"RAGAS returned a non-finite {name} score")
    if -SCORE_BOUND_EPSILON <= score < 0.0:
        return 0.0
    if 1.0 < score <= 1.0 + SCORE_BOUND_EPSILON:
        return 1.0
    if not 0.0 <= score <= 1.0:
        raise ValueError(f"RAGAS returned {name}={score} outside the lab range [0, 1]")
    return score


def load_test_set(path: str = TEST_SET_PATH) -> list[dict]:
    """Load test set from JSON. (Đã implement sẵn)"""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def evaluate_ragas(questions: list[str], answers: list[str],
                   contexts: list[list[str]], ground_truths: list[str]) -> dict:
    """Run RAGAS evaluation."""
    import config
    # Pass evaluator models explicitly. RAGAS 0.1.22 attaches defaults to each
    # metric during evaluate(), then resets metric.llm/metric.embeddings before
    # returning. Inspecting those metrics afterward therefore loses the IDs;
    # the previous fallback also referenced undefined uppercase names.
    evaluator_llm_model = getattr(
        config, "RAGAS_LLM_MODEL", getattr(config, "JUDGE_MODEL", "gpt-4o-mini")
    )
    evaluator_embedding_model = getattr(
        config, "RAGAS_EMBEDDING_MODEL", getattr(config, "EMBEDDING_MODEL", "BAAI/bge-m3")
    )
    metric_names = ("faithfulness", "answer_relevancy", "context_precision", "context_recall")
    if not (len(questions) == len(answers) == len(contexts) == len(ground_truths)):
        raise ValueError("Evaluation inputs must have matching lengths")
    if not questions:
        return {**dict.fromkeys(metric_names, 0.0), "per_question": [],
                "metadata": {"evaluator_models": []}}

    stage = "initializing PyTorch runtime"
    try:
        # On Windows, importing Transformers/RAGAS first can initialize DLLs that
        # make torch's later c10.dll load fail (WinError 1114). Initialize torch
        # before any RAGAS or Sentence Transformers imports in this process.
        import torch  # noqa: F401

        stage = "loading RAGAS and local embedding adapters"
        from ragas import evaluate
        from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
        from ragas.llms import llm_factory
        from langchain_community.embeddings import HuggingFaceEmbeddings
        from datasets import Dataset

        stage = "building the evaluation dataset and LLM adapter"
        dataset = Dataset.from_dict({
            "question": questions, "answer": answers,
            "contexts": contexts, "ground_truth": ground_truths,
        })
        evaluator_llm = llm_factory(model=evaluator_llm_model)
        # Use the same local Hugging Face embedding model as retrieval; this
        # avoids sending evaluator text to a hosted embeddings endpoint.
        # Require cached local weights so evaluation never downloads a model.
        stage = f"initializing local embedding model {evaluator_embedding_model}"
        evaluator_embeddings = HuggingFaceEmbeddings(
            model_name=evaluator_embedding_model,
            model_kwargs={"local_files_only": True},
        )
        stage = "running RAGAS metrics"
        result = evaluate(
            dataset,
            metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
            llm=evaluator_llm,
            embeddings=evaluator_embeddings,
            raise_exceptions=True,
        )
        stage = "validating RAGAS metric rows"
        frame = result.to_pandas()
        if len(frame) != len(questions):
            raise ValueError("RAGAS must return one result per question")
        per_question = []
        for _, row in frame.iterrows():
            scores = {name: _contract_score(row[name], name) for name in metric_names}
            per_question.append(EvalResult(
                question=row["question"], answer=row["answer"],
                contexts=list(row["contexts"]), ground_truth=row["ground_truth"], **scores,
            ))
        return {**{name: sum(getattr(item, name) for item in per_question) / len(per_question)
                   for name in metric_names}, "per_question": per_question,
                "metadata": {"evaluator_models": [
                    evaluator_llm_model, evaluator_embedding_model
                ]}}
    except Exception as error:
        # Never turn setup/scoring failures into plausible zero-score rows.
        detail = _safe_error_message(error)
        raise RuntimeError(
            f"RAGAS evaluation failed while {stage} ({type(error).__name__}): {detail}"
        ) from None


def failure_analysis(eval_results: list[EvalResult], bottom_n: int = 10) -> list[dict]:
    """Analyze bottom-N worst questions using Diagnostic Tree."""
    if bottom_n <= 0:
        return []
    diagnostic_tree = {
        "faithfulness": (
            "LLM có thể bịa thông tin ngoài tài liệu",
            "Thắt chặt system prompt, giảm temperature về 0",
        ),
        "context_recall": (
            "Hệ thống tìm kiếm có thể bỏ sót đoạn văn liên quan",
            "Cải thiện chunking hoặc bổ sung từ khóa BM25",
        ),
        "context_precision": (
            "Đoạn văn không liên quan có thể bị xếp lên đầu",
            "Bổ sung Cross-Encoder reranking hoặc lọc theo metadata",
        ),
        "answer_relevancy": (
            "Câu trả lời có thể lệch trọng tâm câu hỏi",
            "Viết lại prompt để hướng dẫn trả lời trực tiếp hơn",
        ),
    }
    failures = []
    for result in eval_results:
        scores = {name: float(getattr(result, name)) for name in diagnostic_tree}
        if not all(isfinite(score) for score in scores.values()):
            raise ValueError("Failure analysis requires finite metric scores")
        worst_metric = min(scores, key=scores.get)
        diagnosis, suggested_fix = diagnostic_tree[worst_metric]
        failures.append({
            "question": result.question, "worst_metric": worst_metric,
            "score": sum(scores.values()) / len(scores),
            "diagnosis": diagnosis, "suggested_fix": suggested_fix,
        })
    return sorted(failures, key=lambda item: item["score"])[:bottom_n]


def save_report(results: dict, failures: list[dict], path: str = "reports/ragas_report.json"):
    """Save evaluation report to JSON. (Đã implement sẵn)"""
    parent_dir = os.path.dirname(path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)
    report = {
        "aggregate": {k: v for k, v in results.items() if k != "per_question"},
        "num_questions": len(results.get("per_question", [])),
        "failures": failures,
        "per_question": [asdict(item) for item in results.get("per_question", [])],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"Report saved to {path}")


if __name__ == "__main__":
    test_set = load_test_set()
    print(f"Loaded {len(test_set)} test questions")
    print("Run pipeline.py first to generate answers, then call evaluate_ragas().")
