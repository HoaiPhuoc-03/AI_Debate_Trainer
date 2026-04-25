# Thiết kế dataset AI Debate Trainer Debate-CER v1

## 1. Mục tiêu dataset

Dataset được xây dựng để phục vụ hệ thống AI Debate Trainer: sinh phản biện, chấm điểm CER và đưa feedback cải thiện lập luận. Mục tiêu chính của phiên bản v1 là chuẩn hóa schema dữ liệu, kiểm thử pipeline evaluation và chuẩn bị nền cho fine-tuning/QLoRA ở các giai đoạn sau.

## 2. Vì sao cần dataset riêng

AI Debate Trainer không chỉ cần trả lời như chatbot thông thường. Hệ thống cần phản biện lại lập luận của người dùng, phát hiện điểm yếu chính, chấm Claim-Evidence-Reasoning và đưa lời khuyên phù hợp với độ tuổi, trình độ tranh biện và độ khó phiên học. Dataset riêng giúp backend, prompt, parser và evaluation cùng bám vào một contract ổn định.

## 3. Bối cảnh sử dụng trong đồ án

Trong đồ án, dataset này dùng để:

- Kiểm tra output có đúng format Debate-CER hay không.
- Đánh giá chất lượng phản biện và feedback theo các case cố định.
- Chuẩn bị dữ liệu supervised instruction tuning.
- Làm nền cho QLoRA prototype nếu có đủ tài nguyên GPU.

## 4. Input schema

Mỗi sample có trường `input` gồm:

- `topic`: chủ đề tranh biện.
- `stance`: lập trường của người dùng, gồm `support`, `oppose`, `neutral`.
- `difficulty`: độ khó, gồm `basic`, `intermediate`, `advanced`.
- `age_group`: nhóm tuổi, gồm `teen`, `adult`, `senior`.
- `debate_level`: trình độ tranh biện, gồm `basic`, `intermediate`, `advanced`.
- `language`: ngôn ngữ, hiện dùng `vi`.
- `user_argument`: lập luận đầu vào của người dùng.

## 5. Output schema

Trường `output` gồm:

- `rebuttal`: phản biện của AI.
- `cer.claim`: điểm Claim từ 0 đến 10.
- `cer.evidence`: điểm Evidence từ 0 đến 10.
- `cer.reasoning`: điểm Reasoning từ 0 đến 10.
- `cer.total`: trung bình của ba điểm trên, làm tròn 2 chữ số.
- `feedback.strengths`: điểm mạnh.
- `feedback.weaknesses`: điểm yếu.
- `feedback.suggestions`: gợi ý cải thiện.

## 6. Metadata schema

Trường `metadata` gồm:

- `topic_category`: `education`, `technology_ai`, `society`, `environment`, `economy`.
- `argument_quality`: `medium`, `weak_evidence`, `weak_reasoning`, `vague_claim`, `strong`, `too_short`, `off_topic`, `unsafe`.
- `main_weakness`: `claim`, `evidence`, `reasoning`, `safety`.
- `safety_label`: `safe`, `unsafe`, `needs_review`.
- `generation_method`: phương pháp sinh dữ liệu synthetic.

## 7. CER rubric

- Claim 0-10: đánh giá độ rõ ràng, cụ thể và nhất quán của quan điểm chính.
- Evidence 0-10: đánh giá mức độ có ví dụ, số liệu, bằng chứng hoặc căn cứ.
- Reasoning 0-10: đánh giá khả năng liên kết giữa claim và evidence, tính logic và chiều sâu suy luận.
- Total: `round((claim + evidence + reasoning) / 3, 2)`.

## 8. Phân bổ 1000 mẫu

Phân bổ hiện tại theo thống kê dataset:

- Topic category: education 250, technology_ai 250, society 200, environment 150, economy 150.
- Age group: teen 300, adult 500, senior 200.
- Argument quality: medium 250, weak_evidence 200, weak_reasoning 180, vague_claim 120, strong 120, too_short 60, off_topic 40, unsafe 30.

## 9. Các nhóm topic

- `education`: học tập, trường học, phương pháp học.
- `technology_ai`: công nghệ, AI, thiết bị số.
- `society`: xã hội, hành vi, quy định cộng đồng.
- `environment`: môi trường, khí hậu, tiêu dùng bền vững.
- `economy`: kinh tế, việc làm, chi tiêu, chính sách.

## 10. Các loại lập luận

- `medium`: lập luận trung bình, có ý chính nhưng chưa sâu.
- `weak_evidence`: thiếu bằng chứng hoặc ví dụ cụ thể.
- `weak_reasoning`: suy luận chưa chắc, liên kết ý còn yếu.
- `vague_claim`: claim mơ hồ hoặc quá chung.
- `strong`: lập luận tốt, tương đối rõ và có hỗ trợ.
- `too_short`: quá ngắn để phản biện sâu.
- `off_topic`: lệch chủ đề.
- `unsafe`: có yếu tố cần xử lý an toàn.

## 11. Quy trình kiểm tra chất lượng

Quy trình local gồm:

- Validate JSONL hợp lệ.
- Kiểm tra đủ input/output/metadata fields.
- Kiểm tra enum hợp lệ.
- Kiểm tra CER nằm trong 0-10 và `total` đúng công thức.
- Kiểm tra rebuttal, feedback và user argument không rỗng.
- Kiểm tra ID trùng và argument trùng lặp nhiều.
- Thống kê phân bổ để phát hiện lệch dữ liệu.
- Review thủ công một phần, đặc biệt với `unsafe`, `off_topic`, `too_short` và test set.

## 12. Hạn chế

- Synthetic data có thể lặp pattern.
- CER có thể chưa hoàn toàn giống đánh giá của chuyên gia.
- Feedback có thể nhất quán về format nhưng chưa đủ tự nhiên.
- Cần bổ sung gold samples do người review sau.

## 13. Dùng cho giai đoạn 3 evaluation

Giai đoạn 3 có thể dùng `eval_cases_v1.jsonl` làm tập case cố định để kiểm tra:

- Có phản biện hay không.
- Có CER đúng format hay không.
- Có feedback đủ nhóm hay không.
- Output có vượt giới hạn từ không.
- Phản hồi có bám vào focus như evidence, reasoning, safety, age tone không.

## 14. Dùng cho QLoRA sau này

Khi chuyển sang QLoRA, có thể dùng `train.jsonl`, `dev.jsonl`, `test.jsonl` làm split chuẩn. Mỗi sample đã có instruction/input/output, phù hợp để chuyển sang format chat hoặc instruction tuning. Trước khi train thật, cần review dữ liệu, khóa test set và định nghĩa metric evaluation rõ ràng.
