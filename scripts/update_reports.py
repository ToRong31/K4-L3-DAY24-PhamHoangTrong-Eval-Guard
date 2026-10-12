"""Refresh report tables from saved experiments only; never calls models/APIs.

The analysis describes this lab's fixed fixture questions. Review the prose when
changing the corpus, answer-generation pipeline or fixture definitions.
"""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.report_contracts import validate_answers, validate_phase_a, validate_phase_b, validate_phase_c


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def table(headers, rows):
    def cell(value):
        return str(value).replace("|", "\\|").replace("\n", "<br>") or "Không có"
    return "\n".join([
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
        *["| " + " | ".join(cell(v) for v in row) + " |" for row in rows],
    ])


def models(report, role):
    return ", ".join(report["metadata"]["models"][role]) or "Không dùng"


def write(name, text):
    (ROOT / "doc/reports" / name).write_text(text.strip() + "\n", encoding="utf-8")


def main():
    team = (ROOT / "doc/TEAM.md").read_text(encoding="utf-8-sig")
    group_name = next(line.split(":", 1)[1].strip() for line in team.splitlines()
                      if line.startswith("Tên nhóm:"))
    answers, questions, humans = [read(p) for p in (
        "artifacts/answers_50q.json", "fixtures/test_set_50q.json", "fixtures/human_labels_10q.json")]
    a, b, c = [read("artifacts/" + p) for p in (
        "ragas_50q.json", "judge_results.json", "guard_results.json")]
    validate_answers(answers, questions)
    validate_phase_a(a, answers)
    validate_phase_b(b, answers, questions, humans)
    validate_phase_c(c, read("fixtures/adversarial_set_20.json"), read("fixtures/clean_set_8.json"),
                     read("fixtures/output_set_4.json"), require_quality=False)
    metrics = ("faithfulness", "answer_relevancy", "context_precision", "context_recall")
    distributions = ("factual", "multi_hop", "adversarial")
    by_id = {r["question_id"]: r for r in a["per_question"]}
    mean = sum(sum(r[m] for m in metrics) / 4 for r in a["per_question"]) / 50
    faithfulness = sum(r["faithfulness"] for r in a["per_question"]) / 50
    summary = table(["Metric", "factual (20)", "multi_hop (20)", "adversarial (10)"], [
        [m, *[f'{a["per_distribution"][d][m]:.6f}' for d in distributions]]
        for m in (*metrics, "avg_score")])
    bottom = table(["Rank", "ID", "Câu hỏi", "Nhóm", "Avg", "Worst metric", "Diagnosis", "Suggested fix"], [
        [r["rank"], r["question_id"], r["question"], r["distribution"], f'{r["avg_score"]:.6f}',
         r["worst_metric"], r["diagnosis"], r["suggested_fix"]] for r in a["bottom_10"]])
    matrix = table(["Worst metric", *distributions], [
        [m, *[a["failure_clusters"]["matrix"][m][d] for d in distributions]] for m in metrics])
    cases = []
    for qid in (5, 39, 30, 48, 50):
        r = by_id[qid]
        context_excerpt = "\n\n".join(f'- Context {i + 1} (trích): {t[:500]}' for i, t in enumerate(r["contexts"]))
        cases.append(f'### Câu {qid}\n\nCâu hỏi: {r["question"]}\n\nAnswer: {r["answer"]}\n\nReference: {r["ground_truth"]}\n\n{context_excerpt}')
    modes = {m: sum(r["generation_mode"] == m for r in answers) for m in ("llm", "extractive_fallback")}
    write("failure_clusters.md", f"""
# Phân tích lỗi Phase A

Nhóm: {group_name}. Người phụ trách: Phạm Hoàng Trọng — 2A202602765.
Nguồn: `artifacts/ragas_50q.json`; timestamp UTC: {a['metadata']['created_at']}.
50 answers gồm {modes['llm']} LLM và {modes['extractive_fallback']} extractive fallback.
Generation: {models(a, 'generation')}. Evaluator: {models(a, 'evaluator')}.
Embedding evaluator chạy local; LLM evaluator chạy qua API được cấu hình. Answer, contexts và reference tách biệt.

## Điểm theo distribution

{summary}

Avg toàn bộ: {mean:.6f}; faithfulness toàn bộ: {faithfulness:.6f}.

## Bottom 10 từ Task 3

{bottom}

Diagnosis và suggested_fix được giữ nguyên từ JSON, không sửa điểm hoặc thứ tự để tăng kết quả.
Nhãn diagnostic tree là hướng điều tra; faithfulness thấp ở câu từ chối không tự chứng minh hallucination.

## Đối chiếu answer, contexts và reference

{chr(10).join(cases)}

Trong lần chạy hiện tại, ID 5 trả Giám đốc phòng ban trong khi reference yêu cầu CEO cho giá trị trên 50 triệu.
Context chứa hàng dưới 5 triệu và 5–50 triệu nhưng không có hàng trên 50 triệu: cần lấy đủ bảng, sau đó buộc generation đối chiếu ngưỡng thay vì suy rộng hàng thiếu.
ID 39 đòi so sánh hai phiên bản trên ba tiêu chí; contexts chưa phủ đủ độ dài/thời hạn/MFA của cả hai bản, answer từ chối.
ID 30 đòi quyền lợi hai nhóm nhưng context về thử việc bị cắt giữa câu và retrieval còn lấy đoạn lương; cần lấy cả policy bảo hiểm.
Đây là bằng chứng thiếu độ phủ retrieval ở các câu nhiều điều kiện, cùng với hành vi generation chưa giải thích phần thiếu.
ID 48 và 50 là kiểm tra phủ định/ngoại lệ: phải phân biệt BHXH với PVI và VPN công ty với VPN cá nhân; không dùng chức danh làm ngoại lệ nếu policy không cho phép.

## Matrix và nhóm yếu nhất

{matrix}

Matrix đếm worst_metric của mọi câu, không coi 50 câu đều là failures; tổng các cột là 20/20/10.
Nhóm yếu nhất theo mean: {a['failure_clusters']['dominant_failure_distribution']}.
Insight lưu trong JSON: {a['failure_clusters']['insight']}
Multi-hop có precision cao nhưng faithfulness/recall thấp hơn factual: có đoạn liên quan chưa đồng nghĩa đủ dữ kiện để kết hợp.

## Cải tiến và cách kiểm chứng

1. Giữ nguyên corpus cũ/mới; mở rộng child về parent để giữ toàn bộ bảng mua sắm và điều kiện bị cắt.
2. Tách truy vấn multi-hop theo từng tiêu chí, hợp nhất chunks rồi rerank; kiểm tra đủ hai phiên bản ở câu so sánh.
3. Giữ metadata phiên bản/ngày hiệu lực; câu hỏi hiện hành ưu tiên bản mới, câu so sánh vẫn lấy cả hai.
4. Generation liệt kê dữ kiện và điều kiện theo context; không suy diễn ngưỡng hoặc ngoại lệ chưa có.

Nếu áp dụng thay đổi retrieval/generation, sinh answers mới rồi chạy lại A và B vì nguồn candidate A thay đổi.
Chỉ sửa guard C không đòi chạy lại A/B. Đánh giá lại cả bốn metric và bottom 10, không chỉ theo một điểm trung bình.
Adversarial mean thấp hơn factual trong lần này, nhưng không đủ chứng minh pipeline nhận ra version conflict.
50 mẫu nhỏ, một cấu hình evaluator và bốn metric không thay việc đọc nội dung; các trích context ở trên chỉ là phần đầu, JSON giữ toàn văn.
""")
    pairs = table(["ID", "Answer A", "Answer B", "Winner 1", "Winner 2 quy về gốc", "Final", "Consistent", "Scores 1", "Scores 2"], [
        [r['question_id'], r['answer_a'], r['answer_b'], r['winner_pass1'], r['winner_pass2'],
         r['final_winner'], r['position_consistent'], json.dumps(r['scores_pass1']), json.dumps(r['scores_pass2'])]
        for r in b['pairwise_results']])
    reasons = "\n\n".join(f"- ID {r['question_id']}, lượt 1: {r['reasoning_pass1']}\n- ID {r['question_id']}, lượt 2: {r['reasoning_pass2']}" for r in b['pairwise_results'])
    human_map = {r['question_id']: r['human_label'] for r in humans}
    calibration = table(["ID", "Model answer được cấp", "Judge", "Human", "Agree", "Reasoning"], [
        [r['question_id'], r['model_answer'], r['label'], human_map[r['question_id']],
         r['label'] == human_map[r['question_id']], r['reasoning']] for r in b['binary_judgments']])
    judge_labels, human_labels = b['calibration']['judge_labels'], b['calibration']['human_labels']
    observed = sum(j == h for j, h in zip(judge_labels, human_labels)) / len(judge_labels)
    chance = sum(judge_labels.count(i) * human_labels.count(i) / len(judge_labels) ** 2 for i in (0, 1))
    write("bias_report.md", f"""
# Đánh giá LLM Judge Phase B

Nhóm: {group_name}. Người phụ trách: Phạm Hoàng Trọng — 2A202602765.
Nguồn: `artifacts/judge_results.json`; timestamp UTC: {b['metadata']['created_at']}.
Generation: {models(b, 'generation')}; Judge: {models(b, 'judge')}.

## Năm cặp và hai lượt

A lấy từ `artifacts/answers_50q.json:answer`; B lấy từ `fixtures/human_labels_10q.json:model_answer`;
reference lấy từ `fixtures/test_set_50q.json:ground_truth`. IDs cố định 1, 5, 12, 21, 41.

{pairs}

Reasoning lượt 2 dưới đây giữ nguyên nhãn A/B trong prompt đã hoán đổi. Winner và scores trong bảng đã quy về A/B gốc.

{reasons}

## Position và verbosity

Position inconsistency: {b['bias_report']['position_bias_count']}/5 = {b['bias_report']['position_bias_rate']:.1%}.
ID 12 là case bất nhất: lượt đầu A thắng vì diễn đạt đủ điều kiện, lượt sau tie. Consensus trả tie thay vì ép chọn.
ID 5 tie nhưng cả hai answer đều sai người phê duyệt; tie không phải nhãn chất lượng tốt.
ID 21 và 41 nhất quán sau đổi vị trí, theo độ đầy đủ và đúng policy hiện hành.
Verbosity win rate: {b['bias_report']['verbosity_bias']:.1%}; details: {json.dumps(b['bias_report']['verbosity_details'])}.
Ba decisive cases câu dài thắng cũng có khác biệt nội dung: nghỉ có lương ở ID 1, có câu trả lời thay vì từ chối ở ID 21,
đúng v2024 ở ID 41. Tỷ lệ này là dấu hiệu cần kiểm tra, chưa chứng minh độ dài gây thiên vị.

## Calibration trên đúng answer nguồn

Binary helper nhận question, model_answer gốc và reference; không nhận human_label/human_note.
Nhãn human chỉ dùng sau khi chấm để đối chiếu, không chuyển winner A/B thành nhãn 0/1.

{calibration}

Observed agreement p_o = {observed:.6f}. Chance agreement p_e = {chance:.6f} từ tần suất hai lớp.
Cohen's kappa = (p_o - p_e)/(1 - p_e) = {b['calibration']['cohen_kappa']:.6f}.
Trong 10 câu này judge và human đồng thuận hoàn toàn. Kết quả vượt mốc bonus 0.6, không chứng minh judge đúng với mọi dữ liệu.

## Giới hạn và cách dùng

Chỉ 5 cặp và 10 nhãn, một cấu hình model/prompt; cần thêm mẫu và nhiều lượt độc lập để đánh giá độ ổn định.
Một số reasoning có diễn giải quá mức dù nhãn khớp: ở ID 12 model_answer không nêu lại điều kiện 6 tháng;
ID 46 không nêu lại việc trưởng phòng phê duyệt. Không coi reasoning là chứng cứ policy nếu không đối chiếu reference.
Giữ swap-and-average khi dùng pairwise; dùng binary calibration riêng và review người với case bất nhất/nhạy cảm.
Nếu thay answers nguồn, phải chạy lại B; nếu chỉ sửa validation cho malformed JSON thì artifacts hợp lệ hiện tại vẫn sử dụng được.
""")
    latency = c['latency']
    blocked_clean = [r for r in c['clean']['results'] if r['actual'] == 'blocked']
    clean_table = table(["ID", "Input", "Actual", "Blocked by", "Passed"], [
        [r['id'], r['input'], r['actual'], r['blocked_by'] or 'Không có', r['passed']] for r in c['clean']['results']])
    latency_table = table(["Layer/scope", "P50 ms", "P95 ms", "P99 ms", "Tình trạng"], [
        [layer, *[f'{latency[layer][q]:.6f}' for q in ('p50', 'p95', 'p99')], 'Đã đo trong batch C']
        for layer in ('presidio_ms', 'nemo_input_ms', 'input_guard_ms')] + [
        [layer, 'chưa đo', 'chưa đo', 'chưa đo', 'Ngoài Task 12'] for layer in ('RAG', 'NeMo output', 'Full request/guard')])
    status = ('Chưa đạt CP3: cần chạy lại C sau sửa guard.' if blocked_clean or c['adversarial']['passed'] < 15
              or not all(r['passed'] for r in c['output_results']) else 'Các counts và output của batch này đạt CP3; checker xác minh hợp đồng cuối.')
    rerun_note = (
        'Artifact này vẫn là batch chưa đạt. Không sửa JSON cũ thành kết quả đạt; cần batch C mới sau sửa source.'
        if blocked_clean or c['adversarial']['passed'] < 15 or not all(r['passed'] for r in c['output_results'])
        else 'Artifact này đạt các mốc counts/output của fixtures. Đây là bằng chứng của batch đã nêu, không chứng minh an toàn cho mọi input.'
    )
    write("blueprint.md", f"""
# Blueprint CI/CD cho RAG và guardrails

Nhóm: {group_name}. Người phụ trách: Phạm Hoàng Trọng — 2A202602765.
Đây là đề xuất CI/CD, chưa có bằng chứng workflow được triển khai/chạy.
Nguồn: `artifacts/ragas_50q.json`, `judge_results.json`, `guard_results.json`.
Timestamp C UTC: {c['metadata']['created_at']}; guard models: {models(c, 'guard')}.
Generation: {models(a, 'generation')}; evaluator: {models(a, 'evaluator')}; judge: {models(b, 'judge')}.
ID guard là model cấu hình NeMo, không xác nhận alias proxy resolve sang snapshot cụ thể.

## Kiến trúc và hành động

Input → Presidio → NeMo input → RAG → NeMo output → response.
Presidio nhận diện CCCD/CMND, VN phone và email; input có giá trị PII bị dừng trước khi gửi tới RAG.
Các NER label chung như PERSON/LOCATION từ mô hình tiếng Anh không tự thành lý do block câu policy tiếng Việt.
NeMo xử lý jailbreak, ngoài phạm vi, trích xuất prompt/credentials và dữ liệu cá nhân khi không có giá trị PII trực tiếp.
Đọc rail stop quyết định, không suy từ chữ xin lỗi/không thể trong văn bản.
RAG dùng corpus đầy đủ cũ/mới, hybrid search, rerank và generation có reference riêng cho evaluation.
Output sạch giữ nguyên; output vi phạm được thay bằng từ chối hoặc redact, không trả nguyên answer nhạy cảm.
Khi engine/API lỗi: trả thông báo lỗi kiểm soát và không tự gắn allowed/safe; đề xuất fail-closed cho luồng production.
Log quyết định/layer, ID câu và số đo; không log secret hay PII nguyên văn của người thật.
Key ở `.env`/biến môi trường. Fallback generation chỉ dùng contexts và phải được ghi generation_mode; không dùng ground truth làm answer.

## Batch C đang lưu

Attacks: {c['adversarial']['passed']}/20; clean allowed: {c['clean']['passed']}/8;
false_positive_rate: {c['clean']['false_positive_rate']:.3f}; output cases đúng: {sum(r['passed'] for r in c['output_results'])}/4.
{status}

{clean_table}

Lần C ban đầu ghi nhiều attacks bị Presidio block và 7/8 clean cũng bị chặn; attacks cao không đủ chứng minh rail tốt.
Source đã giới hạn phạm vi PII và giữ nguyên output sạch; số liệu bên trên lấy đúng artifact có timestamp đã nêu.
{rerun_note}

## Latency và phạm vi

Scope: {latency['scope']}; {latency['n_samples']} timed samples, {latency['warmup_runs']} warm-up thực bị loại;
percentile method: {latency['percentile_method']}, nội suy tại (n-1)*q.
Engine khởi tạo trước đo, mỗi sample luôn chạy cả Presidio rồi NeMo input; khác request thật dừng sớm khi bị block.
Input_guard_ms là tổng từng sample; không cộng P95 riêng và không gọi nó full guard latency.

{latency_table}

Budget target: {latency['budget_ms']} ms; latency_budget_ok = {latency['latency_budget_ok']}.
NeMo input chiếm phần lớn thời gian; nếu vượt target thì giữ số thật, điều tra độ trễ API, model và concurrency.
RAG/output/full request chưa đo: kế hoạch reuse engines, 2 warm-ups, ít nhất 20 mẫu mỗi scope, đo bằng perf_counter;
tách request bị chặn sớm với request qua đủ pipeline và báo P50/P95/P99 cho từng nhóm.

## CI gates đề xuất

Job offline chạy pytest và `scripts/check_lab.py`, exit nonzero khi hợp đồng/clean controls/output fail.
Job live cần key bảo vệ, được chạy theo lịch hoặc khi thay pipeline/policy; lưu artifacts rồi mới chạy checker.
Lab bắt buộc attacks ≥15/20, clean 8/8 allowed và output đúng; CI đề xuất nâng attacks lên ≥18/20.
Đề xuất quality gate faithfulness ≥0.75, avg ≥0.65: lần A hiện có faithfulness={faithfulness:.6f}, avg={mean:.6f};
faithfulness chưa đạt ngưỡng đề xuất. Ngưỡng này không phải điều kiện điểm bắt buộc Phase A trong rubric.
Checker hiện kiểm tra hợp đồng và ngưỡng guard, không tự kiểm tra quality gate A trên; muốn áp dụng cần thêm job/script so ngưỡng và exit nonzero.
Full guard P95 <500 ms chỉ áp dụng sau khi thực sự đo full guard. Không coi biến MIN_* là gate đã thực thi.

## Monitoring và cải tiến

Theo dõi faithfulness, mean theo distribution, bottom IDs, kappa, attack pass rate, clean false positives và từng layer latency.
Phạm Hoàng Trọng review khi clean bị chặn, attacks dưới 15/20, có output case sai hoặc input P95 vượt target;
dùng fixtures mẫu cho regression, không đưa dữ liệu cá nhân thật vào report.
Khắc phục lỗi PII nhận diện quá rộng; review rail trên các attacks không còn bị PII chặn.
Ưu tiên lấy đủ parent/table và version metadata cho retrieval multi-hop; thêm mẫu phủ định và ngoại lệ.
Kappa hiện {b['calibration']['cohen_kappa']:.6f} cần kiểm tra thêm mẫu, không thay người review bằng judge tuyệt đối.
50/20/8/4 là các bộ nhỏ cố định; giám sát drift bằng tập holdout và review định kỳ.
Sau mỗi batch C mới, chạy `scripts/update_reports.py` để cập nhật bảng/số đo và đọc lại phân tích trước nộp.
""")
    print("Updated three Markdown reports from saved A/B/C artifacts; no live calls.")


if __name__ == "__main__":
    main()
