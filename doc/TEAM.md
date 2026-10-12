# Nhóm thực hiện K4 Track 3B

Tên nhóm: PhamHoangTrong

Repo chung: https://github.com/ToRong31/K4-Track-3B-Day24-PhamHoangTrong-2A202602765-EvalGuard

Trưởng nhóm/người thực hiện và nộp: Phạm Hoàng Trọng — 2A202602765.

Ngày thực nghiệm trong artifacts: 12/10/2026, Asia/Ho_Chi_Minh (UTC+07:00).
Deadline theo hướng dẫn nộp bài người thực hiện cung cấp: 11:59 AM ngày 13/10/2026,
Asia/Ho_Chi_Minh (UTC+07:00). Áp dụng điều chỉnh của key coach nếu có;
kênh nộp và chính sách AI lấy từ thông báo lớp.

Commit dùng để chấm: `c72cf86daef6e222dbb9ce7e4554b1839b9fa816`.
SHA do người thực hiện cung cấp từ `git rev-parse HEAD`, gồm source, artifacts và báo cáo của nhóm PhamHoangTrong.
Commit bổ sung dòng ghi nhận SHA này chỉ cập nhật thông tin bàn giao; khi nộp gửi link repo kèm SHA dùng để chấm ở trên.

## Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò / công việc thực tế | Bằng chứng |
| --- | --- | --- | --- | --- |
| 1 | Phạm Hoàng Trọng | 2A202602765 | Tích hợp module Day 18, chuẩn bị môi trường/Qdrant, chạy setup và batch A/B/C, kiểm tra kết quả; dùng AI hỗ trợ implement/debug và soạn báo cáo | Source m1–m5/phase A–C, bốn JSON trong artifacts, ba báo cáo và lịch sử Git bản cuối |

Người tích hợp/chạy batch/nộp link: Phạm Hoàng Trọng. Lệnh live được người thực hiện chạy trực tiếp; AI không tạo số đo giả.

## Môi trường và chuẩn bị

Windows, Python 3.11.9 trong `.venv`. Phiên bản compiler C++ cài trên máy chưa kiểm kê riêng;
không suy từ dòng MSC của interpreter thành bằng chứng cài Build Tools.
`python -m pip check` trả `No broken requirements found` trong lần audit.
Unit tests offline đã pass; kết quả cụ thể ghi trong kế hoạch hoàn thành, không thay bằng chứng runtime thật.
Qdrant khởi chạy bằng Docker Compose; pipeline đã sinh đủ 50 answers.
Generation/evaluator/judge/guard IDs và timestamps lấy từ từng JSON, không gộp thành một model chung.
BGE-M3 embedding và BGE reranker local theo module RAG; LLM đi qua API/proxy cấu hình của người thực hiện.
RAGAS và NeMo đã có artifacts thực nghiệm. Sau sửa guard, batch C cuối lúc
2026-10-12T08:17:29.017518+00:00 đạt attacks 20/20, clean 8/8, outputs 4/4.
Input-layer P95 là 850.107065 ms, vượt target 500 ms; giữ số thật, không suy ra full-request latency.
Presidio được kiểm tra thực bằng tám clean inputs và bốn inputs chứa PII mẫu, không gọi API.
Hai PDF scan ảnh đã bị loader bỏ qua do không có text layer; OCR chưa triển khai.

## INDIVIDUAL

### PhamHoangTrong-2A202602765

- Phần thực hiện: copy module RAG Day 18, chuẩn bị dependencies/model/Docker, chạy generation và eval A/B/C, gửi lỗi thực tế để sửa, đối chiếu checker. Code tích hợp, guard và báo cáo có AI hỗ trợ.
- Bằng chứng: `artifacts/answers_50q.json`, `ragas_50q.json`, `judge_results.json`, `guard_results.json`, source và báo cáo cùng repo. Chưa tuyên bố bản cuối đã nộp.
- Cách kiểm tra: tests offline dùng SDK/rail mocks; artifacts live do người thực hiện chạy; checker validate schema/counts/hash/statistics. CP3 đã có batch live mới đạt 20/20 attacks, 8/8 clean và 4/4 outputs; checker cuối không còn lỗi.
- Nội dung đã đối chiếu: faithfulness khác recall/precision; worst-metric matrix không phải số câu thất bại; winner A/B khác binary label; swap cần đổi cả scores; latency input layers khác full request.
- Giới hạn: 50/20/8/4 mẫu cố định, model/proxy alias chưa xác nhận snapshot; không suy kappa=1 thành judge đúng tuyệt đối. Budget vượt target và false positives phải ghi số thật.
- AI hỗ trợ: Codex, Antigravity và Codex GPT-6 Luna high hỗ trợ đọc guide, implement/debug, kiểm chứng offline và soạn báo cáo từ JSON. Người thực hiện chạy lệnh live; đề xuất được đối chiếu bằng tests/artifacts/checker, không dùng lời báo hoàn thành làm bằng chứng đã chạy.
- Nguồn: starter Day 24 và năm module từ bài RAG Day 18 của người thực hiện; giữ nguyên fixtures và policy cũ/mới.

## Cập nhật sau khi nộp

Chưa có bằng chứng nộp bài trong phiên hiện tại. Không khai thay đổi hiện tại là cập nhật sau nộp;
nếu sửa sau deadline, ghi commit/thời điểm/lý do và áp dụng quyết định coach.
