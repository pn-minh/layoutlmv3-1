BÁO CÁO NHANH TIẾN ĐỘ KHÓA LUẬN TỐT NGHIỆP

Kính gửi: TS. Phạm Thị Quỳnh Trang
Sinh viên thực hiện: Phạm Nhật Minh (Ngành Hệ thống Thông tin - VNU-UET)
Đề tài: Research on Enhancing Vision-Language Model for Document Key Information Extraction
Thời gian: 02/11/2026

Kính gửi Cô Trang,

Em xin phép gửi Cô bản tóm tắt nhanh về tiến độ nghiên cứu và các nội dung em vừa hoàn thiện cho đề tài khóa luận:

1. Cập nhật và tinh chỉnh mô hình theo thực tế nghiên cứu
- Lược bỏ hoàn toàn nhánh Gated Late Fusion: Trong quá trình thử nghiệm thực tế, cơ chế phân loại trực tiếp trên vector đại diện token sau khi đã được hòa trộn ngữ cảnh dòng tỏ ra hiệu quả, ổn định và nhẹ hơn nhiều về mặt tính toán, nên em đã loại bỏ thành phần này khỏi mô hình.
- Bổ sung thành phần Contrastive Loss (Hàm mất mát tương phản đa phương thái): Em đã triển khai thêm nhánh mất mát này dựa trên InfoNCE giữa vector token văn bản và vector patch ảnh tương ứng với bounding box. Nhánh này giúp neo chặt đặc trưng thị giác với ngữ nghĩa văn bản, ngăn ngừa hiện tượng trôi dạt (representation drift) của nhánh ảnh khi fine-tune trên các tác vụ downstream.
- Chi tiết hóa module Intra-Line Boundary Loss: Em đã diễn giải và trực quan hóa chi tiết cách trích xuất các cặp token liền kề theo từng dòng đọc, đưa qua mạng MLP 2 lớp và giám sát bằng nhãn chuyển tiếp nhị phân (gán nhãn 0 cho hai từ cùng thuộc một thực thể và nhãn 1 cho vị trí ngắt ranh giới giữa các trường thông tin).

2. Bổ sung mô tả trực quan và thống kê 2 tập dữ liệu FUNSD và CORD
Theo góp ý của Cô trong buổi trước, em đã bổ sung vào Chương 4 phần mô tả rất chi tiết về số lượng, loại văn bản và phân bố nhãn thực tế:
- Tập FUNSD: 199 biểu mẫu hành chính scan thực tế (149 train, 50 test), 31.485 từ với 7 nhãn IOB2 thuộc 3 lớp chính (QUESTION, ANSWER, HEADER). Em đã vẽ thêm biểu đồ cột phân bố tỷ lệ nhãn trực tiếp trong bài (Question chiếm 44.2%, Answer chiếm 33.1%, Header chiếm 11.8%, Other chiếm 10.9%).
- Tập CORD: 1.000 hóa đơn bán lẻ in nhiệt từ Indonesia (800 train, 100 val, 100 test), với 61 nhãn IOB2 phân cấp thành 5 nhóm lớn (menu, total, sub_total, void_menu, etc.).

3. Hoàn thiện kết quả thực nghiệm và phân tích lỗi ranh giới
- Báo cáo đầy đủ bảng kết quả chạy trên 3 random seeds (Seed 42, 1337, 2024): Bản nâng cao của em đạt 92.68% F1 trên FUNSD (tăng +2.37% so với LayoutLMv3 base) và 97.79% F1 trên CORD (tăng +1.28% F1).
- Bổ sung bảng phân tích chi tiết lỗi ranh giới: Mô hình giảm được 36.6% lỗi sai lệch ranh giới thực thể và giảm 31.8% lỗi sáp nhập hai trường thông tin khác nhau trên cùng một dòng.
- Viết đầy đủ Chương 5 Kết luận: Thẳng thắn nhìn nhận các hạn chế thực tế (phụ thuộc vào chất lượng OCR đầu vào, khó xử lý tốt các văn bản bị xoay nghiêng hoặc biểu mẫu phi chữ nhật phức tạp) và đề xuất các hướng đi tiếp theo rất cụ thể (học gom cụm bằng đồ thị, chưng cất mô hình nhẹ để chạy thực tế trên thiết bị biên/mobile, và đánh giá mở rộng trên tập hóa đơn tiếng Việt MC-OCR).

4. Sơ đồ kiến trúc mô hình chuẩn hóa vector (HEADS style)
Sơ đồ kiến trúc tổng thể của mô hình được giữ nguyên theo bản vẽ vector chuẩn hóa (phong cách HEADS), thể hiện đầy đủ và mạch lạc luồng xử lý từ Document Input -> HPE -> LayoutLMv3 Backbone -> SCM -> Head phân loại trực tiếp và giám sát đa nhiệm.

5. Đường dẫn xem trực tiếp tài liệu cập nhật:
- Bản thảo Khóa luận tiếng Anh (PDF hoàn chỉnh):
  https://github.com/pn-minh/layoutlmv3-1/blob/documentation/English_Thesis_LayoutLMv3.pdf
- Sơ đồ kiến trúc mô hình (File PDF vector nét cao):
  https://github.com/pn-minh/layoutlmv3-1/blob/documentation/Model_Architecture_Diagram.pdf
- Mã nguồn và toàn bộ tài liệu trên GitHub:
  https://github.com/pn-minh/layoutlmv3-1

Em gửi Cô bản tóm tắt này và rất mong tiếp tục nhận được những góp ý, hướng dẫn của Cô để em hoàn thiện khóa luận tốt hơn ạ.

Em cảm ơn Cô nhiều ạ!
Sinh viên,
Phạm Nhật Minh
