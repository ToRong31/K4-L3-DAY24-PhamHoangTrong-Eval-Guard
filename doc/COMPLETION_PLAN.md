# Kế hoạch hoàn thành theo checkpoints và rubric

Đối chiếu: ASSIGNMENT, CHECKPOINTS, RUBRIC, REPORT_SCHEMAS, PIPELINE_INTERFACE, ENVIRONMENT, RULES và SUBMISSION.
Người thực hiện: Phạm Hoàng Trọng — 2A202602765. Lệnh live do người thực hiện chạy.

| Checkpoint | Bằng chứng và tình trạng | Hành động còn lại |
| --- | --- | --- |
| CP0 | Năm module có giao diện tích hợp; answers 50 ID đúng 20/20/10, có generation_mode/model; pip check đạt | Không cần setup lại cho sửa guard. Nếu thay corpus/pipeline, dùng refresh cache và sinh answers mới |
| CP1 / Tasks 1–4 | Phase A artifact hợp lệ, 50 rows/4 metrics, 10 bottom rows, matrix/means, evaluator models tách riêng; report điền từ JSON | Giữ A hiện tại. Cải tiến chất lượng retrieval là đề xuất, chưa thực hiện |
| CP2 / Tasks 5–8 | B đủ 5 cặp/10 lượt và 10 binary judgments đúng nguồn; kappa/bias hợp lệ; report điền từ JSON | Validation reply malformed được siết để không tạo scores giả; reply cũ hợp lệ không đổi nên không cần chạy B lại |
| CP3 / Tasks 9a–12 | C cuối 08:17:29 UTC đạt attacks 20/20, clean 8/8, outputs 4/4; 20 timed samples, 2 warm-up. Input P95 850.107065 ms được báo đúng | Đã hoàn tất bằng chứng bắt buộc; không cần chạy C lại |
| CP4 / Task 13 | TEAM một người, nhóm SoloLeveling; báo cáo A/B/blueprint theo artifacts hiện tại; checker và 102 tests pass. Source/artifacts đã push ở 72dfce0 | Commit/push cập nhật Markdown cuối, đối chiếu tên repo/deadline coach, chốt SHA rồi gửi link |

## Thứ tự thực hiện tiếp

1. Không chạy lại batch live: các artifacts A/B/C hiện đã hợp lệ.
2. Báo cáo đã cập nhật theo batch C cuối; dùng `scripts/update_reports.py` chỉ khi artifacts đổi.
3. Chạy `scripts/check_lab.py --with-tests` để kiểm tra bản cuối, không gọi API.
4. Commit/push source, bốn artifacts, TEAM và reports; lấy SHA bằng `git rev-parse HEAD` và mở đúng commit trên GitHub trước khi gửi.
5. SUBMISSION yêu cầu tên `K4-L3-DAY24-TenNhom-Eval-Guard`; tên theo nhóm hiện tại là `K4-L3-DAY24-SoloLeveling-Eval-Guard`. Repo hiện dùng tên khác; đối chiếu hướng dẫn coach/đổi tên theo mẫu trước nộp.

Không cần chạy lại setup/A/B khi chỉ đổi guard. Nếu sinh lại answers thì A/B phải chạy lại vì nguồn answer/candidate A đổi.
Không chạy integration live thêm sau batch C để tránh trả phí lặp lại.

## Quality và giới hạn

Ngưỡng bắt buộc C là 15/20, bonus 18/20 vẫn yêu cầu clean 8/8. Budget 500 ms là target; số đo vượt target vẫn ghi thật.
CI faithfulness ≥0.75/avg ≥0.65 là đề xuất blueprint, không phải quality gate đã triển khai.
Pipeline hiện có retrieval/generation yếu ở multi-hop; báo cáo nêu bằng chứng và hướng cải tiến, không đổi corpus/test để làm eval dễ hơn.
Cache resume answers chưa gắn fingerprint corpus/provider đầy đủ: nếu thay corpus/model/provider/code, dùng `--refresh-cache` thay vì checkpoint cũ.
Deadline trong README và tài liệu nộp bài có mốc khác nhau; dùng thông báo coach, chưa tự chốt deadline.
CP3 đã đạt qua batch live cuối và checker xác nhận; thời gian vượt target không bị sửa để tạo kết quả đạt giả.

## Kết quả kiểm chứng sau audit

- `python -m pip check`: No broken requirements found.
- `python -m pytest tests/ -q`: 102 passed, 3 integration tests deselected; không gọi API.
- Presidio thật trên máy: 8/8 clean inputs không chứa các entity PII của lab; bốn inputs chứa giá trị PII mẫu vẫn phát hiện CCCD/VN phone/email.
- `scripts/check_lab.py`: TEAM, ba reports, source, answers và cả ba artifacts A/B/C pass, 0 failed checks.
- Không chạy thêm batch live trong audit; batch C cuối do người thực hiện chạy thật.
