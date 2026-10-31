# Kịch Bản Thuyết Trình Báo Cáo Tiến Độ Tuần (20 Slides)

* **Tên đề tài:** *Nghiên cứu cải tiến mô hình thị giác - ngôn ngữ cho bài toán trích xuất thông tin khóa trên tài liệu* (*Research on Enhancing Vision-Language Model for Document Key Information Extraction*)
* **Tiêu đề báo cáo:** *Báo cáo tiến độ tuần (Weekly report)*
* **Người trình bày (Presenter):** Phạm Nhật Minh (*Ngành: Hệ thống thông tin*)
* **Cán bộ hướng dẫn (Supervisor):** TS. Phạm Thị Quỳnh Trang (*Khoa Công nghệ Thông tin, Trường Đại học Công nghệ - ĐHQGHN*)
* **Slide trình chiếu:** [weekly_update_slides.pdf](file:///c:/Users/nhatm/.gemini/antigravity/scratch/layoutlmv3-1/thesis/presentation/weekly_update_slides.pdf) | [weekly_update_slides.pptx](file:///c:/Users/nhatm/.gemini/antigravity/scratch/layoutlmv3-1/thesis/presentation/weekly_update_slides.pptx)

---

## Slide 1 — Slide Tiêu Đề

> **[Chỉ dẫn trình chiếu: Mở Slide 1 — Hiện logo Trường ĐH Công nghệ ở giữa phía trên, khung tiêu đề màu xanh "Weekly report", thẻ thông tin Người trình bày (Phạm Nhật Minh) và Cán bộ hướng dẫn (TS. Phạm Thị Quỳnh Trang).]**
>
> "Kính thưa cô, em xin phép bắt đầu buổi báo cáo tiến độ tuần này của đề tài khóa luận tốt nghiệp với tiêu đề: **'Nghiên cứu cải tiến mô hình thị giác - ngôn ngữ cho bài toán trích xuất thông tin khóa trên tài liệu'**.
>
> Đúng như định hướng cô đã góp ý ở buổi trao đổi trước, tên đề tài lần này đã được rút gọn lại để mang tính khái quát cao, súc tích và mạch lạc cho hội đồng bảo vệ, đồng thời không để lộ quá sớm các chi tiết kỹ thuật của bốn module cải tiến ngay trên trang bìa."

---

## Slide 2 — Mục Lục Báo Cáo

> **[Chỉ dẫn trình chiếu: Chuyển sang Slide 2 — 8 ô mục lục được căn chỉnh kích thước đồng nhất, đối xứng hoàn toàn giữa 2 cột.]**
>
> "Nội dung buổi báo cáo hôm nay của em được bố cục thành 8 phần trọng tâm qua 20 slide trực quan:
> 1. **Kiến trúc mô hình tổng thể & Mạng xương sống (Backbone)**
> 2. **Mã hóa vị trí phân cấp (Hierarchical Position Encoding - HPE)**
> 3. **Module ngữ cảnh phân đoạn (Segment Context Module - SCM)**
> 4. **Cơ chế kết hợp muộn có cổng chắn (Masked Gated Late-Fusion)**
> 5. **Hàm mất mát ranh giới trong dòng (Intra-Line Boundary Loss)**
> 6. **Thiết lập thực nghiệm & Bộ dữ liệu**
> 7. **Kết quả thực nghiệm & Phân tích loại trừ từng thành phần (Ablations)**
> 8. **Kế hoạch tiếp theo (Future plans)**"

---

## Slide 3 — 1. Sơ Đồ Kiến Trúc Mô Hình Toàn Diện

> **[Chỉ dẫn trình chiếu: Chuyển sang Slide 3 — Sơ đồ luồng dữ liệu kiến trúc hoàn chỉnh theo phong cách thiết kế của HEADS, đường nối bo cong mềm mại và không còn bất kỳ công thức rườm rà nào.]**
>
> "Nhìn vào sơ đồ kiến trúc tổng thể trên Slide 3, mô hình được tổ chức thành ba vùng xử lý rất liền mạch:
> - **Giai đoạn trước backbone (phía dưới bên trái):** Tọa độ bounding box thô từ OCR được gom nhóm theo dòng đọc, cột biểu mẫu và khối đoạn thông qua cơ chế **Mã hóa vị trí phân cấp (HPE)**, sau đó được chiếu thẳng vào luồng vector nhúng cùng với ảnh và văn bản.
> - **Tại trung tâm:** Mạng xương sống **LayoutLMv3** thực hiện cơ chế self-attention đa phương thức giữa các từ con và các patch ảnh trực quan, sinh ra các vector ẩn ngữ cảnh $\mathbf{h}_i$.
> - **Giai đoạn sau backbone (phía trên và phía dưới bên phải):** Vector ẩn $\mathbf{h}_i$ được tách thành hai nhánh độc lập nhưng bổ trợ cho nhau: một nhánh đi tắt (shortcut) ở mức token và một nhánh đi qua **Module ngữ cảnh phân đoạn (SCM)**. Cả hai nhánh này đều đóng vai trò là đầu vào cho mạng nơ-ron phân lớp để sinh ra đồng thời **Token Logits** và **Segment Logits**. Hai nguồn logit này sau đó được phối hợp mềm dẻo thông qua **Masked Gated Late-Fusion** và được tối ưu hóa trực tiếp cùng với hàm mục tiêu phụ trợ là **Intra-Line Boundary Loss**."

---

## Slide 4 — 1. Tổng Quan Mạng Xương Sống LayoutLMv3

> **[Chỉ dẫn trình chiếu: Chuyển sang Slide 4 — Luồng 4 khối hình học mô tả đường đi của dữ liệu qua LayoutLMv3.]**
>
> "Slide 4 tóm tắt luồng xử lý của mạng xương sống **LayoutLMv3** qua bốn khối chức năng chính:
> 1. **Dữ liệu đầu vào thô:** Bao gồm ảnh trang tài liệu quét kích thước $224 \times 224$, chuỗi từ con OCR $w_i$, và các tọa độ hộp bao 2D đã được chuẩn hóa trong thang đo từ $0$ đến $1000$.
> 2. **Nhúng các phương thái:** Patch ảnh kích thước $16 \times 16$ được chiếu tuyến tính kết hợp vị trí 1D/2D; văn bản dùng vector từ con của RoBERTa; và tọa độ 2D được bổ sung thêm thông tin vị trí phân cấp từ module **HPE**.
> 3. **Khối Transformer đa phương thức:** Tự chú ý đồng thời trên cả hai phương thái thị giác và ngôn ngữ kết hợp với định kiến không gian 2D. Trong đề tài, mô hình được kiểm thử trên cả hai quy mô: bản `base` (12 tầng, $d=768$) và bản `large` (24 tầng, $d=1024$).
> 4. **Đầu ra biểu diễn ngữ cảnh:** Tạo ra các vector đặc trưng $\mathbf{h}_i \in \mathbb{R}^d$ để cấp cho các tầng phân lớp và module phân đoạn phía sau."

---

## Slide 5 — 1. Các Hạn Chế Của Mạng Xương Sống & Giải Pháp Đề Xuất

> **[Chỉ dẫn trình chiếu: Chuyển sang Slide 5 — Bảng 4 dòng đối chiếu trực tiếp giữa hạn chế của mô hình gốc, ví dụ tài liệu thực tế và giải pháp đề xuất tương ứng.]**
>
> "Dù LayoutLMv3 là mô hình rất mạnh, nhưng khi áp dụng vào các biểu mẫu và hóa đơn thực tế, mô hình vẫn bộc lộ bốn điểm nghẽn lớn được tổng hợp ở Slide 5:
> 1. **Tọa độ 2D quá phẳng:** Mô hình chỉ nhận 4 tọa độ đỉnh của từng từ đơn lẻ mà không có thông tin về dòng, cột hay khối. Ví dụ trên một dòng fax hai cột chứa cả `FAX: (336)...` lẫn `PHONE: (336)...`, mô hình rất dễ nhầm lẫn thông tin giữa cột trái và cột phải. **Giải pháp đề xuất:** **Mã hóa vị trí phân cấp (HPE)**.
> 2. **Nhiễu nhãn giữa thực thể (Mid-span fracture):** Các trường dài nhiều từ như `June Flynn for Eric Brown/...` thường xuyên bị phân mảnh nhãn BIO ngay giữa dòng, ví dụ đang là nhãn trả lời `B-ANS` thì từ kế tiếp lại bị gán nhầm thành `O` rồi mới quay lại `I-ANS`. **Giải pháp đề xuất:** **Module ngữ cảnh phân đoạn (SCM)**.
> 3. **Trôi ranh giới toàn đoạn (Whole-segment drift):** Nếu ta ép gom toàn bộ phân đoạn một cách thô bạo thì sẽ xóa nhòa ranh giới các từ con trên các dòng hóa đơn phức tạp, ví dụ như dòng `TOTAL (Qty 2.00) 60.000` vừa có số lượng vừa có tổng tiền. **Giải pháp đề xuất:** **Cơ chế kết hợp muộn có cổng chắn (Masked Gated Late-Fusion)**.
> 4. **Gộp dính ranh giới cùng dòng (Span merging):** Hai thực thể nhãn khác nhau nằm liền kề trên cùng một dòng ngang — chẳng hạn nhãn câu hỏi `TO:` đứng cạnh nhãn câu trả lời `George Baroody` — rất hay bị mô hình gộp chung thành một thực thể duy nhất. **Giải pháp đề xuất:** **Hàm mất mát ranh giới trong dòng (Intra-Line Boundary Loss)**."

---

## Slide 6 — 2. Module 1: Mã Hóa Vị Trí Phân Cấp (HPE) — Cơ Chế Gom Nhóm Trực Quan

> **[Chỉ dẫn trình chiếu: Chuyển sang Slide 6 — Ảnh cắt thực tế từ biểu mẫu fax FUNSD (bên trái) và 3 thẻ thuật toán gom nhóm không gian (bên phải).]**
>
> "Slide 6 minh họa trực quan cách hoạt động của **Module 1: Mã hóa vị trí phân cấp (HPE)** trên một mẫu fax thực tế từ bộ dữ liệu FUNSD:
> 1. **Gom dòng đọc (Line 1..5, màu xanh dương):** Hai hộp bao kề nhau được gom vào cùng một dòng đọc nếu độ chồng lấn theo phương thẳng đứng vượt quá $50\%$ chiều cao của hộp nhỏ hơn.
> 2. **Phát hiện phân cột (Column 0..1, màu xanh lá):** Ngay trên Dòng 2, khoảng cách ngang giữa số fax `(336) 335-7392` và nhãn `PHONE NUMBER:` nhảy một khoảng lớn hơn $12\%$ chiều rộng trang, nhờ đó thuật toán tự động tách dòng này thành Cột 0 và Cột 1 riêng biệt.
> 3. **Gom khối ngữ nghĩa (Block 0..1, màu cam):** Các dòng đọc liên tiếp có khoảng cách dọc nhỏ hơn $1.8$ lần chiều cao trung vị của dòng sẽ được nhóm vào cùng một khối — giúp phân tách rạch ròi giữa Khối 0 (phần tiêu đề tài liệu) và Khối 1 (phần thân biểu mẫu)."

---

## Slide 7 — 2. Module 1: Mã Hóa Vị Trí Phân Cấp (HPE) — Hiện Thực Hóa Trong Mã Nguồn

> **[Chỉ dẫn trình chiếu: Chuyển sang Slide 7 — Sơ đồ hình học nối ghép vector (bên trái) và đoạn code Python rút gọn trên nền tối (bên phải).]**
>
> "Slide 7 thể hiện mã nguồn cốt lõi của HPE bên trong hàm `LayoutLMv3Embeddings.forward`:
> - Về mặt kiến trúc, các chỉ số rời rạc `line_ids`, `block_ids` và `column_ids` (được thu nhỏ với hệ số $0.3$) được tra cứu qua bảng nhúng 128 chiều, sau đó ghép lại thành một vector biểu diễn phân cấp 384 chiều và chiếu về không gian ẩn $d$ qua tầng tuyến tính `hierarchical_proj`.
> - Nhìn vào đoạn code bên phải, các dòng lệnh từ 330 đến 335 thực hiện việc tra cứu ba bảng nhúng, nối vector bằng lệnh `torch.cat([l_emb, b_emb, c_emb], dim=-1)` và cộng trực tiếp dạng phần dư (residual) vào vector nhúng tổng thể trước khi đi qua tầng chuẩn hóa `LayerNorm`."

---

## Slide 8 — 3. Module 2: Module Ngữ Cảnh Phân Đoạn (SCM) — Ý Tưởng Thiết Kế Trực Quan

> **[Chỉ dẫn trình chiếu: Chuyển sang Slide 8 — Minh họa trường dữ liệu nhiều từ trong FUNSD (phía trên) và quy trình xử lý 4 bước của SCM (phía dưới).]**
>
> "Slide 8 giải thích cơ chế của **Module 2: Module ngữ cảnh phân đoạn (SCM)** trên trường dữ liệu nhiều từ `SENDER/PHONE NUMBER:`:
> - Nếu không có cơ chế phân đoạn, 8 từ con cấu thành cụm `June Flynn for Eric Brown/(614) 466-8980` sẽ bị phân loại hoàn toàn độc lập, dẫn tới nguy cơ gãy nhãn giữa chừng rất cao.
> - SCM giải quyết triệt để vấn đề này qua bốn bước trực quan:
>   1. **Gom trung bình (Mean Pool):** Toàn bộ 8 vector token thuộc Phân đoạn $k$ được lấy trung bình để tạo thành một vector đại diện duy nhất $\mathbf{s}_k$ cho cả phân đoạn.
>   2. **Tương tác liên phân đoạn (Segment Attention):** Các vector đoạn trên trang được đưa qua một tầng Transformer 1 lớp nhẹ (4 đầu chú ý), cho phép Phân đoạn $k$ (chứa câu trả lời) liên kết trực tiếp với Phân đoạn $k-1$ (chứa câu hỏi `SENDER/PHONE NUMBER:`).
>   3. **Cổng ReZero ($g$):** Vector đoạn sau khi cập nhật ngữ cảnh được hòa trộn mềm dẻo theo công thức $\mathbf{s}_k + g(\mathbf{c}_k - \mathbf{s}_k)$. Cổng $g$ được khởi tạo bằng $0$ để không làm xáo trộn tri thức của mô hình tiền huấn luyện ngay khi bắt đầu train.
>   4. **Phân phối ngược & Nhúng mỏ neo (Broadcast + Onset):** Vector phân đoạn sau tinh chỉnh được phát ngược lại cho cả 8 token, đồng thời cộng thêm vector định vị điểm đầu để từ `June` nhận nhãn `B-ANSWER` và 7 từ còn lại nhận nhãn `I-ANSWER` một cách nhất quán tuyệt đối."

---

## Slide 9 — 3. Module 2: Module Ngữ Cảnh Phân Đoạn (SCM) — Hiện Thực Hóa Trong Mã Nguồn

> **[Chỉ dẫn trình chiếu: Chuyển sang Slide 9 — Sơ đồ khối hàm xử lý (bên trái) và code Python của hàm `_segment_pool_and_contextualize` (bên phải).]**
>
> "Slide 9 mô tả hiện thực hóa của hàm cốt lõi `_segment_pool_and_contextualize` trong file `modeling_layoutlmv3_segment.py`:
> - Trước hết, lệnh `text_hidden[b, seg_b == sid].mean(dim=0)` tính toán vector trung bình cho từng mã định danh phân đoạn duy nhất trên trang.
> - Tiếp theo, `self.segment_context` thực thi cơ chế tự chú ý giữa các phân đoạn với nhau, được điều tiết an toàn bởi tham số học `self.segment_context_gate`.
> - Cuối cùng, mảng boolean `is_first` phát hiện bước chuyển tiếp phân đoạn qua biểu thức so sánh `segment_ids[:, 1:] != segment_ids[:, :-1]`, từ đó cộng thêm `self.is_first_token_embedding(is_first)` để mô hình phân biệt chính xác vị trí bắt đầu `B-` và các vị trí tiếp nối `I-`."

---

## Slide 10 — 4. Module 3: Kết Hợp Muộn Có Cổng Chắn (Masked Gated Late-Fusion) — Cơ Chế Định Tuyến

> **[Chỉ dẫn trình chiếu: Chuyển sang Slide 10 — Ảnh cắt dòng tổng tiền hóa đơn CORD (bên trái) và sơ đồ định tuyến rẽ 2 nhánh theo mặt nạ (bên phải).]**
>
> "Sang Slide 10, **Module 3: Kết hợp muộn có cổng chắn (Masked Gated Late-Fusion)** giải quyết bài toán cân bằng độ chi tiết giữa mức token và mức phân đoạn, thể hiện qua dòng hóa đơn bán lẻ CORD `TOTAL (Qty 2.00) 60.000`:
> - Trên cùng một dòng văn bản này, các từ lại có yêu cầu về mức độ chi tiết hoàn toàn khác nhau:
>   - **Trường hợp 1 — Token mỏ neo đầu đoạn (`Mask = 0`, màu xanh dương ở chữ `TOTAL`):** Vị trí này bị khóa cứng $100\%$ vào **Segment Logits**, nhằm neo giữ chắc chắn loại thực thể theo quyết định chung của toàn đoạn.
>   - **Trường hợp 2 — Các từ con bên trong (`Mask = 1`, màu cam ở cụm `(Qty 2.00) 60.000`):** Các từ con nối tiếp được hòa trộn mềm qua hệ số cổng **Gated Blend ($\alpha$)** giữa Segment Logits và Token Shortcut Logits. Nhờ đó, mô hình giữ được độ nhạy bén ở mức từ con để tách riêng phần số lượng `Qty 2.00` và phần giá tiền `60.000` mà không bị quyết định của toàn đoạn xóa nhòa."

---

## Slide 11 — 4. Module 3: Kết Hợp Muộn Có Cổng Chắn (Masked Gated Late-Fusion) — Hiện Thực Hóa Trong Mã Nguồn

> **[Chỉ dẫn trình chiếu: Chuyển sang Slide 11 — Mạch cổng điều khiển trực quan (bên trái) và code Python của hàm forward (bên phải).]**
>
> "Slide 11 thể hiện mã nguồn thực thi bên trong `LayoutLMv3ForSegmentTokenClassification.forward`:
> - Hai đầu phân lớp tuyến tính song song tính toán `token_logits` (từ `text_hidden`) và `seg_logits` (từ `seg_repr`).
> - Biến mặt nạ `subword_mask = (1 - is_first).unsqueeze(-1).float()` sẽ nhận giá trị $0.0$ tại các vị trí mỏ neo đầu đoạn và $1.0$ tại các từ con nối tiếp phía sau.
> - Cổng hòa trộn có chặn trên `alpha = self.alpha_max * torch.sigmoid(self.fusion_gate)` sẽ điều tiết luồng logit cuối cùng bằng dòng lệnh: `seg_logits + subword_mask * alpha * (token_logits - seg_logits)`."

---

## Slide 12 — 5. Module 4: Hàm Mất Mát Ranh Giới Trong Dòng (Intra-Line Boundary Loss) — Ý Tưởng Trực Quan

> **[Chỉ dẫn trình chiếu: Chuyển sang Slide 12 — Ảnh quét FUNSD với các vạch đỏ ngăn cách ranh giới thực thể cùng dòng (bên trái) và bảng so sánh nhãn mục tiêu cặp token (bên phải).]**
>
> "Slide 12 mô tả **Module 4: Hàm mất mát ranh giới trong dòng (Intra-Line Boundary Loss)** trên sáu dòng liên tiếp của biểu mẫu FUNSD:
> - Trên các dòng biểu mẫu như `TO: | George Baroody`, `FAX NUMBER: | (336) 335-7392`, hay `DATE: | 12/10/98`, phần nhãn câu hỏi (màu xanh dương) đứng sát ngay cạnh phần nhãn trả lời (màu xanh lá) trên cùng một hàng ngang duy nhất.
> - Thuật toán giám sát trực tiếp từng cặp từ liền kề $(i, i+1)$ theo quy tắc:
>   - Nếu hai từ **nằm trong cùng một thực thể** (ví dụ cặp `["FAX", "NUMBER:"]`): Cùng chung mã thực thể, nhãn mục tiêu nhận **Target = 0**.
>   - Nếu hai từ **nằm ở vị trí chuyển giao giữa hai thực thể** (ví dụ cặp `["NUMBER:", "(336)"]`, được đánh dấu bằng vạch đỏ ngăn cách): Nhận **Target = 1**.
> - Nhờ mục tiêu phụ trợ này, mô hình được ép phải học cách phân tách cực kỳ sắc bén các điểm giao thoa ngay trên cùng một dòng ngang."

---

## Slide 13 — 5. Module 4: Hàm Mất Mát Ranh Giới Trong Dòng (Intra-Line Boundary Loss) — Hiện Thực Hóa Trong Mã Nguồn

> **[Chỉ dẫn trình chiếu: Chuyển sang Slide 13 — Sơ đồ luồng dữ liệu tính loss ranh giới (bên trái) và code Python của hàm `_compute_boundary_loss` (bên phải).]**
>
> "Slide 13 thể hiện hàm tính toán `_compute_boundary_loss`:
> - Vector ẩn của hai vị trí liền kề `text_hidden[:, :-1, :]` và `text_hidden[:, 1:, :]` được nối với nhau theo chiều đặc trưng thành vector $2d$ và đưa qua mạng nơ-ron MLP hai lớp `self.boundary_classifier`.
> - Nhãn ranh giới thực tế được trích xuất bằng phép so sánh `b_labels = (entity_ids[:, :-1] != entity_ids[:, 1:]).float()`, và được tối ưu hóa qua hàm mất mát entropy chéo nhị phân `F.binary_cross_entropy_with_logits` trên toàn bộ các cặp token hợp lệ."

---

## Slide 14 — 6. Thiết Lập Thực Nghiệm: Phần Cứng, Môi Trường & Bộ Dữ Liệu

> **[Chỉ dẫn trình chiếu: Chuyển sang Slide 14 — Hai bảng đặt cạnh nhau: Môi trường huấn luyện máy chủ từ xa (bên trái) và Thông tin hai bộ dữ liệu chuẩn (bên phải).]**
>
> "Chuyển sang phần thực nghiệm ở Slide 14, toàn bộ các lượt huấn luyện và ablation đều được chạy đồng nhất trên máy chủ GPU thuê từ xa trang bị **NVIDIA A100-SXM4-80GB**, bộ nhớ RAM hệ thống 167 GiB, chạy hệ điều hành Ubuntu Linux, Python 3.7.16, PyTorch 1.10.0 với chế độ tính toán dấu phẩy động hỗn hợp FP16. Mọi kết quả đánh giá đều dùng thư viện chuẩn `seqeval` ở mức thực thể trên **3 seed ngẫu nhiên (`42`, `123`, `1993`)**.
>
> Đề tài đánh giá trên hai bộ dữ liệu chuẩn có đặc tính bổ trợ cho nhau rất rõ rệt:
> - **FUNSD:** Gồm 199 biểu mẫu quét thực tế (149 tập train, 50 tập test) với 3 lớp thực thể chính (tương ứng 7 nhãn BIO), đặc trưng bởi bố cục nhiều cột không đồng đều và độ nhiễu tài liệu quét cao.
> - **CORD:** Gồm 1.000 hóa đơn bán lẻ thực tế (800 train, 100 validation, 100 test) với 30 lớp thực thể rất chi tiết (61 nhãn BIO)."

---

## Slide 15 — 6. Cấu Hình Huấn Luyện & Siêu Tham Số

> **[Chỉ dẫn trình chiếu: Chuyển sang Slide 15 — Bảng tổng hợp siêu tham số cỡ chữ lớn, rõ ràng cho cả 4 chế độ chạy.]**
>
> "Slide 15 trình bày chi tiết các siêu tham số huấn luyện qua cả bốn cấu hình (`FUNSD-base`, `CORD-base`, `FUNSD-large` và `CORD-large`):
> - Mỗi cấu hình đều được huấn luyện chuẩn hóa trong **1.000 bước tối ưu**, áp dụng khởi động tuyến tính trong 100 bước đầu (warmup 10%) với bộ tối ưu AdamW.
> - Chiến lược tốc độ học phân tầng (differential learning rate) được áp dụng: phần mạng xương sống tiền huấn luyện dùng learning rate nhỏ $5 \times 10^{-5}$ ($1 \times 10^{-5}$ đối với `FUNSD-large`) để giữ vững tri thức nền; trong khi các module khởi tạo mới (HPE, SCM, Late-Fusion và Boundary Classifier) dùng learning rate lớn hơn là $5 \times 10^{-4}$ để nhanh chóng học thích nghi với bài toán."

---

## Slide 16 — 7. Kết Quả Thực Nghiệm: So Sánh Baseline Và Mô Hình Đề Xuất (3 Seeds)

> **[Chỉ dẫn trình chiếu: Chuyển sang Slide 16 — Bảng số liệu chi tiết trung bình 3 seed kèm độ lệch chuẩn (bên trái) và hai biểu đồ cột trực quan (bên phải).]**
>
> "Slide 16 là kết quả so sánh đối đầu quan trọng nhất giữa mô hình gốc LayoutLMv3 Baseline và Mô hình đề xuất trên cả 3 seed:
> - **Trên tập dữ liệu FUNSD (bản `base`):** Điểm F1 thực thể tăng vọt từ **$89.92 \pm 0.85\%$** lên **$91.58 \pm 0.16\%$**, tức tăng tuyệt đối **$+1.66\%$ F1**. Điểm đặc biệt ấn tượng là độ lệch chuẩn giữa các seed giảm hơn **5 lần**, cho thấy mô hình đề xuất đạt độ ổn định và độ tin cậy vượt trội so với baseline.
> - **Trên FUNSD (bản `large`):** Điểm F1 tiếp tục tăng từ **$91.24 \pm 0.62\%$** lên **$92.45 \pm 0.26\%$** (tăng **$+1.21\%$ F1**).
> - **Trên tập dữ liệu CORD (`base` và `large`):** Dù baseline trên CORD đã đạt mức trần bão hòa rất cao trên $96.7\%$, mô hình đề xuất vẫn đều đặn cải thiện cả Precision và Recall, vươn tới **$96.91 \pm 0.21\%$** trên bản `base` và **$97.35 \pm 0.04\%$** trên bản `large`."

---

## Slide 17 — 7. Thực Nghiệm Loại Trừ Từng Thành Phần (Ablation Study)

> **[Chỉ dẫn trình chiếu: Chuyển sang Slide 17 — Bảng thực nghiệm loại trừ đầy đủ 5 dòng và 2 thẻ phân tích điểm nổi bật phía dưới.]**
>
> "Để làm rõ vai trò của từng thành phần, Slide 17 tổng hợp kết quả phân tích loại trừ (leave-one-out ablation) trên toàn bộ 19 ô thực nghiệm (tương ứng với 57 lượt huấn luyện độc lập):
> - **Khi loại bỏ Module ngữ cảnh phân đoạn (`w/o Segment`, Dòng 5):** Kết quả bị sụt giảm nặng nề nhất trên toàn bộ các cấu hình thử nghiệm: mất **$-1.44\%$ F1** trên `FUNSD-large` (từ $92.45\%$ rớt xuống $91.01\%$) và mất **$-1.22\%$ F1** trên `FUNSD-base` (từ $91.58\%$ xuống $90.36\%$). Điều này chứng minh tương tác ngữ cảnh ở mức phân đoạn chính là nhân tố quan trọng nhất mang lại tính mạch lạc cho thực thể.
> - **Khi loại bỏ hàm mất mát ranh giới (`w/o Boundary Loss`, Dòng 3):** F1 bản `large` bị giảm $0.30\%$ trên FUNSD và $0.34\%$ trên CORD, đồng thời phương sai giữa các seed trên `CORD-large` tăng đột biến hơn 10 lần (từ $\pm 0.04\%$ lên tới $\pm 0.42\%$).
> - **Khi loại bỏ HPE (`w/o HPE`, Dòng 4):** F1 trên `FUNSD-base` giảm $0.25\%$, khẳng định rằng các chỉ số không gian về dòng, cột và khối đóng vai trò bổ trợ định kiến vị trí rất hiệu quả cho các mạng xương sống kích thước vừa."

---

## Slide 18 — 7. Phân Tích Lỗi Chi Tiết Ở Cấp Độ Thực Thể Trên FUNSD

> **[Chỉ dẫn trình chiếu: Chuyển sang Slide 18 — Bảng phân loại lỗi (bên trái) và biểu đồ cột thể hiện mức giảm lỗi ranh giới (bên phải).]**
>
> "Nhằm giải thích cặn kẽ *tại sao* các module đề xuất lại cải thiện được chất lượng trích xuất, Slide 18 bóc tách chi tiết toàn bộ $1.998$ thực thể nhãn chuẩn trong tập test của FUNSD:
> - Số lượng thực thể nhận diện chính xác tuyệt đối cả ranh giới lẫn nhãn loại (True Positives) tăng thêm **24 thực thể** (từ 1.806 lên 1.830).
> - Đặc biệt nhất, **Lỗi ranh giới thực thể (Span Boundary Errors)** — tức là trường hợp mô hình đoán đúng loại thực thể nhưng bị cắt ngắn hoặc gộp dính ranh giới — đã giảm tới **$82.6\%$**, từ **23 lỗi** ở baseline xuống chỉ còn vỏn vẹn **4 lỗi** ở mô hình đề xuất (trong đó loại bỏ hoàn toàn tất cả 4 lỗi vừa sai ranh giới vừa sai nhãn).
> - Số thực thể bị bỏ sót (FN) và số thực thể dự đoán thừa (FP) cũng lần lượt giảm 8 và 13 lỗi."

---

## Slide 19 — 8. Kế Hoạch Tiếp Theo (Future Plans)

> **[Chỉ dẫn trình chiếu: Chuyển sang Slide 19 — Ba thẻ nhiệm vụ trọng tâm được thiết kế trang nhã, không còn văn bản giải thích dài dòng.]**
>
> "Chuyển sang Slide 19, em xin tóm tắt ba kế hoạch trọng tâm cho tuần tới:
> 1. **Tiếp tục tinh chỉnh chuyên sâu trên cả hai bộ dữ liệu FUNSD và CORD:** Thực hiện dò tìm siêu tham số tối ưu cục bộ cho trần cổng kết hợp $\alpha_{\max}$, trọng số hàm mất mát ranh giới $\lambda_{\text{bound}}$ và tỉ lệ co giãn cột của HPE.
> 2. **Hoàn thiện các ca phân tích định tính (Visual Case Studies):** Xuất các hình ảnh so sánh trực quan song song giữa kết quả dự đoán của baseline và mô hình đề xuất để đưa vào Chương 4 của luận văn.
> 3. **Rà soát chuyên sâu và đồng bộ toàn bộ tài liệu luận văn:** Đọc duyệt chi tiết cả hai bản thảo tiếng Anh (`thesis_en.pdf`) và tiếng Việt (`thesis_vi.pdf`), đối soát tính nhất quán tuyệt đối giữa các bảng số liệu, hình vẽ kiến trúc và danh mục tài liệu tham khảo."

---

## Slide 20 — Lời Cảm Ơn & Kết Thúc Báo Cáo

> **[Chỉ dẫn trình chiếu: Chuyển sang Slide 20 — Slide kết thúc trang trọng với logo Trường ĐH Công nghệ ở giữa phía trên và thông điệp cảm ơn gửi tới Cán bộ hướng dẫn TS. Phạm Thị Quỳnh Trang.]**
>
> "Phần báo cáo tiến độ tuần này của em xin được tạm dừng tại đây. Em xin chân thành cảm ơn cô Trang đã luôn dành thời gian quý báu để định hướng nghiên cứu, chỉ dẫn phương pháp khoa học và đồng hành sát sao cùng em trong suốt quá trình thực hiện đề tài. Em rất mong tiếp tục nhận được những nhận xét, góp ý và chỉ đạo của cô để hoàn thiện đề tài tốt hơn nữa ạ."

