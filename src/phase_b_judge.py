from __future__ import annotations

"""Phase B: LLM-as-Judge — pairwise, swap-and-average, Cohen κ, bias analysis."""

import json
import math
import os
import sys
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OPENAI_API_KEY, JUDGE_MODEL, HUMAN_LABELS_PATH


@dataclass
class JudgeResult:
    question: str
    answer_a: str
    answer_b: str
    winner_pass1: str       # "A" | "B" | "tie"  (original order)
    winner_pass2: str       # "A" | "B" | "tie"  (after swap, ALREADY converted back)
    final_winner: str       # consensus after swap-and-average
    reasoning_pass1: str
    reasoning_pass2: str
    position_consistent: bool  # True if both passes agree on same answer
    scores_pass1: dict = field(default_factory=dict)  # {"A": float, "B": float}
    scores_pass2: dict = field(default_factory=dict)


# ─── Task 5: Pairwise Judge ───────────────────────────────────────────────────

def pairwise_judge(question: str, answer_a: str, answer_b: str, reference: str = "") -> dict:
    """Task 5: Gọi LLM để chọn answer tốt hơn (A hoặc B) theo 3 tiêu chí."""
    prompt_template = (
        "Bạn là một expert đánh giá chất lượng câu trả lời RAG.\n\n"
        f"Câu hỏi: {question}\n"
        f"Chính sách/đáp án tham chiếu: {reference}\n\n"
        f"Answer A:\n{answer_a}\n\n"
        f"Answer B:\n{answer_b}\n\n"
        "Đánh giá dựa trên 3 tiêu chí: độ chính xác (accuracy theo reference), đầy đủ (completeness), súc tích (conciseness).\n"
        "Trả lời JSON (chỉ JSON, không text khác):\n"
        '{"winner": "A" hoặc "B" hoặc "tie", "reasoning": "giải thích ngắn gọn", "scores": {"A": 0.0-1.0, "B": 0.0-1.0}}'
    )

    from openai import OpenAI
    client = OpenAI()
    resp = client.chat.completions.create(
        model=JUDGE_MODEL,
        messages=[
            {"role": "system", "content": "Bạn là expert đánh giá RAG. Chỉ trả lời JSON."},
            {"role": "user", "content": prompt_template},
        ],
        response_format={"type": "json_object"},
    )
    result = json.loads(resp.choices[0].message.content)
    if not isinstance(result, dict):
        raise ValueError("Pairwise judge must return a JSON object")
    winner = result.get("winner")
    if winner not in ("A", "B", "tie"):
        raise ValueError("Pairwise judge winner must be A, B or tie")
    reasoning = result.get("reasoning")
    if not isinstance(reasoning, str) or not reasoning.strip():
        raise ValueError("Pairwise judge must supply nonempty reasoning")
    scores = result.get("scores")
    if not isinstance(scores, dict) or set(scores) != {"A", "B"}:
        raise ValueError("Pairwise judge must supply scores for A and B")
    for label, value in scores.items():
        if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError(f"Pairwise judge score {label} must be finite and within [0, 1]")
    return {
        "winner": winner,
        "reasoning": reasoning,
        "scores": {
            "A": float(scores["A"]),
            "B": float(scores["B"]),
        },
    }


# ─── Task 6: Swap-and-Average ─────────────────────────────────────────────────

def swap_and_average(question: str, answer_a: str, answer_b: str, reference: str = "") -> JudgeResult:
    """Task 6: Chạy pairwise 2 lần (hoán đổi thứ tự), lấy kết quả nhất quán."""
    pass1 = pairwise_judge(question, answer_a, answer_b, reference=reference)
    pass2_raw = pairwise_judge(question, answer_b, answer_a, reference=reference)

    swap_map = {"A": "B", "B": "A", "tie": "tie"}
    winner_pass2 = swap_map.get(pass2_raw["winner"], "tie")

    position_consistent = (pass1["winner"] == winner_pass2)
    final = pass1["winner"] if position_consistent else "tie"

    scores_p2_raw = pass2_raw.get("scores", {})
    scores_pass2 = {
        "A": float(scores_p2_raw.get("B", 0.0)),
        "B": float(scores_p2_raw.get("A", 0.0)),
    }

    return JudgeResult(
        question=question,
        answer_a=answer_a,
        answer_b=answer_b,
        winner_pass1=pass1["winner"],
        winner_pass2=winner_pass2,
        final_winner=final,
        reasoning_pass1=pass1["reasoning"],
        reasoning_pass2=pass2_raw["reasoning"],
        position_consistent=position_consistent,
        scores_pass1={k: float(v) for k, v in pass1.get("scores", {}).items()},
        scores_pass2=scores_pass2,
    )


# ─── Task 7: Cohen's κ ────────────────────────────────────────────────────────

def cohen_kappa(judge_labels: list[int], human_labels: list[int]) -> float:
    """Task 7: Tính Cohen's κ giữa LLM judge và human labels."""
    if not judge_labels or len(judge_labels) != len(human_labels):
        return 0.0
    n = len(judge_labels)
    observed = sum(j == h for j, h in zip(judge_labels, human_labels)) / n
    p_e = sum(judge_labels.count(label) * human_labels.count(label) / (n * n) for label in (0, 1))
    if p_e >= 1.0:
        return 1.0 if observed == 1.0 else 0.0
    return (observed - p_e) / (1.0 - p_e)


# ─── Task 8: Bias Report ──────────────────────────────────────────────────────

def bias_report(judge_results: list[JudgeResult]) -> dict:
    """Task 8: Đo lường position bias và verbosity bias."""
    total = len(judge_results)
    if total == 0:
        return {
            "total_judged": 0,
            "position_bias_rate": 0.0,
            "position_bias_count": 0,
            "verbosity_bias": 0.0,
            "verbosity_details": {"a_wins_a_longer": 0, "b_wins_b_longer": 0, "total_decisive": 0},
            "interpretation": "Không có dữ liệu đánh giá.",
        }

    position_bias_count = sum(1 for r in judge_results if not r.position_consistent)
    position_bias_rate = position_bias_count / total

    decisive = sum(1 for r in judge_results if r.final_winner != "tie")
    a_wins_a_longer = sum(
        1 for r in judge_results
        if r.final_winner == "A" and len(r.answer_a) > len(r.answer_b)
    )
    b_wins_b_longer = sum(
        1 for r in judge_results
        if r.final_winner == "B" and len(r.answer_b) > len(r.answer_a)
    )
    longer_wins = a_wins_a_longer + b_wins_b_longer
    verbosity_bias = (longer_wins / decisive) if decisive > 0 else 0.0

    interpretation = (
        f"Position bias rate là {position_bias_rate:.1%} ({position_bias_count}/{total} cases bất nhất). "
        f"Verbosity bias rate là {verbosity_bias:.1%} ({longer_wins}/{decisive if decisive else 1} decisive cases câu dài thắng). "
        + ("Position bias cao, swap-and-average rất cần thiết." if position_bias_rate > 0.3 else "Judge có tính nhất quán vị trí tốt.")
    )

    return {
        "total_judged": total,
        "position_bias_rate": position_bias_rate,
        "position_bias_count": position_bias_count,
        "verbosity_bias": verbosity_bias,
        "verbosity_details": {
            "a_wins_a_longer": a_wins_a_longer,
            "b_wins_b_longer": b_wins_b_longer,
            "total_decisive": decisive,
        },
        "interpretation": interpretation,
    }


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from scripts.run_experiments import main
    raise SystemExit(main(["--phase", "b", *sys.argv[1:]]))
