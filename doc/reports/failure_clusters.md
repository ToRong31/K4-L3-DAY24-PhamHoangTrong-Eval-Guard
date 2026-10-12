# Phân tích lỗi Phase A

Nhóm: PhamHoangTrong. Người phụ trách: Phạm Hoàng Trọng — 2A202602765.
Nguồn: `artifacts/ragas_50q.json`; timestamp UTC: 2026-10-12T07:48:53.908454+00:00.
50 answers gồm 50 LLM và 0 extractive fallback.
Generation: openai/gpt-4o-mini. Evaluator: BAAI/bge-m3, openai/gpt-4o-mini.
Embedding evaluator chạy local; LLM evaluator chạy qua API được cấu hình. Answer, contexts và reference tách biệt.

## Điểm theo distribution

| Metric | factual (20) | multi_hop (20) | adversarial (10) |
| --- | --- | --- | --- |
| faithfulness | 0.833333 | 0.491667 | 0.750000 |
| answer_relevancy | 0.785042 | 0.615956 | 0.726342 |
| context_precision | 0.920833 | 0.933333 | 0.983333 |
| context_recall | 0.833333 | 0.745833 | 0.683333 |
| avg_score | 0.843136 | 0.696697 | 0.785752 |

Avg toàn bộ: 0.773084; faithfulness toàn bộ: 0.680000.

## Bottom 10 từ Task 3

| Rank | ID | Câu hỏi | Nhóm | Avg | Worst metric | Diagnosis | Suggested fix |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 5 | Muốn mua thiết bị trị giá 55 triệu cần ai phê duyệt? | factual | 0.000000 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 2 | 39 | So sánh yêu cầu mật khẩu giữa policy v1.0 và v2.0 về độ dài tối thiểu, thời hạn đổi và MFA. | multi_hop | 0.125000 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 3 | 30 | So sánh quyền lợi bảo hiểm giữa nhân viên thử việc và nhân viên chính thức. | multi_hop | 0.333333 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 4 | 21 | Một nhân viên Senior có 9 năm thâm niên được nghỉ bao nhiêu ngày phép năm và lương trong khoảng nào? | multi_hop | 0.375000 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 5 | 33 | Nhân viên Manager có thâm niên 12 năm: tổng phụ cấp hàng tháng và số ngày phép năm theo v2024 là bao nhiêu? | multi_hop | 0.375000 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 6 | 50 | Nhân viên Manager có thể dùng VPN cá nhân (như NordVPN) khi WFH để tăng bảo mật thêm không? | adversarial | 0.375000 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 7 | 48 | Nhân viên thử việc có được hưởng bảo hiểm sức khỏe PVI không? | adversarial | 0.416667 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 8 | 9 | Nam nhân viên được nghỉ bao nhiêu ngày khi vợ sinh con? | factual | 0.500000 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 9 | 7 | Nghỉ phép không lương 20 ngày cần ai phê duyệt? | factual | 0.616916 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 10 | 24 | Nhân viên tạm ứng 15 triệu, sau 20 ngày mới thanh toán. Bị phạt bao nhiêu? | multi_hop | 0.633671 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |

Diagnosis và suggested_fix được giữ nguyên từ JSON, không sửa điểm hoặc thứ tự để tăng kết quả.
Nhãn diagnostic tree là hướng điều tra; faithfulness thấp ở câu từ chối không tự chứng minh hallucination.

## Đối chiếu answer, contexts và reference

### Câu 5

Câu hỏi: Muốn mua thiết bị trị giá 55 triệu cần ai phê duyệt?

Answer: Cần giám đốc phòng ban phê duyệt.

Reference: Đơn hàng trên 50.000.000 VNĐ cần Tổng Giám đốc (CEO) phê duyệt.

- Context 1 (trích): Tài liệu nguồn là mua_sam.md, chủ đề là quy định về phê duyệt đơn hàng.

## Thẩm quyền phê duyệt
| Giá trị đơn hàng | Người phê duyệt |
|-------------------|-----------------|
| Dưới **5.000.000 VNĐ** | Trưởng phòng (Manager) |
| Từ **5.000.000 - 50.000.000 VNĐ** | Giám đốc phòng ban (Director) |

Tóm tắt: Đoạn văn trình bày thẩm quyền phê duyệt đơn hàng dựa trên giá trị của đơn hàng. Có hai mức phê duyệt: Trưởng phòng phê duyệt cho đơn hàng dưới 5 triệu VNĐ và Giám đốc phòng ban cho đơn hàng từ

- Context 2 (trích): Tài liệu nguồn là 'tam_ung.md' nói về quy trình phê duyệt tạm ứng trong tổ chức.

## Phê duyệt
Tạm ứng dưới 5.000.000 VNĐ: trưởng phòng phê duyệt. Từ 5.000.000 VNĐ trở lên: cần thêm phê duyệt Kế toán trưởng.

Tóm tắt: Đoạn văn quy định quy trình phê duyệt tạm ứng trong tổ chức. Tạm ứng dưới 5.000.000 VNĐ do trưởng phòng phê duyệt, trong khi từ 5.000.000 VNĐ trở lên cần có thêm phê duyệt của kế toán trưởng.

Câu hỏi có thể trả lời:
Ai là người phê duyệt tạm ứng dưới 5.000.000 VNĐ?
Cần phê duyệt c

- Context 3 (trích): Tài liệu từ 'mua_sam.md' nêu về quy định mua sắm thiết bị CNTT.

## Lưu ý đặc biệt
Mua sắm thiết bị CNTT (laptop, server, phần mềm) cần có xác nhận của phòng CNTT về cấu hình kỹ thuật trước khi đề xuất. Đơn hàng khẩn cấp có thể bỏ qua yêu cầu 3 báo giá nhưng phải có giải trình bằng văn bản.

Tóm tắt: Mua sắm thiết bị CNTT cần xác nhận cấu hình kỹ thuật từ phòng CNTT trước khi đề xuất. Đơn hàng khẩn cấp có thể bỏ qua yêu cầu 3 báo giá nhưng phải có giải trình bằng văn bản.

Câu hỏi có thể trả lời
### Câu 39

Câu hỏi: So sánh yêu cầu mật khẩu giữa policy v1.0 và v2.0 về độ dài tối thiểu, thời hạn đổi và MFA.

Answer: Không tìm thấy.

Reference: v1.0 (đã hết hiệu lực): tối thiểu 8 ký tự, đổi mỗi 90 ngày, không yêu cầu MFA. v2.0 (hiện hành): tối thiểu 12 ký tự, đổi mỗi 120 ngày, MFA bắt buộc cho tất cả: email, VPN và hệ thống nội bộ.

- Context 1 (trích): Tài liệu nguồn là mat_khau_v1.md, chủ đề là chính sách mật khẩu.

# Chính sách mật khẩu (Phiên bản cũ)
> Phiên bản: 1.0 | Ngày hiệu lực: 01/01/2022 | Phòng ban: CNTT | Trạng thái: ĐÃ THAY THẾ bởi v2.0

Tóm tắt: Đoạn văn thể hiện thông tin về chính sách mật khẩu phiên bản cũ 1.0. Chính sách đã được thay thế bởi phiên bản 2.0.

Câu hỏi có thể trả lời:
Chính sách mật khẩu phiên bản cũ có hiệu lực từ khi nào?
Phiên bản cũ của chính sách mật khẩu thuộc phòng ban nào?
Chính sách mật khẩu phiên bản 1.0

- Context 2 (trích): Tài liệu nguồn: mat_khau_v2.md, chủ đề: yêu cầu mật khẩu.

## Yêu cầu mật khẩu
Mật khẩu phải có tối thiểu **12 ký tự**, bao gồm ít nhất 1 chữ hoa, 1 chữ thường, 1 số và 1 ký tự đặc biệt (!@#$%^&*). Khuyến khích sử dụng passphrase dài hơn 16 ký tự.

Tóm tắt: Mật khẩu cần có ít nhất 12 ký tự với các yêu cầu cụ thể về loại ký tự. Việc sử dụng passphrase dài hơn 16 ký tự được khuyến khích.

Câu hỏi có thể trả lời:
Mật khẩu tối thiểu cần có bao nhiêu ký tự?
Mật khẩu cần bao gồm những loại ký tự nào?


- Context 3 (trích): Tài liệu nguồn là mat_khau_v1.md về chính sách mật khẩu.

## Lưu ý
Chính sách này đã được thay thế bởi Chính sách mật khẩu v2.0 từ ngày 01/07/2024. Vui lòng tham khảo phiên bản mới để biết quy định hiện hành.

Tóm tắt: Chính sách mật khẩu v1 đã được thay thế bởi chính sách mật khẩu v2.0 từ ngày 01/07/2024. Người dùng cần tham khảo phiên bản mới để biết quy định hiện hành.

Câu hỏi có thể trả lời:
Chính sách mật khẩu v1 đã được thay thế vào ngày nào?
Phiên bản mới của chính sách mật khẩu có tên g
### Câu 30

Câu hỏi: So sánh quyền lợi bảo hiểm giữa nhân viên thử việc và nhân viên chính thức.

Answer: Không tìm thấy.

Reference: Nhân viên thử việc: chỉ được tham gia BHXH bắt buộc, KHÔNG được hưởng gói bảo hiểm sức khỏe PVI. Nhân viên chính thức: được hưởng BHXH + gói PVI hạn mức 200 triệu/năm (nội trú, ngoại trú, nha khoa).

- Context 1 (trích): Tài liệu nguồn về quy định nghỉ phép của nhân viên thử việc.

Nhân viên thử việc **KHÔNG được nghỉ phép năm**. Trường hợp cần nghỉ việc riêng, nhân viên thử việc phải xin nghỉ không lương và được trưởng phòng phê duyệt. Nhân viên thử việc được tham gia bảo hiểm xã hội bắt buộc nhưng chưa được hưởng gói bảo hiểm sức

Tóm tắt: Nhân viên thử việc không có quyền nghỉ phép năm và nếu muốn nghỉ việc riêng, cần xin nghỉ không lương và được trưởng phòng phê duyệt. Họ cũng được tham gia bảo hiểm xã hội n

- Context 2 (trích): Tài liệu nguồn từ thu_viec.md nói về chế độ lương trong thời gian thử việc.

## Lương thử việc
Nhân viên thử việc được nhận **85% mức lương** của cấp bậc tương ứng theo bảng lương công ty. Phụ cấp ăn trưa được áp dụng đầy đủ từ ngày đầu tiên.

Tóm tắt: Nhân viên thử việc nhận 85% mức lương của cấp bậc tương ứng và được hưởng phụ cấp ăn trưa từ ngày đầu. Chế độ lương và phúc lợi áp dụng trong thời gian thử việc được quy định rõ ràng.

Câu hỏi có thể trả lời:
Mức lương thử việc là bao nhiêu phần t

- Context 3 (trích): Tài liệu từ bang_luong_2024.md nêu rõ mức lương và chính sách lương thử việc tại công ty.

| Manager (M1-M2) | 45.000.000 - 70.000.000 |

## Lương thử việc
Nhân viên trong thời gian thử việc được nhận **85% lương** của cấp bậc tương ứng. Sau khi hoàn thành thử việc, lương được điều chỉnh lên 100% kể từ ngày ký hợp đồng chính thức.

Tóm tắt: Đoạn văn cung cấp thông tin về mức lương của vị trí Manager tại công ty là từ 45.000.000 đến 70.000.000 đồng. Nhân viên trong thời gian thử việc nhận 85% lươ
### Câu 48

Câu hỏi: Nhân viên thử việc có được hưởng bảo hiểm sức khỏe PVI không?

Answer: Không tìm thấy.

Reference: KHÔNG. Nhân viên thử việc chưa được hưởng gói PVI. Chỉ được tham gia BHXH bắt buộc. Đây là negation trap — pipeline hay nhầm vì tài liệu PVI không đề cập rõ exclusion.

- Context 1 (trích): Tài liệu nguồn về quy định nghỉ phép của nhân viên thử việc.

Nhân viên thử việc **KHÔNG được nghỉ phép năm**. Trường hợp cần nghỉ việc riêng, nhân viên thử việc phải xin nghỉ không lương và được trưởng phòng phê duyệt. Nhân viên thử việc được tham gia bảo hiểm xã hội bắt buộc nhưng chưa được hưởng gói bảo hiểm sức

Tóm tắt: Nhân viên thử việc không có quyền nghỉ phép năm và nếu muốn nghỉ việc riêng, cần xin nghỉ không lương và được trưởng phòng phê duyệt. Họ cũng được tham gia bảo hiểm xã hội n

- Context 2 (trích): Tài liệu nguồn: bao_hiem_suc_khoe.md, chủ đề: bảo hiểm sức khỏe cho nhân viên.

## Bảo hiểm cho nhân viên
Công ty cung cấp gói bảo hiểm sức khỏe toàn diện qua **PVI Insurance** cho tất cả nhân viên chính thức. Hạn mức bảo hiểm: **200.000.000 VNĐ/năm** bao gồm nội trú, ngoại trú và nha khoa.

Tóm tắt: Công ty cung cấp gói bảo hiểm sức khỏe toàn diện cho nhân viên qua PVI Insurance với hạn mức 200.000.000 VNĐ/năm. Gói bảo hiểm bao gồm nội trú, ngoại trú và nha khoa.

Câu hỏi có thể trả lời:
Ai là 

- Context 3 (trích): Tài liệu nguồn: bảo hiểm sức khỏe, hướng dẫn về thẻ bảo hiểm PVI.

Nhân viên xuất trình thẻ bảo hiểm PVI tại các bệnh viện/phòng khám trong danh sách liên kết. Trường hợp khám ngoài danh sách, nhân viên thanh toán trước và nộp hồ sơ bồi hoàn trong vòng 30 ngày. Thời gian xử lý bồi hoàn: 10-15 ngày làm việc.

Tóm tắt: Nhân viên cần xuất trình thẻ bảo hiểm PVI tại các cơ sở y tế liên kết. Nếu khám ở nơi không nằm trong danh sách, nhân viên phải thanh toán trước và có thời gian bồi hoàn là 10-15 ng
### Câu 50

Câu hỏi: Nhân viên Manager có thể dùng VPN cá nhân (như NordVPN) khi WFH để tăng bảo mật thêm không?

Answer: Không tìm thấy.

Reference: KHÔNG. Chính sách VPN v1.3 cấm sử dụng VPN cá nhân (NordVPN, ExpressVPN) trong mạng công ty. Bắt buộc dùng VPN WireGuard của công ty. Đây là policy contradiction trap — câu hỏi nghe hợp lý nhưng vi phạm chính sách.

- Context 1 (trích): Tài liệu nguồn: vpn_truy_cap.md, chủ đề: Quy định sử dụng VPN.

## Quy định sử dụng
- Không chia sẻ thông tin đăng nhập VPN
- Ngắt kết nối VPN khi không sử dụng
- Không sử dụng VPN cá nhân (NordVPN, ExpressVPN) trong mạng công ty
- Phiên VPN tự động ngắt sau 12 giờ, cần đăng nhập lại

Tóm tắt: Đoạn văn trình bày quy định về việc sử dụng VPN trong công ty, bao gồm không chia sẻ thông tin đăng nhập và yêu cầu ngắt kết nối khi không sử dụng. Ngoài ra, VPN cá nhân không được phép sử dụng trong mạng 

- Context 2 (trích): Tài liệu về quy định bảo mật thông tin của công ty liên quan đến xác thực đa yếu tố.

## Xác thực đa yếu tố (MFA)
Tất cả nhân viên **bắt buộc** kích hoạt MFA cho tài khoản email, VPN và các hệ thống nội bộ. Phương thức MFA được chấp nhận: ứng dụng Authenticator (ưu tiên), SMS OTP, hoặc YubiKey.

Tóm tắt: Nhân viên được yêu cầu kích hoạt xác thực đa yếu tố (MFA) cho tài khoản email, VPN và các hệ thống nội bộ. Các phương thức MFA được chấp nhận bao gồm ứng dụng Authenticator, SMS OTP hoặc YubiKey

- Context 3 (trích): Tài liệu nguồn: vpn_truy_cap.md, chủ đề: Giao thức kết nối VPN.

## Giao thức kết nối
Công ty sử dụng **WireGuard VPN** với mã hóa xác thực **ChaCha20-Poly1305**. Tất cả kết nối từ xa bắt buộc qua VPN. Nhân viên tải cấu hình VPN từ IT Portal hoặc liên hệ helpdesk@cty.vn.

Tóm tắt: Công ty sử dụng WireGuard VPN với mã hóa ChaCha20-Poly1305 cho tất cả các kết nối từ xa. Nhân viên có thể tải cấu hình VPN từ IT Portal hoặc liên hệ với helpdesk để được hỗ trợ.

Câu hỏi có thể trả lời:
Công ty sử dụng

Trong lần chạy hiện tại, ID 5 trả Giám đốc phòng ban trong khi reference yêu cầu CEO cho giá trị trên 50 triệu.
Context chứa hàng dưới 5 triệu và 5–50 triệu nhưng không có hàng trên 50 triệu: cần lấy đủ bảng, sau đó buộc generation đối chiếu ngưỡng thay vì suy rộng hàng thiếu.
ID 39 đòi so sánh hai phiên bản trên ba tiêu chí; contexts chưa phủ đủ độ dài/thời hạn/MFA của cả hai bản, answer từ chối.
ID 30 đòi quyền lợi hai nhóm nhưng context về thử việc bị cắt giữa câu và retrieval còn lấy đoạn lương; cần lấy cả policy bảo hiểm.
Đây là bằng chứng thiếu độ phủ retrieval ở các câu nhiều điều kiện, cùng với hành vi generation chưa giải thích phần thiếu.
ID 48 và 50 là kiểm tra phủ định/ngoại lệ: phải phân biệt BHXH với PVI và VPN công ty với VPN cá nhân; không dùng chức danh làm ngoại lệ nếu policy không cho phép.

## Matrix và nhóm yếu nhất

| Worst metric | factual | multi_hop | adversarial |
| --- | --- | --- | --- |
| faithfulness | 4 | 15 | 3 |
| answer_relevancy | 12 | 1 | 2 |
| context_precision | 2 | 0 | 0 |
| context_recall | 2 | 4 | 5 |

Matrix đếm worst_metric của mọi câu, không coi 50 câu đều là failures; tổng các cột là 20/20/10.
Nhóm yếu nhất theo mean: multi_hop.
Insight lưu trong JSON: Distribution 'multi_hop' có điểm trung bình thấp nhất (0.6967). Metric 'faithfulness' là điểm yếu chủ đạo với 22 câu. Gợi ý khắc phục: Tighten system prompt, lower temperature.
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
