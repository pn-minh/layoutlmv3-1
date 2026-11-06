# Kịch Bản Báo Cáo Tiến Độ Tuần (Weekly Report)

* **Báo cáo:** Cập nhật tiến độ nghiên cứu & hoàn thiện mô hình (Weekly Report)
* **Người trình bày:** Phạm Nhật Minh (Ngành Hệ thống Thông tin, Khoa CNTT, Trường ĐH Công nghệ - ĐHQGHN)
* **Cán bộ hướng dẫn:** TS. Phạm Thị Quỳnh Trang (Khoa CNTT, Trường ĐH Công nghệ - ĐHQGHN)
* **Slide trình chiếu:** [`weekly_update_slides.pdf`](file:///c:/Users/nhatm/.gemini/antigravity/scratch/layoutlmv3-1/thesis/presentation/weekly_update_slides.pdf) | [`weekly_update_slides.pptx`](file:///c:/Users/nhatm/.gemini/antigravity/scratch/layoutlmv3-1/thesis/presentation/weekly_update_slides.pptx)
* **Phong cách trình bày:** Tự nhiên, súc tích, giữ thái độ tôn trọng và lễ phép với cô hướng dẫn, đi thẳng vào bản chất kỹ thuật và hiệu quả thực tế của từng thành phần.

---

## Slide 1 — Tiêu Đề (Title Slide)

> **[Chỉ dẫn trình chiếu: Bật Slide 1 — Tiêu đề "Weekly report", tên người trình bày và cán bộ hướng dẫn TS. Phạm Thị Quỳnh Trang.]**
>
> *"Dạ em chào cô Trang ạ. Hôm nay em xin phép được báo cáo nhanh với cô về tiến độ nghiên cứu và các kết quả thực nghiệm mới nhất của đề tài trong tuần qua.*
>
> *Nội dung tuần này em tập trung vào việc chuẩn hóa toàn bộ sơ đồ kiến trúc cải tiến của mô hình, phân tích sâu cơ chế hoạt động thực tế bên trong từng module kèm theo các ví dụ trực quan trên tài liệu thật, và cuối cùng là các số liệu ablation study chi tiết để đánh giá mức độ đóng góp của từng thành phần ạ."*

---

## Slide 2 — Sơ Đồ Kiến Trúc Tổng Thể (Model Architecture)

> **[Chỉ dẫn trình chiếu: Chuyển sang Slide 2 — Toàn bộ slide dành không gian tối đa cho sơ đồ kiến trúc tổng thể, dải bên trái ghi nhãn "Model Architecture".]**
>
> *"Dạ, ở Slide 2 là toàn bộ bức tranh kiến trúc tổng thể của mô hình mà em đã tích hợp hoàn chỉnh và tối ưu kích thước để cô tiện theo dõi.*
>
> *Quy trình xử lý đi rất mạch lạc từ trái qua phải, từ trên xuống dưới:*
> * *Đầu tiên, văn bản, tọa độ OCR và các chỉ số không gian phân cấp (HPE) được đưa vào mạng xương sống **LayoutLMv3 Multimodal Backbone** cùng với các patch ảnh.*
> * *Sau khi qua các tầng Transformer, các vector biểu diễn token được đưa qua **Segment Context Module (SCM)** để gom ngữ cảnh cấp dòng và tổng hợp thông tin trên toàn trang.*
> * *Cuối cùng, trong quá trình huấn luyện, mô hình được tối ưu đồng thời bằng hàm mất mát đa nhiệm (**Multi-Task Objective**), kết hợp giữa hàm phân loại thực thể chính với hai hàm mất mát cấu trúc phụ trợ là **Intra-Line Boundary Loss** và **Cross-Modal Contrastive Loss**.*
>
> *Ở các slide tiếp theo, em xin phép đi vào chi tiết từng module để giải thích cơ chế bên trong và sự khác biệt mà nó mang lại trên tài liệu thực tế ạ."*

---

## Slide 3 — Hierarchical Position Encoding (HPE)

> **[Chỉ dẫn trình chiếu: Chuyển sang Slide 3 — Bên trái là ảnh crop của module HPE, bên phải là giải thích cơ chế và ảnh thực tế trên mẫu biểu FUNSD.]**
>
> *"Dạ, đầu tiên là module **HPE (Hierarchical Position Encoding)** ở Slide 3.*
>
> *Về mặt bản chất bên trong mô hình, thay vì chỉ dùng 4 tọa độ hộp bao 2D đơn thuần như LayoutLMv3 gốc, HPE gán thêm cho mỗi token ba chỉ số phân cấp cấu trúc: chỉ số dòng (`line_id`), chỉ số cột (`column_id`) và chỉ số khối (`block_id`). Ba chỉ số này được chiếu qua các tầng tuyến tính và cộng trực tiếp vào vector nhúng token qua một cổng vô hướng có thể học được (learnable scalar gate).*
>
> *Cô có thể nhìn vào ảnh tài liệu thực tế của bộ FUNSD ở góc dưới bên phải:*
> * *Ở nửa bên trái (khi không có HPE): Do số điện thoại và số fax nằm ngang hàng nhau trên cùng một độ cao, cơ chế tự chú ý 2D thông thường rất dễ bị nhầm lẫn và ghép sai nhãn giữa hai cột cạnh nhau.*
> * *Nhưng ở nửa bên phải (khi có HPE): Nhờ có chỉ số cột phân tách riêng biệt (`column 1` và `column 2`), mô hình cô lập hoàn toàn không gian giữa hai cột, ghép đúng chính xác từng cặp câu hỏi - câu trả lời và liên kết các dòng bị ngắt của cùng một thực thể."*

---

## Slide 4 — LayoutLMv3 Multimodal Backbone

> **[Chỉ dẫn trình chiếu: Chuyển sang Slide 4 — Bên trái là crop cột Backbone, bên phải là ảnh mẫu FUNSD chứng minh vai trò của patch ảnh trực quan.]**
>
> *"Sang Slide 4 là **Mạng xương sống đa phương thái LayoutLMv3**.*
>
> *Bên trong mạng xương sống, mô hình đưa các từ con văn bản và các patch ảnh kích thước $16 \times 16$ vào chung một chuỗi biểu diễn tự chú ý (self-attention), có bổ sung thêm ma trận định kiến không gian 2D tương đối để nhận biết vị trí và khoảng cách hình học giữa các thành phần.*
>
> *Tác động thực tế trên tài liệu được minh họa rất rõ ở hình bên phải:*
> * *Nếu chỉ dựa vào văn bản (Text only), khi gặp các tài liệu bị mờ, chữ in hoa cách điệu hoặc dấu mộc tròn ở tiêu đề, OCR rất dễ nhận dạng sai hoặc bỏ sót từ, khiến mô hình nhầm thành nhãn khác (như `other`).*
> * *Khi có sự tham gia của các patch ảnh thị giác (Text + image patches), đặc trưng hình ảnh của con dấu và kiểu chữ in đậm giúp mô hình nhận biết ngay đây là vùng tiêu đề (`header`), bù đắp hoàn hảo cho phần văn bản bị suy hao."*

---

## Slide 5 — Segment Context Module (SCM)

> **[Chỉ dẫn trình chiếu: Chuyển sang Slide 5 — Crop SCM bên trái, ví dụ FUNSD về hiện tượng nhiễu nhãn từ con bên phải.]**
>
> *"Tiếp theo ở Slide 5 là **Segment Context Module (SCM)**, đây cũng là module mang lại bước nhảy vọt lớn nhất về hiệu năng của mô hình.*
>
> *Về mặt xử lý bên trong, SCM lấy trung bình (mean-pooling) các trạng thái ẩn của các token trong cùng một dòng để tạo thành vector đại diện cho từng phân đoạn (segment vector). Sau đó, một tầng Transformer gọn nhẹ sẽ truyền thông tin ngữ cảnh qua lại giữa các dòng trên toàn trang, rồi hòa trộn sự đồng thuận cấp dòng này ngược trở lại từng token qua cơ chế cổng phần dư (residual gate).*
>
> *Ý nghĩa thực tế của việc này được thể hiện rõ ở ví dụ bên phải:*
> * *Khi không có SCM, các từ trong cùng một cụm dài như `NUMBER OF PAGES INCLUDING COVER SHEET:` rất hay bị hiện tượng 'nhiễu nhãn' (label jitter) — nghĩa là các từ con trong cùng một dòng bị dự đoán nhầm thành các nhãn lộn xộn khác nhau.*
> * *Khi có SCM, toàn bộ các từ trong dòng được đồng nhất theo vector ngữ cảnh chung của phân đoạn, loại bỏ hoàn toàn hiện tượng phân mảnh nhãn và kết nối mượt mà các trường thông tin nằm cách xa nhau."*

---

## Slide 6 — Intra-Line Boundary Loss

> **[Chỉ dẫn trình chiếu: Chuyển sang Slide 6 — Crop Boundary Loss bên trái, ví dụ FUNSD về trường thông tin cùng dòng bên phải.]**
>
> *"Ở Slide 6 là hàm mất mát **Intra-Line Boundary Loss**.*
>
> *Về cơ chế kỹ thuật, trong quá trình huấn luyện, mô hình lấy các cặp vector ẩn liền kề $(\mathbf{h}_i, \mathbf{h}_{i+1})$ dọc theo dòng đọc đưa vào một mạng MLP 2 tầng nhỏ gọn để giám sát xem giữa hai từ có phải là điểm chuyển tiếp ranh giới thực thể hay không, sử dụng hàm mất mát binary cross-entropy. Đặc biệt, nhánh này chỉ hoạt động lúc huấn luyện nên khi suy luận thực tế (inference) sẽ không tốn thêm bất kỳ tham số hay độ trễ nào.*
>
> *Trên tài liệu thực tế:*
> * *Ở các dòng in liền nhau như nhãn `TO:` và tên người `George Baroody`, mô hình thông thường rất hay bị 'chảy nhãn' (label bleed), tức là gộp chung cả câu hỏi lẫn câu trả lời vào làm một thực thể.*
> * *Nhờ có Boundary Loss giám sát các điểm chuyển tiếp, mô hình cắt dứt khoát ranh giới giữa hai thực thể cạnh nhau, phân tách rõ ràng câu hỏi và câu trả lời."*

---

## Slide 7 — Cross-Modal Contrastive Loss

> **[Chỉ dẫn trình chiếu: Chuyển sang Slide 7 — Crop Contrastive Loss bên trái, ví dụ hóa đơn CORD có hình nền mờ bên phải.]**
>
> *"Slide 7 là **Cross-Modal Contrastive Loss**, phần mà tuần trước em đã tinh chỉnh lại để giải quyết dứt điểm xung đột gradient.*
>
> *Về mặt kỹ thuật bên trong, mô hình chiếu các vector văn bản ở giai đoạn trước khi gom dòng (pre-SCM) và căn chỉnh trực tiếp với các vector patch ảnh đã được ngắt lan truyền gradient (`detach`). Sử dụng hàm InfoNCE với mục tiêu mềm dựa trên độ chồng lấn không gian, mô hình sẽ kéo các token văn bản lại gần đúng patch ảnh tương ứng và đẩy lùi các patch ảnh nhiễu nền.*
>
> *Nhìn vào ví dụ hóa đơn CORD ở bên phải:*
> * *Nếu không có Contrastive Loss, các họa tiết nền, hình mờ (watermark) hoặc vết bấm lỗ trên tài liệu thường làm phân tán sự chú ý của token.*
> * *Khi có Contrastive Loss, token văn bản được 'neo' vững chắc vào đúng vùng ảnh chứa nó, giúp mô hình miễn nhiễm với nhiễu nền và nhận dạng chính xác vùng thông tin quan trọng."*

---

## Slide 8 — Multi-Task Training Objective

> **[Chỉ dẫn trình chiếu: Chuyển sang Slide 8 — Crop Multi-Task Objective bên trái, ví dụ toàn diện FUNSD bên phải.]**
>
> *"Slide 8 tổng hợp lại **Hàm mục tiêu huấn luyện đa nhiệm (Multi-Task Training Objective)**.*
>
> *Mô hình tối ưu đồng thời ba thành phần trong một lượt lan truyền ngược duy nhất: hàm mất mát phân loại thực thể chính $\mathcal{L}_{\text{CE}}$, mất mát ranh giới phụ trợ $\mathcal{L}_{\text{bound}}$ với trọng số $0.10$, và mất mát tương phản đa phương thái $\mathcal{L}_{\text{cont}}$ với trọng số nhỏ được hiệu chuẩn ($0.01 \dots 0.03$).*
>
> *Hai nhiệm vụ cấu trúc phụ trợ này đóng vai trò như các bộ điều chuẩn (regularizers), giúp mạng xương sống không bị học vẹt các từ ngữ thường gặp, từ đó cải thiện độ khái quát hóa trên toàn bộ tài liệu như minh họa so sánh giữa mô hình gốc và mô hình đầy đủ ở hình bên phải ạ."*

---

## Slide 9 — Kết Quả Thực Nghiệm & Mức Độ Đóng Góp Của Từng Module

> **[Chỉ dẫn trình chiếu: Chuyển sang Slide 9 — Biểu đồ thanh có mã màu trực quan bên trái, 3 nhận xét rút ra bên phải.]**
>
> *"Dạ, sang Slide 9 là phần kết quả thực nghiệm và phân tích loại trừ (ablation study) trên bộ dữ liệu chuẩn FUNSD-Large, được trực quan hóa bằng biểu đồ thanh phân biệt bằng màu sắc rất rõ ràng.*
>
> *Từ biểu đồ này, em xin báo cáo với cô hai phát hiện mấu chốt quan trọng nhất:*
> 1. *Thứ nhất, **module SCM có đóng góp lớn nhất vào hiệu năng mô hình**: Khi loại bỏ SCM (thanh màu đỏ), điểm F1 sụt giảm nghiêm trọng nhất, giảm tới **$2.34\%$** trên bản Large (từ $93.35\%$ xuống $91.01\%$) và giảm **$1.79\%$** trên bản Base. Điều này khẳng định việc mô hình hóa ngữ cảnh phân đoạn cấp dòng là yếu tố sống còn cho các biểu mẫu phức tạp.*
> 2. *Thứ hai, **toàn bộ 4 module đề xuất đều đóng góp tích cực để vượt qua mô hình baseline gốc**: Mô hình đầy đủ (thanh màu xanh lá) đạt F1 cao nhất là **$93.35\%$**, tăng vượt trội **$+2.11\%$** so với baseline LayoutLMv3 ($91.24\%$). Ngay cả các phiên bản ablation khi bỏ riêng lẻ từng module thì điểm số vẫn cao hơn mức baseline, chứng minh mỗi cải tiến đều có giá trị thực chất.*
> 3. *Ngoài ra, **Boundary Loss** giúp tăng thêm $+1.20\%$ F1 nhờ triệt tiêu lỗi chảy nhãn, và **Contrastive Loss** sau khi được tinh chỉnh chuẩn xác đã đóng góp thêm $+0.90\%$ F1 mà không gây bất kỳ tác dụng phụ nào."*

---

## Slide 10 — Phân Tích Sâu Về Kết Quả Loại Trừ (Ablation Insights)

> **[Chỉ dẫn trình chiếu: Chuyển sang Slide 10 — 6 điểm phân tích chuyên sâu phân bố cân đối trên 2 cột.]**
>
> *"Ở Slide 10, em tổng hợp thêm một số phân tích kỹ thuật sâu hơn về hành vi của mô hình:*
> * *Độ nhạy cảm với độ phức tạp của bố cục: Bộ dữ liệu biểu mẫu nhiều cột như FUNSD nhạy cảm với HPE và SCM hơn hẳn so với hóa đơn CORD, vì hóa đơn thường chỉ có một cột dọc đơn giản.*
> * *Sự đồng thuận phân đoạn: SCM giải quyết triệt để bài toán nhiễu nhãn từ con nhờ việc ép toàn bộ từ trong dòng tuân theo biểu diễn chung của phân đoạn.*
> * *Không phát sinh độ trễ: Boundary Loss chỉ hỗ trợ nắn chỉnh vector trong lúc huấn luyện nên khi triển khai thực tế mô hình chạy nhanh tương đương mô hình gốc.*
> * *Hiệu ứng hiệp đồng siêu tuyến tính (Superlinear synergy): Mức tăng $+2.11\%$ của mô hình đầy đủ lớn hơn tổng mức đóng góp rời rạc của các module cộng lại, cho thấy 4 module này có sự hỗ trợ lẫn nhau rất tốt.*
> * *Tính bất biến theo quy mô: Thứ tự tầm quan trọng của các module được duy trì nhất quán trên cả hai kích thước mô hình 12 tầng (Base) và 24 tầng (Large)."*

---

## Slide 11 — Lời Cảm Ơn & Trao Đổi

> **[Chỉ dẫn trình chiếu: Chuyển sang Slide 11 — Màn hình "Thank You!", thông tin liên hệ email `pnminh289@gmail.com`.]**
>
> *"Dạ, phần báo cáo tiến độ tuần này của em xin được tạm dừng tại đây. Em rất mong nhận được những nhận xét, góp ý và định hướng tiếp theo từ cô để em tiếp tục hoàn thiện các phần thực nghiệm còn lại trong khóa luận ạ.*
>
> *Em xin chân thành cảm ơn cô ạ!"*
