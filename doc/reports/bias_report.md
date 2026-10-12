# Đánh giá LLM Judge Phase B

Nhóm: PhamHoangTrong. Người phụ trách: Phạm Hoàng Trọng — 2A202602765.
Nguồn: `artifacts/judge_results.json`; timestamp UTC: 2026-10-12T07:50:34.676555+00:00.
Generation: openai/gpt-4o-mini; Judge: openai/gpt-4o-mini.

## Năm cặp và hai lượt

A lấy từ `artifacts/answers_50q.json:answer`; B lấy từ `fixtures/human_labels_10q.json:model_answer`;
reference lấy từ `fixtures/test_set_50q.json:ground_truth`. IDs cố định 1, 5, 12, 21, 41.

| ID | Answer A | Answer B | Winner 1 | Winner 2 quy về gốc | Final | Consistent | Scores 1 | Scores 2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Nhân viên được nghỉ 3 ngày làm việc khi kết hôn. | Nhân viên được nghỉ 3 ngày làm việc có lương khi kết hôn. | B | B | B | True | {"A": 0.8, "B": 1.0} | {"A": 0.8, "B": 1.0} |
| 5 | Cần giám đốc phòng ban phê duyệt. | Cần Giám đốc phòng ban phê duyệt. | tie | tie | tie | True | {"A": 0.0, "B": 0.0} | {"A": 0.0, "B": 0.0} |
| 12 | Thưởng Tết tối thiểu cho nhân viên chính thức có từ 6 tháng trở lên là 1 tháng lương. | Nhân viên được thưởng Tết tối thiểu 1 tháng lương. | A | tie | tie | False | {"A": 1.0, "B": 0.7} | {"A": 1.0, "B": 1.0} |
| 21 | Không tìm thấy. | Được nghỉ 18 ngày phép (15 cơ bản + 3 thâm niên). Lương Senior từ 20 đến 35 triệu. | B | B | B | True | {"A": 0.0, "B": 1.0} | {"A": 0.0, "B": 1.0} |
| 41 | Nhân viên chính thức được hưởng 15 ngày phép năm có lương. | Nhân viên được nghỉ 12 ngày phép năm. | A | A | A | True | {"A": 1.0, "B": 0.0} | {"A": 1.0, "B": 0.3} |

Reasoning lượt 2 dưới đây giữ nguyên nhãn A/B trong prompt đã hoán đổi. Winner và scores trong bảng đã quy về A/B gốc.

- ID 1, lượt 1: Answer B cung cấp thông tin chính xác và đầy đủ về việc nghỉ có lương, trong khi Answer A thiếu thông tin về việc này.
- ID 1, lượt 2: Answer A cung cấp thông tin đầy đủ và chính xác về việc nghỉ có lương, trong khi Answer B thiếu thông tin về lương.

- ID 5, lượt 1: Cả hai câu trả lời đều không chính xác vì đều đưa ra thông tin sai về người phê duyệt. Tuy nhiên, về sự khác biệt trong cú pháp thì không có ý nghĩa quan trọng.
- ID 5, lượt 2: Cả hai câu trả lời đều không chính xác vì đều đề cập đến Giám đốc phòng ban thay vì Tổng Giám đốc (CEO).

- ID 12, lượt 1: Answer A cung cấp đầy đủ thông tin về mức thưởng cụ thể cho nhân viên có từ 6 tháng trở lên, trong khi Answer B chỉ đưa ra một câu ngắn gọn nhưng thiếu phần cụ thể về điều kiện.
- ID 12, lượt 2: Cả hai câu trả lời đều chính xác và đầy đủ thông tin, mô tả cùng một nội dung với sự súc tích tương đương.

- ID 21, lượt 1: Answer B cung cấp thông tin chính xác về số ngày phép và khoảng lương cho nhân viên Senior theo chính sách tham chiếu, trong khi Answer A không cung cấp thông tin nào.
- ID 21, lượt 2: Answer A chính xác và đầy đủ thông tin theo chính sách tham chiếu, trong khi Answer B không cung cấp thông tin nào.

- ID 41, lượt 1: Answer A cung cấp thông tin chính xác theo chính sách v2024, trong khi Answer B đã lỗi thời và không chính xác.
- ID 41, lượt 2: Answer B cung cấp thông tin chính xác theo chính sách 2024, trong khi Answer A đưa ra thông tin đã lỗi thời.

## Position và verbosity

Position inconsistency: 1/5 = 20.0%.
ID 12 là case bất nhất: lượt đầu A thắng vì diễn đạt đủ điều kiện, lượt sau tie. Consensus trả tie thay vì ép chọn.
ID 5 tie nhưng cả hai answer đều sai người phê duyệt; tie không phải nhãn chất lượng tốt.
ID 21 và 41 nhất quán sau đổi vị trí, theo độ đầy đủ và đúng policy hiện hành.
Verbosity win rate: 100.0%; details: {"a_wins_a_longer": 1, "b_wins_b_longer": 2, "total_decisive": 3}.
Ba decisive cases câu dài thắng cũng có khác biệt nội dung: nghỉ có lương ở ID 1, có câu trả lời thay vì từ chối ở ID 21,
đúng v2024 ở ID 41. Tỷ lệ này là dấu hiệu cần kiểm tra, chưa chứng minh độ dài gây thiên vị.

## Calibration trên đúng answer nguồn

Binary helper nhận question, model_answer gốc và reference; không nhận human_label/human_note.
Nhãn human chỉ dùng sau khi chấm để đối chiếu, không chuyển winner A/B thành nhãn 0/1.

| ID | Model answer được cấp | Judge | Human | Agree | Reasoning |
| --- | --- | --- | --- | --- | --- |
| 1 | Nhân viên được nghỉ 3 ngày làm việc có lương khi kết hôn. | 1 | 1 | True | Câu trả lời chính xác và đầy đủ theo thông tin trong reference, không thiếu ý thiết yếu. |
| 5 | Cần Giám đốc phòng ban phê duyệt. | 0 | 0 | True | Câu trả lời sai vì yêu cầu phê duyệt cho đơn hàng trên 50 triệu là từ Tổng Giám đốc, không phải Giám đốc phòng ban. |
| 12 | Nhân viên được thưởng Tết tối thiểu 1 tháng lương. | 1 | 1 | True | Câu trả lời chính xác theo thông tin trong reference, nêu rõ điều kiện và mức thưởng cho nhân viên chính thức có từ 6 tháng trở lên. |
| 21 | Được nghỉ 18 ngày phép (15 cơ bản + 3 thâm niên). Lương Senior từ 20 đến 35 triệu. | 1 | 1 | True | Câu trả lời chính xác theo reference, nêu rõ số ngày phép và khoảng lương cho nhân viên Senior có 9 năm thâm niên. |
| 23 | Hoàn trả 25 triệu vì chưa đủ 1 năm cam kết. | 1 | 1 | True | Câu trả lời chính xác theo reference, nêu rõ nhân viên phải hoàn trả 25 triệu vì chưa đủ 1 năm cam kết. |
| 29 | Trưởng phòng phê duyệt. Phạt 2% tháng trên 8 triệu. | 0 | 0 | True | Câu trả lời sai vì không đề cập đến sự cần thiết có sự phê duyệt của Kế toán trưởng bên cạnh Trưởng phòng. Ngoài ra, phí phạt được tính cho quá hạn 15 ngày, không phải 30 ngày như trong câu trả lời. |
| 33 | Phép: 19 ngày. Phụ cấp: 1.500.000 VNĐ/tháng. | 1 | 1 | True | Câu trả lời cung cấp đúng tổng số ngày phép và tổng phụ cấp hàng tháng theo thông tin trong tài liệu tham khảo. |
| 41 | Nhân viên được nghỉ 12 ngày phép năm. | 0 | 0 | True | Câu trả lời sai vì nó dựa trên chính sách cũ (v2023) thay vì chính sách hiện hành (v2024) là 15 ngày phép năm. |
| 46 | Nhân viên thử việc không được nghỉ phép năm và phải xin nghỉ không lương nếu cần. | 1 | 1 | True | Câu trả lời chính xác theo reference, nêu rõ rằng nhân viên thử việc không được nghỉ phép năm và phải xin nghỉ không lương nếu cần, đồng thời không bỏ qua điều kiện cần có sự phê duyệt của trưởng phòng. |
| 50 | Được, miễn là đảm bảo kết nối an toàn. | 0 | 0 | True | Câu trả lời sai vì khẳng định rằng nhân viên Manager có thể dùng VPN cá nhân khi WFH, trong khi chính sách rõ ràng cấm việc này. |

Observed agreement p_o = 1.000000. Chance agreement p_e = 0.520000 từ tần suất hai lớp.
Cohen's kappa = (p_o - p_e)/(1 - p_e) = 1.000000.
Trong 10 câu này judge và human đồng thuận hoàn toàn. Kết quả vượt mốc bonus 0.6, không chứng minh judge đúng với mọi dữ liệu.

## Giới hạn và cách dùng

Chỉ 5 cặp và 10 nhãn, một cấu hình model/prompt; cần thêm mẫu và nhiều lượt độc lập để đánh giá độ ổn định.
Một số reasoning có diễn giải quá mức dù nhãn khớp: ở ID 12 model_answer không nêu lại điều kiện 6 tháng;
ID 46 không nêu lại việc trưởng phòng phê duyệt. Không coi reasoning là chứng cứ policy nếu không đối chiếu reference.
Giữ swap-and-average khi dùng pairwise; dùng binary calibration riêng và review người với case bất nhất/nhạy cảm.
Nếu thay answers nguồn, phải chạy lại B; nếu chỉ sửa validation cho malformed JSON thì artifacts hợp lệ hiện tại vẫn sử dụng được.
