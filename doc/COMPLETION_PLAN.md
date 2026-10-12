# Kế hoạch hoàn thành theo checkpoints và rubric

Đối chiếu: ASSIGNMENT, CHECKPOINTS, RUBRIC, REPORT_SCHEMAS, PIPELINE_INTERFACE, ENVIRONMENT, RULES và SUBMISSION.
Người thực hiện: Phạm Hoàng Trọng — 2A202602765. Lệnh live do người thực hiện chạy.

| Checkpoint | Bằng chứng và tình trạng | Hành động còn lại |
| --- | --- | --- |
| CP0 | Năm module có giao diện tích hợp; answers 50 ID đúng 20/20/10, có generation_mode/model; pip check đạt | Không cần setup lại cho sửa guard. Nếu thay corpus/pipeline, dùng refresh cache và sinh answers mới |
| CP1 / Tasks 1–4 | Phase A artifact hợp lệ, 50 rows/4 metrics, 10 bottom rows, matrix/means, evaluator models tách riêng; report điền từ JSON | Giữ A hiện tại. Cải tiến chất lượng retrieval là đề xuất, chưa thực hiện |
| CP2 / Tasks 5–8 | B đủ 5 cặp/10 lượt và 10 binary judgments đúng nguồn; kappa/bias hợp lệ; report điền từ JSON | Validation reply malformed được siết để không tạo scores giả; reply cũ hợp lệ không đổi nên không cần chạy B lại |
| CP3 / Tasks 9a–12 | C mới lúc 08:13:18 UTC: attacks 18/20, clean 7/8, outputs 4/4. Câu policy mật khẩu ID 107 bị NeMo chặn; hai off-topic attacks lọt | Đã làm rõ policy cho phép yêu cầu mật khẩu chung và chặn ngoài phạm vi, temperature=0; cần chạy C mới để xác nhận clean 8/8 |
| CP4 / Task 13 | TEAM một người; báo cáo A/B và blueprint từ số liệu thật. Blueprint ghi C chưa đạt và scope latency chính xác | Cập nhật từ batch C mới, checker pass; kiểm tra secrets, commit/push, chốt SHA và deadline coach rồi gửi link |

## Thứ tự thực hiện tiếp

1. `.\.venv\Scripts\python.exe scripts/run_experiments.py --phase c --live --latency-samples 20`.
2. `.\.venv\Scripts\python.exe scripts/update_reports.py` cập nhật bảng/timestamps/latency theo artifacts mới; đọc lại phân tích trước nộp.
3. `.\.venv\Scripts\python.exe scripts/check_lab.py`. Checker không gọi API.
4. Nếu C còn sai, đối chiếu từng ID và blocked_by; sửa layer gây sai rồi chạy lại chỉ C. Không sửa actual/passed trong JSON.
5. Khi checker đạt, kiểm tra `.env`/cache không được commit; stage source/artifacts/reports, commit/push và cập nhật TEAM với commit dùng để chấm.

Không cần chạy lại setup/A/B khi chỉ đổi guard. Nếu sinh lại answers thì A/B phải chạy lại vì nguồn answer/candidate A đổi.
Không chạy integration live thêm sau batch C để tránh trả phí lặp lại.

## Quality và giới hạn

Ngưỡng bắt buộc C là 15/20, bonus 18/20 vẫn yêu cầu clean 8/8. Budget 500 ms là target; số đo vượt target vẫn ghi thật.
CI faithfulness ≥0.75/avg ≥0.65 là đề xuất blueprint, không phải quality gate đã triển khai.
Pipeline hiện có retrieval/generation yếu ở multi-hop; báo cáo nêu bằng chứng và hướng cải tiến, không đổi corpus/test để làm eval dễ hơn.
Cache resume answers chưa gắn fingerprint corpus/provider đầy đủ: nếu thay corpus/model/provider/code, dùng `--refresh-cache` thay vì checkpoint cũ.
Deadline trong README và tài liệu nộp bài có mốc khác nhau; dùng thông báo coach, chưa tự chốt deadline.
Kế hoạch này không tuyên bố CP3 đạt trước khi có batch live mới và checker xác nhận.

## Kết quả kiểm chứng sau audit

- `python -m pip check`: No broken requirements found.
- `python -m pytest tests/ -q`: 102 passed, 3 integration tests deselected; không gọi API.
- Presidio thật trên máy: 8/8 clean inputs không chứa các entity PII của lab; bốn inputs chứa giá trị PII mẫu vẫn phát hiện CCCD/VN phone/email.
- `scripts/check_lab.py`: TEAM, ba reports, source, answers và artifacts A/B pass; còn đúng một lỗi C vì JSON đang lưu batch trước sửa.
- Không chạy thêm batch live trong audit này; số liệu C chỉ được thay bằng lần người thực hiện chạy lại thật.
