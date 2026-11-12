# Kịch Bản Báo Cáo Tiến Độ Tuần (Weekly Report - 16 Slides)

* **Báo cáo:** Cập nhật tiến độ nghiên cứu & trực quan hóa từng thành phần mô hình
* **Người trình bày:** Phạm Nhật Minh (Ngành Hệ thống Thông tin, Khoa CNTT, Trường ĐH Công nghệ - ĐHQGHN)
* **Cán bộ hướng dẫn:** TS. Phạm Thị Quỳnh Trang (Khoa CNTT, Trường ĐH Công nghệ - ĐHQGHN)
* **Slide trình chiếu:** [`weekly_update_slides.pdf`](file:///c:/Users/nhatm/.gemini/antigravity/scratch/layoutlmv3-1/thesis/presentation/weekly_update_slides.pdf) | [`weekly_update_slides.pptx`](file:///c:/Users/nhatm/.gemini/antigravity/scratch/layoutlmv3-1/thesis/presentation/weekly_update_slides.pptx)
* **Phong cách:** Tự nhiên, súc tích, giữ thái độ tôn trọng và lễ phép với cô hướng dẫn, đi thẳng vào bản chất kỹ thuật và hiệu quả thực tế của từng thành phần.

---

## Slide 1 — Tiêu Đề (Title Slide)

> **[Chỉ dẫn trình chiếu: Bật Slide 1 — Tiêu đề "Weekly report", tên người trình bày và cán bộ hướng dẫn TS. Phạm Thị Quỳnh Trang.]**
>
> *"Dạ em chào cô Trang ạ. Hôm nay em xin phép được báo cáo nhanh với cô về tiến độ nghiên cứu và các kết quả thực nghiệm mới nhất của đề tài trong tuần qua.*
>
> *Nội dung tuần này em tập trung vào việc chuẩn hóa toàn bộ sơ đồ kiến trúc cải tiến của mô hình, phân tích sâu cơ chế hoạt động thực tế bên trong từng module kèm theo 2 ví dụ trực quan cụ thể trên cả biểu mẫu FUNSD lẫn hóa đơn CORD, và cuối cùng là biểu đồ phân tích ablation study chi tiết để đánh giá mức độ đóng góp của từng thành phần ạ."*

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
> *Ở các slide tiếp theo, em xin phép đi vào chi tiết từng module với 2 ví dụ thực tế trên cả biểu mẫu và hóa đơn ạ."*

---

## Slide 3 — Hierarchical Position Encoding (HPE) — Ví Dụ 1: FUNSD (Bảng Nhiều Cột)

> **[Chỉ dẫn trình chiếu: Chuyển sang Slide 3 — Bên trái là ảnh crop của module HPE, bên phải là giải thích cơ chế và ảnh thực tế trên mẫu biểu FUNSD nhiều cột.]**
>
> *"Dạ, đầu tiên là module **HPE (Hierarchical Position Encoding)** ở Slide 3.*
>
> *Về mặt bản chất bên trong mô hình, thay vì chỉ dùng 4 tọa độ hộp bao 2D đơn thuần, HPE gán thêm cho mỗi token ba chỉ số phân cấp cấu trúc: chỉ số dòng (`line_id`), chỉ số cột (`column_id`) và chỉ số khối (`block_id`), sau đó chiếu qua tầng tuyến tính và cộng trực tiếp vào vector nhúng token qua một cổng vô hướng có thể học được (learnable scalar gate).*
>
> *Ở ví dụ 1 trên biểu mẫu FUNSD nhiều cột:*
> * *Bên trái (không có HPE): Số điện thoại và số fax nằm ngang hàng nhau trên cùng độ cao, cơ chế tự chú ý thông thường rất dễ bị nhầm lẫn và ghép chéo sai nhãn giữa hai cột cạnh nhau.*
> * *Bên phải (khi có HPE): Nhờ có chỉ số cột phân tách riêng (`column 1` và `column 2`), mô hình cô lập hoàn toàn không gian giữa hai cột, ghép đúng chính xác từng cặp câu hỏi - câu trả lời tương ứng."*

---

## Slide 4 — Hierarchical Position Encoding (HPE) — Ví Dụ 2: CORD (Hóa Đơn Nhiều Dòng)

> **[Chỉ dẫn trình chiếu: Chuyển sang Slide 4 — Giữ nguyên crop HPE bên trái, thay ảnh ví dụ CORD ở bên phải.]**
>
> *"Sang Slide 4 là ví dụ thứ hai của HPE trên mẫu hóa đơn CORD có nhiều dòng món ăn xếp chồng nhau:*
> * *Về cơ chế: HPE mã hóa chỉ số thứ tự dòng vào vector nhúng, giúp bảo toàn thứ tự đọc và gom nhóm cục bộ giữa các phần tử trên cùng một hàng ngang.*
> * *Trên hóa đơn thực tế: Khi không có chỉ số dòng, các con số giá tiền rất dễ bị 'nhảy dòng' và gắn nhầm vào tên món ở hàng trên hoặc hàng dưới. Khi có HPE, chỉ số dòng liên kết chặt chẽ giá tiền với đúng tên món tương ứng trên cùng dòng."*

---

## Slide 5 — LayoutLMv3 Multimodal Backbone — Ví Dụ 1: FUNSD (Tiêu Đề & Con Dấu)

> **[Chỉ dẫn trình chiếu: Chuyển sang Slide 5 — Bên trái là crop Backbone, bên phải là ảnh mẫu FUNSD chứng minh vai trò của patch ảnh trực quan.]**
>
> *"Slide 5 là **Mạng xương sống đa phương thái LayoutLMv3**.*
>
> *Bên trong mạng xương sống, mô hình đưa các từ con văn bản và các patch ảnh kích thước $16 \times 16$ vào chung một chuỗi biểu diễn tự chú ý (self-attention), có bổ sung thêm ma trận định kiến không gian 2D tương đối để nhận biết khoảng cách hình học.*
>
> *Ở ví dụ 1 trên bộ FUNSD:*
> * *Nếu chỉ dựa vào văn bản (Text only), khi gặp các tài liệu bị mờ, chữ in hoa cách điệu hoặc dấu mộc tròn ở tiêu đề, OCR rất dễ bỏ sót từ khiến mô hình nhầm thành nhãn khác (như `other`).*
> * *Khi có sự tham gia của các patch ảnh thị giác (Text + image patches), đặc trưng hình ảnh của con dấu và kiểu chữ in đậm giúp mô hình nhận biết ngay đây là vùng tiêu đề (`header`), bù đắp hoàn hảo cho phần văn bản bị suy hao."*

---

## Slide 6 — LayoutLMv3 Multimodal Backbone — Ví Dụ 2: CORD (Phân Biệt Tổng Tiền In Đậm)

> **[Chỉ dẫn trình chiếu: Chuyển sang Slide 6 — Crop Backbone bên trái, ví dụ CORD phân biệt tổng tiền và giá món bên phải.]**
>
> *"Ở Slide 6 là ví dụ 2 của Backbone trên hóa đơn CORD:*
> * *Về cơ chế: Tầng attention đa phương thái tích hợp các đặc trưng thị giác như cỡ chữ, độ đậm (font weight) và độ nổi bật để phân biệt các chuỗi số vốn dĩ nhìn về mặt chữ rất giống nhau.*
> * *Trên thực tế: Nếu chỉ nhìn chuỗi ký tự '40,000', mô hình thuần văn bản sẽ dễ nhầm đây là giá của một món ăn bình thường. Nhưng nhờ các patch ảnh nhận diện được cỡ chữ to và in đậm đặc trưng của dòng tổng tiền, mô hình phân loại chính xác đây là trường `total_price`."*

---

## Slide 7 — Segment Context Module (SCM) — Ví Dụ 1: FUNSD (Triệt Tiêu Nhiễu Nhãn Từ Con)

> **[Chỉ dẫn trình chiếu: Chuyển sang Slide 7 — Crop SCM bên trái, ví dụ FUNSD về hiện tượng nhiễu nhãn từ con bên phải.]**
>
> *"Tiếp theo ở Slide 7 là **Segment Context Module (SCM)**, module mang lại bước nhảy vọt lớn nhất về hiệu năng.*
>
> *Về mặt xử lý bên trong, SCM lấy trung bình (mean-pooling) các trạng thái ẩn của các token trong cùng một dòng để tạo thành vector đại diện cho từng phân đoạn (segment vector). Sau đó, một tầng Transformer gọn nhẹ sẽ truyền thông tin ngữ cảnh qua lại giữa các dòng trên toàn trang, rồi hòa trộn sự đồng thuận cấp dòng này ngược trở lại từng token qua cơ chế cổng phần dư.*
>
> *Ở ví dụ 1 trên FUNSD:*
> * *Khi không có SCM, các từ trong cùng một cụm dài như `NUMBER OF PAGES INCLUDING COVER SHEET:` rất hay bị hiện tượng 'nhiễu nhãn' (label jitter) — các từ con trong cùng một dòng bị dự đoán nhầm thành các nhãn lộn xộn khác nhau.*
> * *Khi có SCM, toàn bộ các từ trong dòng được đồng nhất theo vector ngữ cảnh chung của phân đoạn, loại bỏ hoàn toàn hiện tượng phân mảnh nhãn."*

---

## Slide 8 — Segment Context Module (SCM) — Ví Dụ 2: CORD (Truyền Ngữ Cảnh Gán Nhãn Giá Trị)

> **[Chỉ dẫn trình chiếu: Chuyển sang Slide 8 — Giữ crop SCM bên trái, thay ví dụ CORD gán nhãn các số tiền độc lập bên phải.]**
>
> *"Sang Slide 8 là ví dụ 2 của SCM trên hóa đơn CORD:*
> * *Về cơ chế: Tầng Transformer phân đoạn truyền thông tin qua lại giữa các dòng, giúp chuyển giao ngữ nghĩa từ nhãn khóa (key) sang giá trị (value).*
> * *Trên thực tế: Các con số đứng độc lập như '46,000', '50,000', '4,000' nếu đứng một mình sẽ rất khó phân loại. Nhưng nhờ SCM truyền ngữ cảnh từ các dòng khóa tương ứng là `TOTAL`, `CASH`, `CHANGE`, mô hình gán đúng nhãn cho từng số tiền mà không bị nhầm lẫn."*

---

## Slide 9 — Intra-Line Boundary Loss — Ví Dụ 1: FUNSD (Ngắt Cặp Key-Value Cùng Dòng)

> **[Chỉ dẫn trình chiếu: Chuyển sang Slide 9 — Crop Boundary Loss bên trái, ví dụ FUNSD về trường thông tin cùng dòng bên phải.]**
>
> *"Ở Slide 9 là hàm mất mát **Intra-Line Boundary Loss**.*
>
> *Về cơ chế kỹ thuật, trong quá trình huấn luyện, mô hình lấy các cặp vector ẩn liền kề $(\mathbf{h}_i, \mathbf{h}_{i+1})$ dọc theo dòng đọc đưa vào một mạng MLP 2 tầng nhỏ gọn để giám sát xem giữa hai từ có phải là điểm chuyển tiếp ranh giới thực thể hay không. Nhánh này chỉ chạy lúc huấn luyện nên không phát sinh bất kỳ độ trễ nào lúc suy luận.*
>
> *Ở ví dụ 1 trên FUNSD:*
> * *Ở các dòng in liền nhau như nhãn `TO:` và tên người `George Baroody`, mô hình thông thường rất hay bị 'chảy nhãn' (label bleed), tức là gộp chung cả câu hỏi lẫn câu trả lời vào làm một thực thể.*
> * *Nhờ có Boundary Loss giám sát các điểm chuyển tiếp, mô hình cắt dứt khoát ranh giới giữa hai thực thể cạnh nhau, phân tách rõ ràng câu hỏi và câu trả lời."*

---

## Slide 10 — Intra-Line Boundary Loss — Ví Dụ 2: CORD (Tách Số Lượng, Tên Món, Đơn Giá)

> **[Chỉ dẫn trình chiếu: Chuyển sang Slide 10 — Giữ crop Boundary Loss bên trái, thay ví dụ CORD tách 3 trường trên một dòng bên phải.]**
>
> *"Slide 10 là ví dụ 2 của Boundary Loss trên hóa đơn CORD:*
> * *Về cơ chế: MLP ranh giới phát hiện sự đổi nhãn giữa các token liên tiếp nằm sát nhau trên cùng một dòng đọc ngang.*
> * *Trên hóa đơn thực tế: Mỗi dòng món ăn thường gồm số lượng `[1]`, tên món `[TWIST STRAWBERRY DONUT]` và đơn giá `[10,000]` nằm rất sát nhau. Nếu không có Boundary Loss, mô hình rất hay gộp nhầm số lượng và tên món vào cùng một trường. Boundary Loss tạo ra các điểm cắt chính xác để phân tách độc lập cả 3 trường này."*

---

## Slide 11 — Cross-Modal Contrastive Loss — Ví Dụ 1: CORD (Chống Nhiễu Nền Watermark)

> **[Chỉ dẫn trình chiếu: Chuyển sang Slide 11 — Crop Contrastive Loss bên trái, ví dụ hóa đơn CORD có hình nền mờ bên phải.]**
>
> *"Slide 11 là **Cross-Modal Contrastive Loss**, phần mà tuần trước em đã tinh chỉnh lại để giải quyết dứt điểm xung đột gradient.*
>
> *Về mặt kỹ thuật, mô hình chiếu các vector văn bản ở giai đoạn trước khi gom dòng (pre-SCM) và căn chỉnh trực tiếp với các vector patch ảnh đã ngắt gradient (`detach`). Sử dụng hàm InfoNCE với mục tiêu mềm dựa trên độ chồng lấn không gian, mô hình sẽ kéo các token văn bản lại gần đúng patch ảnh tương ứng và đẩy lùi các patch ảnh nhiễu nền.*
>
> *Ở ví dụ 1 trên hóa đơn CORD:*
> * *Nếu không có Contrastive Loss, các họa tiết nền mờ (watermark) hoặc logo in chìm rất hay hút sự chú ý của token, làm sai lệch biểu diễn.*
> * *Khi có Contrastive Loss, token văn bản được neo vững chắc vào đúng vùng ảnh chứa nó, giúp mô hình miễn nhiễm với nhiễu nền."*

---

## Slide 12 — Cross-Modal Contrastive Loss — Ví Dụ 2: FUNSD (Chống Trôi Vào Mép Bấm Lỗ)

> **[Chỉ dẫn trình chiếu: Chuyển sang Slide 12 — Giữ crop Contrastive bên trái, thay ví dụ FUNSD chống trôi vào mép quét / lỗ bấm bên phải.]**
>
> *"Slide 12 là ví dụ 2 của Contrastive Loss trên tài liệu FUNSD:*
> * *Về cơ chế: Hàm mất mát tương phản đẩy lùi các vùng ảnh tối, không chứa văn bản ra xa khỏi không gian biểu diễn của token.*
> * *Trên tài liệu quét thực tế: Các biểu mẫu cũ thường có vết đục lỗ ở lề trái hoặc dải màu đen ở mép quét máy scan. Nếu không có Contrastive Loss, các token ở đầu dòng rất hay bị trôi đặc trưng về phía các đốm đen này. Contrastive Loss kéo token trở lại đúng vùng văn bản in thực tế."*

---

## Slide 13 — Multi-Task Training Objective — Ví Dụ 1: FUNSD (Hiệu Chỉnh Toàn Diện Biểu Mẫu)

> **[Chỉ dẫn trình chiếu: Chuyển sang Slide 13 — Crop Multi-Task Objective bên trái, ví dụ toàn diện FUNSD bên phải.]**
>
> *"Slide 13 thể hiện **Hàm mục tiêu huấn luyện đa nhiệm (Multi-Task Training Objective)**.*
>
> *Mô hình tối ưu đồng thời ba thành phần trong một lượt lan truyền ngược duy nhất: hàm phân loại thực thể chính $\mathcal{L}_{\text{CE}}$, mất mát ranh giới phụ trợ $\mathcal{L}_{\text{bound}}$ và mất mát tương phản đa phương thái $\mathcal{L}_{\text{cont}}$.*
>
> *Ở ví dụ 1 trên bộ FUNSD:*
> * *Hai nhiệm vụ cấu trúc phụ trợ đóng vai trò như các bộ điều chuẩn (regularizers), giúp mạng xương sống học được biểu diễn không gian chuẩn xác.*
> * *Như cô có thể thấy trên hình so sánh: mô hình baseline bị gán sai 3 thực thể lớn ở phần tiêu đề và câu hỏi, trong khi mô hình đầy đủ 4 module nhận dạng chính xác $100\%$ toàn bộ các trường trên trang."*

---

## Slide 14 — Multi-Task Training Objective — Ví Dụ 2: CORD (Độ Chính Xác Tuyệt Đối Trên Hóa Đơn)

> **[Chỉ dẫn trình chiếu: Chuyển sang Slide 14 — Giữ crop Objective bên trái, thay ví dụ CORD đối chiếu baseline vs mô hình đầy đủ bên phải.]**
>
> *"Slide 14 là ví dụ 2 của Multi-Task Objective trên hóa đơn CORD:*
> * *Về cơ chế: Sự kết hợp đồng thời giữa ranh giới token cục bộ và căn chỉnh ảnh toàn cục giúp ổn định hoàn toàn trọng số mô hình qua quá trình hội tụ.*
> * *Trên hóa đơn CORD: Mô hình baseline bị nhầm lẫn giữa tổng tiền, số lượng và tiền thừa (các ô màu đỏ). Khi có đủ 4 module, tất cả các trường từ tên món, tổng tiền đến tiền thối lại đều được trích xuất hoàn hảo (các ô màu xanh)."*

---

## Slide 15 — Kết Quả Thực Nghiệm & Mức Độ Đóng Góp Của Từng Module

> **[Chỉ dẫn trình chiếu: Chuyển sang Slide 15 — Biểu đồ thanh có mã màu trực quan bên trái, 3 nhận xét rút ra bên phải.]**
>
> *"Dạ, sang Slide 15 là phần kết quả thực nghiệm và phân tích loại trừ (ablation study) trên bộ dữ liệu chuẩn FUNSD-Large, được trực quan hóa bằng biểu đồ thanh phân biệt bằng màu sắc rất rõ ràng.*
>
> *Từ biểu đồ này, em xin báo cáo với cô hai phát hiện mấu chốt quan trọng nhất:*
> 1. *Thứ nhất, **module SCM có đóng góp lớn nhất vào hiệu năng mô hình**: Khi loại bỏ SCM (thanh màu đỏ), điểm F1 sụt giảm nghiêm trọng nhất, giảm tới **$2.34\%$** trên bản Large (từ $93.35\%$ xuống $91.01\%$) và giảm **$1.79\%$** trên bản Base. Điều này khẳng định việc mô hình hóa ngữ cảnh phân đoạn cấp dòng là yếu tố sống còn cho các biểu mẫu phức tạp.*
> 2. *Thứ hai, **toàn bộ 4 module đề xuất đều đóng góp tích cực để vượt qua mô hình baseline gốc**: Mô hình đầy đủ (thanh màu xanh lá) đạt F1 cao nhất là **$93.35\%$**, tăng vượt trội **$+2.11\%$** so với baseline LayoutLMv3 ($91.24\%$). Ngay cả các phiên bản ablation khi bỏ riêng lẻ từng module thì điểm số vẫn cao hơn mức baseline, chứng minh mỗi cải tiến đều có giá trị thực chất.*
> 3. *Ngoài ra, **Boundary Loss** giúp tăng thêm $+1.20\%$ F1 nhờ triệt tiêu lỗi chảy nhãn, và **Contrastive Loss** sau khi được tinh chỉnh chuẩn xác đã đóng góp thêm $+0.90\%$ F1 mà không gây bất kỳ tác dụng phụ nào."*

---

## Slide 16 — Lời Cảm Ơn & Trao Đổi

> **[Chỉ dẫn trình chiếu: Chuyển sang Slide 16 — Màn hình "Thank You!", thông tin liên hệ email `pnminh289@gmail.com`.]**
>
> *"Dạ, phần báo cáo tiến độ tuần này của em xin được tạm dừng tại đây. Em rất mong nhận được những nhận xét, góp ý và định hướng tiếp theo từ cô để em tiếp tục hoàn thiện các phần thực nghiệm còn lại trong khóa luận ạ.*
>
> *Em xin chân thành cảm ơn cô ạ!"*
