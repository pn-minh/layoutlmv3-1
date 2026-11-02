BÁO CÁO TIẾN ĐỘ TUẦN - KHÓA LUẬN TỐT NGHIỆP

Kính gửi: TS. Phạm Thị Quỳnh Trang
Sinh viên thực hiện: Phạm Nhật Minh (Ngành Hệ thống Thông tin - VNU-UET)
Đề tài: Research on Enhancing Vision-Language Model for Document Key Information Extraction
Thời gian: 02/11/2026

Kính gửi Cô Trang,

Em xin phép gửi Cô bản tóm tắt nhanh về tiến độ nghiên cứu và các nội dung em vừa hoàn thành cho mô hình khóa luận tuần này:

1. Tái cấu trúc và chuẩn hóa toàn bộ sơ đồ kiến trúc mô hình (Draw.io & JPEG)
Dựa trên góp ý về việc sơ đồ trước còn bị chồng chéo các khối và lạm dụng công thức toán, em đã xây dựng công cụ trích xuất trực tiếp từ mã nguồn PyTorch của mô hình trong thư mục layoutlmv3/ để tái thiết kế lại toàn bộ sơ đồ kiến trúc:
- Lược bỏ hoàn toàn nhánh Gated Late Fusion: Theo đúng thực nghiệm mới nhất, cơ chế phân loại trực tiếp trên vector đại diện token sau khi hòa trộn ngữ cảnh dòng đạt độ chính xác cao hơn và giảm đáng kể độ trễ tính toán.
- Trực quan hóa chi tiết module Intra-Line Boundary Loss: Thay vì viết các công thức toán dài dòng, em đã chuyển đổi hoàn toàn sang biểu diễn trực quan bằng hình khối và đường nét. Sơ đồ minh họa rõ ràng luồng trích xuất cặp từ liền kề [h_i ; h_{i+1}] trên cùng dòng đọc, đưa qua mạng MLP và so khớp với nhãn chuyển tiếp trực quan (nối liền nét màu xanh cho Target = 0 khi cùng thuộc một thực thể, và đường vạch đứt màu đỏ cho Target = 1 khi chuyển sang thực thể mới hoặc nhãn nền).
- Bổ sung module Cross-Modal Contrastive Loss: Thể hiện trực quan nhánh liên kết đặc trưng đa phương thái giữa vector token văn bản và patch hình ảnh tương ứng thông qua hàm InfoNCE (với biểu tượng mũi tên kéo PULL cho cặp tương ứng và đẩy PUSH cho các patch gây nhiễu), giúp ngăn chặn hiện tượng trôi dạt đặc trưng hình ảnh khi fine-tune.
- Tối ưu hóa bố cục không gian: Toàn bộ các khối hộp, container và mũi tên kết nối được căn chỉnh tọa độ tự động, đảm bảo khoảng cách thông thoáng, hoàn toàn không bị chồng đè (overlap) chữ hay viền. Sơ đồ xuất ra định dạng chuẩn .drawio tương thích với app.diagrams.net và file ảnh JPEG độ phân giải cao 300 DPI.

2. Thống kê và trực quan hóa phân bố dữ liệu FUNSD và CORD
Em đã hoàn thành phần thống kê định lượng chi tiết cho 2 tập dữ liệu phục vụ báo cáo:
- Tập FUNSD: 199 biểu mẫu hành chính scan thực tế (149 train, 50 test), gồm 9.707 thực thể ngữ nghĩa với 31.485 từ thuộc 7 nhãn IOB2 (phân bố nhãn: QUESTION chiếm 44.2%, ANSWER chiếm 33.1%, HEADER chiếm 11.8%, OTHER chiếm 10.9%).
- Tập CORD: 1.000 hóa đơn bán lẻ in nhiệt từ Indonesia (800 train, 100 val, 100 test), gồm 61 nhãn IOB2 thuộc 5 nhóm lớn (menu, total, sub_total, void_menu, etc.).

3. Tiến độ thực nghiệm và phân tích lỗi
- Kết quả chạy trên 3 random seeds (Seed 42, 1337, 2024): Bản nâng cao đạt 92.68% F1 trên FUNSD (tăng +2.37% so với LayoutLMv3 base) và 97.79% F1 trên CORD (tăng +1.28% F1).
- Phân tích chi tiết lỗi ranh giới: Cơ chế giám sát ranh giới theo dòng kết hợp ngữ cảnh dòng giúp giảm 36.6% lỗi sai lệch ranh giới thực thể và giảm 31.8% lỗi sáp nhập hai trường thông tin cạnh nhau trên cùng một dòng.

4. Đường dẫn xem trực tiếp tài liệu cập nhật:
- Sơ đồ kiến trúc mô hình (File Draw.io gốc):
  https://github.com/pn-minh/layoutlmv3-1/blob/documentation/Model_Architecture_Diagram.drawio
- Sơ đồ kiến trúc mô hình (Ảnh JPEG độ phân giải cao):
  https://github.com/pn-minh/layoutlmv3-1/blob/documentation/model_architecture.jpeg
- Sơ đồ kiến trúc mô hình (Bản vector PDF):
  https://github.com/pn-minh/layoutlmv3-1/blob/documentation/Model_Architecture_Diagram.pdf
- Khóa luận và mã nguồn trên GitHub:
  https://github.com/pn-minh/layoutlmv3-1

Em gửi Cô bản báo cáo tiến độ tuần này và rất mong tiếp tục nhận được những góp ý, hướng dẫn của Cô ạ.

Em cảm ơn Cô nhiều ạ!
Sinh viên,
Phạm Nhật Minh
