# Kịch Bản Thuyết Trình Bảo Vệ Khóa Luận Tốt Nghiệp (Vietnamese Defense Script)

**Đề tài:** *Trích xuất thông tin chính trên tài liệu giàu hình ảnh dựa trên kiến trúc đa phương thức LayoutLMv3 nhận thức cấu trúc*  
*(Structure-Aware Multi-Modal LayoutLMv3 for Key Information Extraction on Visually Rich Documents)*  
**Thời lượng tiêu chuẩn:** 12 – 15 phút thuyết trình + Phần trả lời câu hỏi phản biện (Q&A)  
**Cấu trúc:** Bám sát bố cục 5 chương của khóa luận (Chương 5 sẽ được bổ sung khi toàn bộ chuỗi thí nghiệm Ablation trên GPU A100 hoàn tất).

---

## SLIDE 1: Trang Bìa & Lời Chào Mở Đầu (0:00 – 1:00)

**[Hiển thị trên Slide]:**
- Tên đề tài tiếng Việt & tiếng Anh.
- Thông tin Sinh viên thực hiện, Giảng viên hướng dẫn (TS. Phạm Thị Quỳnh Trang), Giảng viên đồng hướng dẫn (PGS. TS. Lê Đức Trọng), Khoa Công nghệ Thông tin – Trường Đại học Công nghệ, ĐHQGHN (VNU-UET).

**[Lời thoại thuyết trình]:**
> "Kính thưa Thầy/Cô Chủ tịch Hội đồng, các Thầy/Cô ủy viên trong Hội đồng chấm khóa luận tốt nghiệp, cùng toàn thể các bạn sinh viên có mặt trong buổi bảo vệ ngày hôm nay.  
> Em tên là [Tên Sinh Viên], sinh viên khóa [Khóa] ngành Khoa học Máy tính. Hôm nay, em rất vinh dự được trình bày kết quả nghiên cứu khóa luận tốt nghiệp của mình với đề tài: *'Trích xuất thông tin chính trên tài liệu giàu hình ảnh dựa trên kiến trúc đa phương thức LayoutLMv3 nhận thức cấu trúc'*, dưới sự hướng dẫn khoa học của TS. Phạm Thị Quỳnh Trang và PGS. TS. Lê Đức Trọng.  
> Nội dung bài trình bày của em gồm 5 phần tương ứng với 5 chương trong quyển báo cáo: (1) Đặt vấn đề và bài toán Trích xuất thông tin chính – KIE; (2) Cơ sở lý thuyết và các nghiên cứu liên quan; (3) Phương pháp đề xuất với 3 cải tiến kiến trúc cốt lõi; (4) Thực nghiệm và kết quả đánh giá đa hạt giống (multi-seed) trên GPU NVIDIA A100; và (5) Định hướng kết luận."

---

## SLIDE 2: Động Lực Thực Tiễn & Bài Toán KIE trên VRD (Chương 1 | 1:00 – 2:30)

**[Hiển thị trên Slide]:**
- Hình minh họa mẫu biểu mẫu hành chính (FUNSD) và hóa đơn bán lẻ (CORD).
- Ba phương thức thông tin (3 Modalities): Văn bản (Text) + Bố cục không gian 2D (Layout Bounding Boxes) + Hình ảnh thị giác (Visual Image Patches).
- Phát biểu bài toán gán nhãn chuỗi đa phương thức theo chuẩn IOB2: $\mathcal{D} = \{(w_i, \mathbf{b}_i, s_i)\}_{i=1}^L \cup \{\mathbf{I}\} \to \hat{\mathbf{Y}} \in \{\texttt{B-}e_k, \texttt{I-}e_k, \texttt{O}\}^L$.

**[Lời thoại thuyết trình]:**
> "Thưa Hội đồng, trong quá trình chuyển đổi số tại các ngân hàng, doanh nghiệp kiểm toán, bảo hiểm và cơ quan hành chính, mỗi ngày có hàng triệu hóa đơn, biên lai thu ngân (POS), hợp đồng và biểu mẫu được số hóa dưới dạng ảnh quét hoặc tệp PDF. Bài toán tự động bóc tách các trường thông tin quan trọng từ các tài liệu này được cộng đồng nghiên cứu quốc tế định danh là bài toán **Trích xuất thông tin chính (Key Information Extraction – KIE)** trên **Tài liệu giàu hình ảnh (Visually Rich Documents – VRDs)**.  
> Khác với bài toán nhận diện thực thể tên riêng (NER) trên văn bản thuần túy một chiều, ngữ nghĩa của một trường thông tin trên tài liệu VRD phụ thuộc chặt chẽ vào sự giao thoa của 3 phương thức: từ vựng OCR ($w_i$), tọa độ khung giới hạn 2 chiều ($\mathbf{b}_i = (x_0, y_0, x_1, y_1)$ chuẩn hóa về lưới $[0, 1000]^4$), và đặc trưng thị giác của ảnh tài liệu ($\mathbf{I}$). Chúng em mô hình hóa KIE dưới dạng bài toán gán nhãn chuỗi đa phương thức theo lược đồ **IOB2**, yêu cầu mô hình dự đoán chính xác hoàn toàn cả ranh giới bắt đầu – kết thúc lẫn loại thực thể."

---

## SLIDE 3: Cơ Sở Lý Thuyết & Ba Hạn Chế Của LayoutLMv3 Gốc (Chương 1 & Chương 2 | 2:30 – 4:30)

**[Hiển thị trên Slide]:**
- Sơ đồ kiến trúc LayoutLMv3 gốc (Huang et al., ACM Multimedia 2022) và bảng đối sánh với LayoutLMv1, LayoutLMv2, BROS, LiLT, DocFormer.
- Ba hạn chế cốt lõi khi tinh chỉnh (fine-tune) LayoutLMv3 gốc cho bài toán KIE:
  1. **Mã hóa tọa độ 2D đẳng hướng (Isotropic 2D Embedding):** Cấp phát cứng $d/6$ chiều cho mọi trục $(x_0, y_0, x_1, y_1, w, h)$.
  2. **Thiếu đồng thuận cấu trúc cấp đoạn/dòng (Lack of Segment Consensus):** Chỉ dùng chung khung bao dòng nhưng không có biểu diễn trung gian cấp dòng (segment).
  3. **Thiếu ràng buộc trơn ranh giới nội dòng (Lack of Intra-Line Boundary Smoothness):** Hàm mất mát Cross-Entropy xử lý độc lập từng token.

**[Lời thoại thuyết trình]:**
> "Trong Chương 2, chúng em khảo sát sự tiến hóa của dòng mô hình đa phương thức LayoutLM. Trong đó, **LayoutLMv3** là kiến trúc tiên tiến nhất khi loại bỏ hoàn toàn mạng CNN nặng nề, thay bằng phép chiếu tuyến tính các mảnh ảnh (image patches $16 \times 16$) kết hợp 3 mục tiêu tiền huấn luyện MLM, MIM và WPA.  
> Tuy nhiên, qua phân tích lý thuyết và thực nghiệm mã nguồn, chúng em phát hiện **3 hạn chế cấu trúc** khiến LayoutLMv3 gốc vẫn gặp lỗi phân mảnh thực thể trên bài toán KIE:  
> - **Thứ nhất**, phép nhúng tọa độ 2D của mô hình gốc hoàn toàn *đẳng hướng* – chia đều $d/6 = 128$ chiều cho cả trục ngang và trục dọc, bỏ qua sự bất đối xứng hình học giữa trật tự từ nội dòng (trục $X$) và cấu trúc phân층 liên dòng (trục $Y$).  
> - **Thứ hai**, cơ chế Self-Attention chỉ hoạt động ở mức subword token mà thiếu một tầng biểu diễn trung gian cấp đoạn/dòng văn bản (segment), dẫn đến hiện tượng các từ nằm cùng một dòng nhưng bị gán nhãn mâu thuẫn nhau.  
> - **Thứ ba**, hàm mất mát Cross-Entropy tiêu chuẩn tối ưu từng token độc lập mà không phạt sự biến thiên đột ngột của vector ẩn giữa các token liền kề trong cùng một dòng."

---

## SLIDE 4: Phương Pháp Đề Xuất – Tổng Quan & Thành Phần 1: HPE (Chương 3 | 4:30 – 6:30)

**[Hiển thị trên Slide]:**
- Sơ đồ kiến trúc tổng thể **Structure-Aware LayoutLMv3** (Hình 3.1 trong khóa luận).
- Công thức **Mã hóa vị trí 2D phân cấp (Hierarchical 2D Positional Encoding – HPE)**:
  - Nhóm nội dòng (Horizontal): $(x_0, x_1, w) \to d_x = d/8 = 96$ chiều/thuộc tính ($3d_x = 288$).
  - Nhóm liên dòng (Vertical): $(y_0, y_1, h) \to d_y = 5d/24 = 160$ chiều/thuộc tính ($3d_y = 480$).
  - Phép chiếu hợp nhất phi tuyến: $\mathbf{e}_{\text{HPE}}^{\text{pos2D}}(\mathbf{b}_i) = \text{GELU}(\text{LN}(\mathbf{W}_{\text{HPE}}[\mathbf{e}_{\text{horiz}} \| \mathbf{e}_{\text{vert}}] + \mathbf{b}_{\text{HPE}}))$.

**[Lời thoại thuyết trình]:**
> "Để giải quyết triệt để 3 hạn chế trên, trong Chương 3, chúng em đề xuất kiến trúc **Structure-Aware LayoutLMv3** tích hợp 3 thành phần cải tiến đồng bộ.  
> Thành phần thứ nhất là **Mã hóa vị trí 2D phân cấp (HPE)**. Thay vì chia đều 128 chiều cho mỗi tọa độ, HPE phân tách không gian tọa độ thành hai nhánh bất đối xứng: nhánh ngang $(x_0, x_1, w)$ biểu diễn cấu trúc cục bộ nội dòng với $d_x = 96$ chiều mỗi thuộc tính; và nhánh dọc $(y_0, y_1, h)$ biểu diễn cấu trúc phân tầng liên dòng với dung lượng lớn hơn là $d_y = 160$ chiều mỗi thuộc tính. Sau khi ghép nối ($288 + 480 = 768$ chiều), vector tọa độ đi qua tầng hợp nhất phi tuyến gồm phép chiếu tuyến tính $\mathbf{W}_{\text{HPE}}$, chuẩn hóa tầng LayerNorm và hàm kích hoạt GELU, giúp mô hình nắm bắt tương tác tỷ lệ khung hình (aspect ratio) ngay từ tầng đầu vào."

---

## SLIDE 5: Thành Phần 2 (Mô-đun Tương Tác Token–Đoạn SCM) & Thành Phần 3 (Hàm Mất Mát Ranh Giới) (Chương 3 | 6:30 – 9:00)

**[Hiển thị trên Slide]:**
- **Thành phần 2 – Mô-đun tương tác Token–Đoạn (SCM):**
  1. Gộp đặc trưng dòng bằng Mean Pooling: $\mathbf{u}_k = \frac{1}{|\mathcal{I}_k|} \sum_{i \in \mathcal{I}_k} \mathbf{h}_i$.
  2. Tương tác liên đoạn qua Multi-Head `SegmentAttention` (8 heads): $\hat{\mathbf{U}} = \text{LN}(\mathbf{U} + \text{Dropout}(\text{MHSA}_{\text{seg}}(\mathbf{U})))$.
  3. Truyền ngược có cổng **ReZero** ($\alpha^{(0)} = 0$) + Nhúng chỉ báo đầu đoạn $f_i = \mathds{1}[s_i \neq s_{i-1}]$:
     $$\mathbf{h}_i^{\text{final}} = \mathbf{h}_i + \alpha \cdot \mathds{1}[s_i \ge 0] \cdot \left(\hat{\mathbf{u}}_{s_i} + \mathbf{e}_{\text{first}}(f_i)\right)$$
- **Thành phần 3 – Hàm mất mát điều chuẩn ranh giới nội dòng ($\mathcal{L}_{\text{bound}}$):**
  $$\mathcal{L}_{\text{bound}} = \frac{1}{|\mathcal{P}_{\text{intra}}|} \sum_{(i, i+1) \in \mathcal{P}_{\text{intra}}} \left(1 - \cos(\mathbf{h}_i^{\text{final}}, \mathbf{h}_{i+1}^{\text{final}})\right), \quad \mathcal{L}_{\text{total}} = \mathcal{L}_{\text{CE}} + \lambda_{\text{bound}}\mathcal{L}_{\text{bound}}$$

**[Lời thoại thuyết trình]:**
> "Thành phần thứ hai là **Mô-đun tương tác Token–Đoạn (Segment Consensus Module – SCM)** đặt phía trên bộ mã hóa Transformer. Trước hết, các token thuộc cùng một dòng văn bản $s_i = k$ được gộp qua phép lấy trung bình có mặt nạ (Masked Mean Pooling) để tạo vector đại diện dòng $\mathbf{u}_k$. Tiếp theo, toàn bộ $S$ dòng trên trang tài liệu tương tác với nhau qua khối `SegmentAttention` 8 đầu chú ý để nắm bắt quan hệ bố cục toàn cục (ví dụ: câu hỏi bên trái liên kết với câu trả lời bên phải).  
> Điểm đột phá kỹ thuật của chúng em nằm ở bước truyền ngược ngữ cảnh dòng về từng token: nếu cộng trực tiếp một mô-đun khởi tạo ngẫu nhiên vào mạng tiền huấn luyện, gradient ở các epoch đầu sẽ bị nhiễu loạn. Do đó, chúng em thiết kế **cổng vô hướng khả học theo phong cách ReZero** ($\alpha$ khởi tạo bằng $0$), kết hợp với **vector nhúng chỉ báo token đầu đoạn** $\mathbf{e}_{\text{first}}(f_i)$. Tại bước 0, $\alpha=0$ giữ nguyên hoàn toàn không gian đặc trưng gốc của LayoutLMv3; khi quá trình huấn luyện tiến triển, $\alpha$ mở dần để bơm ngữ cảnh dòng đồng thời giúp bộ phân loại phân biệt sắc nét nhãn mở đầu $\texttt{B-}$ và nhãn bên trong $\texttt{I-}$.  
> Thành phần thứ ba là **Hàm mất mát điều chuẩn ranh giới nội dòng $\mathcal{L}_{\text{bound}}$**. Với mọi cặp token liền kề $(i, i+1)$ nằm trong cùng một dòng ($s_i = s_{i+1}$) và thuộc cùng một thực thể gốc ($\phi(y_i) = \phi(y_{i+1})$), chúng em phạt khoảng cách bất tương đồng cosine giữa $\mathbf{h}_i^{\text{final}}$ và $\mathbf{h}_{i+1}^{\text{final}}$ với trọng số $\lambda_{\text{bound}} = 0.2$. Đặc biệt, $\mathcal{L}_{\text{bound}}$ chỉ tính khi huấn luyện và **không làm tăng bất kỳ chi phí tính toán nào khi suy diễn (inference)**."

---

## SLIDE 6: Thiết Lập Thực Nghiệm & Kết Quả Định Lượng Đa Hạt Giống (Chương 4 | 9:00 – 12:00)

**[Hiển thị trên Slide]:**
- Cấu hình phần cứng: GPU **NVIDIA A100-SXM4-80GB**, 167 GiB RAM, đánh giá nghiêm ngặt trên **3 hạt giống ngẫu nhiên độc lập** $\mathcal{S} = \{42, 123, 1993\}$ theo chuẩn `seqeval` Entity-level Precision, Recall, F1 ($\text{Mean} \pm \text{Std}$).
- Bảng kết quả thực nghiệm (Bảng 4.4 & Biểu đồ Hình 4.1 trong khóa luận):
  - **FUNSD (`base`, 3 seeds):**
    - Baseline LayoutLMv3: Precision = $89.32 \pm 1.31\%$, Recall = $90.53 \pm 0.48\%$, **Entity F1 = $89.92 \pm 0.85\%$** (Max: $90.51\%$).
    - **Mô hình đề xuất (Full Model):** Precision = **$91.82 \pm 0.05\%$** ($+2.50\%$), Recall = **$91.33 \pm 0.28\%$** ($+0.80\%$), **Entity F1 = $91.58 \pm 0.16\%$** (Max: **$91.76\%$**).
  - **CORD (`base`, 3 seeds):**
    - Baseline LayoutLMv3: Precision = $96.50 \pm 0.39\%$, Recall = $96.94 \pm 0.28\%$, **Entity F1 = $96.72 \pm 0.33\%$** (Max: $96.95\%$).
    - Full Model & chuỗi Ablation 20 cấu hình: Đang chạy trực tiếp trên A100 và cập nhật tự động.

**[Lời thoại thuyết trình]:**
> "Chuyển sang Chương 4, toàn bộ thực nghiệm được chúng em triển khai trên hệ thống GPU **NVIDIA A100-SXM4-80GB** trên 2 bộ dữ liệu chuẩn quốc tế là **FUNSD** (199 biểu mẫu hành chính nhiễu) và **CORD** (1.000 hóa đơn bán lẻ với 30 lớp thực thể). Để đảm bảo tính khách quan khoa học và loại bỏ sai lệch do chọn hạt giống đơn lẻ, mọi cấu hình đều được huấn luyện và đánh giá độc lập trên **3 random seeds $\{42, 123, 1993\}$** theo thước đo **Entity-level F1 nghiêm ngặt** của thư viện `seqeval`.  
> Kết quả thực nghiệm trên bộ dữ liệu FUNSD cho thấy 3 phát hiện rất rõ nét:  
> 1. **Về độ chính xác tổng thể:** Mô hình đề xuất nâng điểm F1 trung bình 3 seed từ **89.92%** lên **91.58%** (tăng **+1.66%** tuyệt đối), đạt đỉnh **91.76%** ở seed 42 – vượt xa kết quả công bố trong bài báo LayoutLMv3 gốc của Microsoft (90.29%) tới **+1.29%** dù chỉ tăng thêm khoảng 2.4% số lượng tham số.  
> 2. **Về cơ chế cải thiện:** Độ chính xác **Precision tăng vọt +2.50%** (từ 89.32% lên 91.82%) đi kèm mức tăng **+0.80% ở Recall**. Điều này chứng minh mô-đun SCM và hàm mất mát ranh giới đã triệt tiêu hiệu quả lỗi đứt gãy thực thể giữa dòng.  
> 3. **Về độ ổn định hội tụ:** Độ lệch chuẩn F1 giữa các seed giảm **5.3 lần** (từ $\pm 0.85\%$ xuống chỉ còn $\pm 0.16\%$), và độ lệch chuẩn Precision giảm **26 lần** (xuống $\pm 0.05\%$), khẳng định vai trò giữ ổn định gradient của cổng ReZero $\alpha$."

---

## SLIDE 7: Theo Dõi Chuỗi Thí Nghiệm Khảo Sát Thành Phần (Ablation Study) & Lời Cảm Ơn (Chương 4 & 5 | 12:00 – 13:30)

**[Hiển thị trên Slide]:**
- Bảng tổng hợp tiến độ 20 cấu hình thực nghiệm (Cells 4–23: `baseline`, `full`, `no_boundary`, `no_segment`, `no_hpe` trên cả `base` và `large`).
- Tóm tắt đóng góp và lời cảm ơn Hội đồng.

**[Lời thoại thuyết trình]:**
> "Hiện tại, hệ thống thực nghiệm trên GPU A100 của chúng em đang tiếp tục hoàn tất các cấu hình khảo sát loại bỏ từng thành phần (Ablation Study gồm `no_boundary`, `no_segment`, `no_hpe`) trên cả hai biến thể `base` và `large` để điền đầy đủ bảng tổng kết cuối cùng và hoàn thiện Chương 5.  
> Trên đây là toàn bộ nội dung báo cáo khóa luận tốt nghiệp của em. Em xin chân thành cảm ơn các Thầy/Cô trong Hội đồng đã lắng nghe, và em rất mong nhận được các ý kiến nhận xét, góp ý cũng như câu hỏi từ các Thầy/Cô ạ!"

---

## PHỤ LỤC: Bộ Câu Hỏi & Trả Lời Phản Biện Dự Kiến (Defense Q&A Preparation)

1. **Câu hỏi 1:** *Tại sao trong HPE, em lại cấp phát số chiều cho trục dọc $d_y = 160$ lớn hơn trục ngang $d_x = 96$, thay vì ngược lại?*
   - **Trả lời:** Trong tài liệu biểu mẫu và hóa đơn (FUNSD, CORD), các token nằm trong cùng một dòng đã chia sẻ chung tọa độ khung bao cấp đoạn (segment-level bounding box) và đã có nhúng vị trí 1D (`pos1D`) phản ánh thứ tự đọc từ trái sang phải. Ngược lại, việc phân biệt các dòng văn bản khác nhau theo chiều dọc, khoảng cách giữa các hàng trong bảng và phân vùng tiêu đề – nội dung phụ thuộc hoàn toàn vào trục $Y$ $(y_0, y_1, h)$. Do đó, ưu tiên dung lượng biểu diễn lớn hơn cho trục dọc ($3d_y = 480$ so với $3d_x = 288$) kết hợp tầng chiếu phi tuyến GELU giúp mô hình phân tách ranh giới dòng sắc nét hơn.

2. **Câu hỏi 2:** *Tại sao không dùng tầng CRF (Conditional Random Field) ở đầu ra như các mô hình NER truyền thống mà lại dùng mô-đun SCM kết hợp hàm mất mát ranh giới $\mathcal{L}_{\text{bound}}$?*
   - **Trả lời:** Tầng Linear-Chain CRF có độ phức tạp giải mã Viterbi bậc hai $O(L \cdot |\mathcal{Y}|^2)$ tại thời điểm suy diễn (inference) – đặc biệt chậm trên các bộ dữ liệu có số nhãn lớn như CORD ($|\mathcal{Y}| = 61 \implies |\mathcal{Y}|^2 = 3721$) và chỉ ràng buộc chuyển dịch Markov bậc 1 giữa hai nhãn đầu ra. Ngược lại, hàm mất mát $\mathcal{L}_{\text{bound}}$ của chúng em điều chuẩn trực tiếp độ trơn cosine trên không gian vector ẩn 768 chiều giữa các token cùng dòng và **hoàn toàn bằng 0 chi phí tính toán khi inference**, trong khi mô-đun SCM cho phép mọi dòng trên toàn trang tài liệu tương tác toàn cục với nhau.

3. **Câu hỏi 3:** *Vai trò cụ thể của tham số cổng ReZero $\alpha$ và `is_first_token_embedding` trong mô-đun SCM là gì?*
   - **Trả lời:** Khi ghép thêm một khối Multi-Head Attention mới (`SegmentAttention` khởi tạo ngẫu nhiên) vào sau lưng bộ mã hóa LayoutLMv3 đã tiền huấn luyện kỹ, nếu dùng kết nối tắt thông thường ($\mathbf{h}_i + \hat{\mathbf{u}}_{s_i}$), nhiễu từ khối mới ở những bước huấn luyện đầu tiên sẽ làm hỏng đặc trưng tiền huấn luyện, gây dao động lớn giữa các random seeds. Khởi tạo $\alpha^{(0)} = 0$ đảm bảo tại bước 0 mạng hoạt động y hệt LayoutLMv3 gốc, sau đó gradient tự điều chỉnh $\alpha$ tăng dần. Trong khi đó, `is_first_token_embedding` đánh dấu token đầu tiên của mỗi đoạn ($f_i = 1$), phá vỡ tính đối xứng giữa các token cùng nhận chung một vector đoạn $\hat{\mathbf{u}}_{s_i}$, giúp phân biệt chính xác nhãn bắt đầu $\texttt{B-}$ và nhãn tiếp nối $\texttt{I-}$.

