# CÂU TRẢ LỜI KHI GIẢNG VIÊN HỎI VỀ DBO VÀ IDBO

## 1. Câu quan trọng nhất cần nhớ

> Nhóm đã thử DBO và IDBO trong nhiều cấu hình nhưng chưa ghi nhận IDBO cho kết quả tốt hơn DBO. Nhóm đã kiểm tra riêng và xác nhận IDBO có cơ chế hoạt động khác DBO, không phải hệ thống gọi nhầm cùng một thuật toán. Tuy nhiên, trong thử nghiệm chính, phần bổ sung của IDBO chưa tạo ra cải thiện về điểm số. Vì vậy, nhóm báo cáo trung thực rằng IDBO khác DBO về cách hoạt động nhưng chưa chứng minh được tốt hơn về kết quả.

---

## 2. Câu trả lời ngắn trong khoảng 20 giây

### Nếu giảng viên hỏi: “DBO và IDBO có khác nhau không?”

> Dạ có khác về cách hoạt động. IDBO có thêm bước xáo trộn và khởi động lại khi quá trình tìm kiếm bị kẹt hoặc các phương án trở nên quá giống nhau. Nhóm đã kiểm tra riêng và xác nhận những bước bổ sung này có thể hoạt động. Tuy nhiên, trong thử nghiệm chính, DBO và IDBO vẫn cho kết quả tương đương.

### Nếu giảng viên hỏi: “IDBO có tốt hơn DBO không?”

> Dạ hiện tại nhóm chưa có đủ bằng chứng để nói IDBO tốt hơn DBO. Trên 10 lần chạy cùng điều kiện, hai thuật toán có cùng điểm tốt nhất và cùng điểm trung bình. Vì vậy nhóm chỉ kết luận rằng IDBO có cơ chế khác, nhưng chưa cải thiện kết quả trong phạm vi thử nghiệm hiện tại.

---

## 3. Câu trả lời đầy đủ khi trình bày slide kết quả

> Nhóm so sánh DBO và IDBO trong cùng điều kiện, cùng dữ liệu và cùng 10 hạt giống ngẫu nhiên. Kết quả cho thấy cả hai cùng đạt điểm tốt nhất 99,5106 và điểm trung bình 98,2148. Vì vậy, nhóm không kết luận IDBO tốt hơn DBO.
>
> Nhóm tiếp tục kiểm tra xem hai thuật toán có thật sự chạy khác nhau hay không. Trong cấu hình thử nghiệm chính, phần bổ sung của IDBO không được kích hoạt nên IDBO hoạt động gần giống DBO. Sau đó, nhóm dùng một cấu hình kiểm tra riêng và ghi nhận cơ chế bổ sung của IDBO đã hoạt động. Điều này xác nhận code IDBO có cơ chế riêng và hệ thống không gọi nhầm DBO.
>
> Tuy nhiên, cấu hình kiểm tra riêng chỉ dùng để xác nhận cơ chế hoạt động, không dùng để chứng minh IDBO tốt hơn. Kết luận hiện tại của nhóm là IDBO khác DBO về cách hoạt động, nhưng chưa cho kết quả tốt hơn trong thử nghiệm chính.

---

## 4. Các câu hỏi giảng viên có thể hỏi

### Câu 1: “Nhóm đã thử những trường hợp nào?”

> Dạ nhóm đã thử cấu hình chính với 25 vòng, sau đó thử các cấu hình dài hơn với 100 và 150 vòng. Nhóm cũng thay đổi thời gian chờ trước khi phát hiện quá trình bị kẹt và ngưỡng kích hoạt cơ chế bổ sung. Tuy nhiên, trong các cấu hình so sánh chính, DBO và IDBO vẫn cho kết quả giống nhau. Nhóm còn dùng một cấu hình kiểm tra riêng để xác nhận cơ chế IDBO có thể hoạt động.

### Câu 2: “Vậy tại sao kết quả của hai thuật toán giống nhau?”

> Dạ trong các cấu hình chính, phần bổ sung của IDBO không được kích hoạt nên IDBO hoạt động gần giống DBO. Vì vậy, khi hai thuật toán dùng cùng dữ liệu và cùng hạt giống, hai thuật toán có thể đi theo quá trình tìm kiếm giống nhau và cho cùng kết quả. Nhóm đang đo thêm mức độ đa dạng và mức độ bị kẹt để xác định chính xác điều kiện nào làm IDBO phát huy tác dụng.

### Câu 3: “Có phải code gọi nhầm DBO cho IDBO không?”

> Dạ nhóm đã kiểm tra việc lựa chọn thuật toán và xác nhận DBO với IDBO được gọi bằng hai lớp riêng. Ngoài ra, trong cấu hình kiểm tra riêng, IDBO đã ghi nhận các lần xáo trộn và khởi động lại, trong khi DBO không có các cơ chế này. Do đó, nhóm không cho rằng hệ thống đang gọi nhầm cùng một thuật toán.

### Câu 4: “Nếu IDBO chưa tốt hơn thì cải tiến nằm ở đâu?”

> Dạ phần cải tiến nằm ở khả năng xáo trộn và khởi động lại quá trình tìm kiếm khi bị kẹt. Nhóm đã xác nhận cơ chế này tồn tại và có thể hoạt động. Tuy nhiên, có cơ chế bổ sung không đồng nghĩa với việc chắc chắn đạt kết quả tốt hơn trên mọi bài toán. Với bài toán và cấu hình hiện tại, nhóm chưa quan sát được lợi ích về điểm số.

### Câu 5: “Như vậy IDBO có thất bại không?”

> Dạ nhóm chưa xem đây là thất bại của code, vì cơ chế IDBO đã hoạt động trong thử nghiệm kiểm tra riêng. Kết quả hiện tại chỉ cho thấy IDBO chưa tạo lợi thế trên bài toán và cấu hình đang dùng. Nhóm xem đây là một giới hạn thực nghiệm cần báo cáo trung thực và tiếp tục nghiên cứu.

### Câu 6: “Tại sao vẫn dùng IDBO cho đề tài?”

> Dạ IDBO vẫn là hướng nghiên cứu chính vì có thêm cơ chế giúp quá trình tìm kiếm thoát khỏi trạng thái bị kẹt. Trong kết quả hiện tại, IDBO cũng không kém DBO về điểm số. Ngoài phần thuật toán, đề tài còn có bộ giải hai tầng, tự chọn món, điều chỉnh khẩu phần, lập kế hoạch 7 ngày, hạn chế lặp món, kiểm thử và tích hợp Web. Nhóm tiếp tục giữ khả năng chuyển đổi giữa DBO và IDBO để đánh giá thêm mà không phải viết lại hệ thống.

### Câu 7: “Web tuần 10 sẽ dùng DBO hay IDBO?”

> Dạ Web có thể dùng IDBO làm lựa chọn mặc định theo định hướng đề tài, nhưng phần kết nối được thiết kế để có thể đổi giữa DBO và IDBO. Nhóm không dùng Web để chứng minh IDBO tốt hơn. Việc tích hợp Web và việc đánh giá thuật toán được tách thành hai phần riêng.

### Câu 8: “Nhóm sẽ làm gì tiếp theo?”

> Dạ nhóm sẽ ghi trực tiếp mức độ đa dạng, số vòng không cải thiện, số lần xáo trộn và số lần khởi động lại. Sau đó nhóm chạy so sánh theo từng cặp cùng hạt giống và kiểm tra các trường hợp khó hơn. Mục tiêu là xác định IDBO hữu ích trong điều kiện nào, chứ không điều chỉnh tham số chỉ để ép IDBO thắng.

### Câu 9: “Nếu cuối cùng IDBO vẫn không tốt hơn thì sao?”

> Dạ nhóm sẽ báo cáo đúng kết quả rằng IDBO có cơ chế tìm kiếm khác nhưng chưa cải thiện đáng kể trên bộ bài toán hiện tại. Nhóm sẽ trình bày nguyên nhân được quan sát, giới hạn của cách đo và hướng điều chỉnh phù hợp. Một kết quả chưa có cải thiện nhưng được kiểm tra và giải thích rõ vẫn có giá trị hơn một kết luận tốt hơn nhưng không có đủ bằng chứng.

### Câu 10: “Nhóm có đang cố thay đổi tham số để làm IDBO thắng không?”

> Dạ không. Cấu hình kiểm tra riêng chỉ dùng để xác nhận cơ chế IDBO có hoạt động. Khi so sánh hiệu năng, DBO và IDBO phải dùng cùng dữ liệu, cùng hạt giống, cùng số cá thể, cùng số vòng và cùng cách tính điểm. Nếu IDBO hòa hoặc kém hơn, nhóm vẫn giữ và báo cáo kết quả đó.

---

## 5. Nếu giảng viên hỏi về các con số trên slide

### “99,5106 và 98,2148 là gì?”

> 99,5106 là điểm tốt nhất mà cả hai thuật toán đạt được. 98,2148 là điểm trung bình qua 10 lần chạy. Điểm càng cao thì phương án càng gần các mục tiêu kỹ thuật đã đặt ra.

### “0/10 vi phạm nghĩa là gì?”

> Nghĩa là trong 10 lần chạy được báo cáo, nhóm không ghi nhận vi phạm trong bộ điều kiện kỹ thuật của thử nghiệm tuần 8. Con số này không có nghĩa là thực đơn đã được chứng nhận an toàn y tế.

### “Tại sao IDBO chậm hơn?”

> IDBO phải theo dõi thêm tình trạng của quần thể và kiểm tra điều kiện xáo trộn hoặc khởi động lại. Vì vậy IDBO có thêm chi phí xử lý, dù trong thử nghiệm chính các cơ chế bổ sung chưa tạo cải thiện về điểm số.

### “30 lần ở tầng ngoài và 8 098 lần ở tầng trong nghĩa là gì?”

> Đây là tổng số lần cơ chế bổ sung của IDBO được kích hoạt trong cấu hình kiểm tra riêng. Số 8 098 là số cộng dồn qua rất nhiều lần giải tầng trong, không phải 8 098 lần trong một vòng đơn lẻ. Các con số này chỉ xác nhận cơ chế hoạt động, không chứng minh cấu hình đó tốt hơn.

---

## 6. Những câu không nên nói

Không nên nói:

> “Tụi em chạy mãi vẫn giống nhau nên không biết sao.”

Nên nói:

> “Trong phạm vi thử nghiệm hiện tại, nhóm chưa ghi nhận khác biệt về chất lượng nghiệm.”

Không nên nói:

> “IDBO chắc chắn tốt hơn nhưng dữ liệu chưa thể hiện.”

Nên nói:

> “Nhóm chưa có đủ bằng chứng để kết luận IDBO tốt hơn.”

Không nên nói:

> “Chắc do bài toán quá dễ.”

Nên nói:

> “Độ khó của bài toán là một giả thuyết đang được kiểm tra, chưa phải kết luận.”

Không nên nói:

> “Code chắc chắn không có lỗi.”

Nên nói:

> “Nhóm đã xác nhận việc lựa chọn thuật toán và cơ chế IDBO hoạt động trong thử nghiệm kiểm tra riêng; nhóm vẫn tiếp tục kiểm tra điều kiện kích hoạt trong bài toán chính.”

Không nên nói:

> “Nhóm tăng tham số để IDBO tốt hơn.”

Nên nói:

> “Nhóm dùng cấu hình riêng để kiểm tra cơ chế, không dùng cấu hình đó để so sánh hiệu năng.”

---

## 7. Đoạn nói trực tiếp khi đến slide DBO và IDBO

> Trong 10 lần chạy cùng điều kiện, DBO và IDBO có cùng điểm tốt nhất là 99,5106 và cùng điểm trung bình là 98,2148. Vì vậy nhóm chưa kết luận IDBO tốt hơn DBO. Nhóm đã kiểm tra riêng và xác nhận IDBO có cơ chế xáo trộn và khởi động lại, nên hai thuật toán không phải là một. Tuy nhiên, trong thử nghiệm chính, các cơ chế bổ sung này chưa tạo ra cải thiện về kết quả. Kết luận hiện tại là IDBO khác DBO về cách hoạt động, nhưng chưa tốt hơn DBO trong phạm vi thử nghiệm.

---

## 8. Câu kết thúc nếu bị hỏi sâu nhưng chưa có kết quả mới

> Phần này nhóm chưa muốn kết luận vượt quá dữ liệu đang có. Nhóm đã xác định được rằng IDBO có cơ chế riêng và có thể hoạt động, nhưng chưa xác định được trường hợp nào cơ chế đó tạo lợi thế rõ ràng. Nhóm đang chạy thêm phép đo về mức độ đa dạng và mức độ bị kẹt. Khi có kết quả, nhóm sẽ cập nhật bằng số liệu theo từng cặp chạy, thay vì suy đoán.

---

## 9. Phiên bản cực ngắn để học thuộc

> DBO và IDBO có cơ chế khác nhau. Nhóm đã xác nhận cơ chế bổ sung của IDBO có thể hoạt động, nên không phải gọi nhầm thuật toán. Tuy nhiên, trong các thử nghiệm chính, hai thuật toán vẫn cho kết quả tương đương. Vì vậy nhóm chưa kết luận IDBO tốt hơn, mà đang tiếp tục tìm điều kiện phù hợp để IDBO phát huy tác dụng.

---

## 10. Bốn ý tuyệt đối không được quên

1. **DBO và IDBO được chạy trong cùng điều kiện để so sánh công bằng.**
2. **IDBO có cơ chế khác và cơ chế đó đã được kiểm tra riêng.**
3. **Kết quả chính hiện vẫn tương đương nên chưa được nói IDBO tốt hơn.**
4. **Nhóm tiếp tục đo và tìm điều kiện phù hợp, không ép tham số để tạo kết quả đẹp.**
