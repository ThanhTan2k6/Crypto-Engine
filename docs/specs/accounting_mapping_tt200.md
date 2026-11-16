# Specification: Accounting Mapping & Valuation Standard (Circular 200/2014/TT-BTC)

## 1. Mục đích & Cơ sở Pháp lý
Tài liệu này chuẩn hóa quy tắc hạch toán và định giá tài sản số (Crypto Assets) theo tinh thần **Thông tư 200/2014/TT-BTC** của Bộ Tài chính Việt Nam áp dụng cho hệ thống `CryptoIntel-Engine`:
- Phục vụ việc quản lý danh mục đầu tư tích sản (Spot Accumulation) minh bạch, có kiểm toán.
- Tách bạch giữa **Lợi nhuận đã thực hiện (Realized PnL)** và **Chênh lệch đánh giá lại chưa thực hiện (Unrealized PnL)**.
- Thiết lập quy tắc trích lập dự phòng giảm giá tài sản tài chính số (Impairment Provisions) để quản trị rủi ro bảng cân đối kế toán.

---

## 2. Ánh xạ Hệ thống Tài khoản (Chart of Accounts Mapping)

| Mã TK theo TT 200 | Tên Tài khoản / Bản chất | Ứng dụng trong CryptoIntel-Engine |
|---|---|---|
| **TK 112** | Tiền gửi ngân hàng / Tiền tệ tương đương | Tiền gửi pháp định (VND, USD) trên các tài khoản giao dịch. |
| **TK 121** | Chứng khoán kinh doanh (Trading Securities) | Tài sản Crypto nắm giữ ngắn hạn cho chiến lược **Swing/Position Trading** (ví dụ: BTC, ETH lướt sóng). |
| **TK 128** | Đầu tư nắm giữ đến ngày đáo hạn | Các hợp đồng Staking cố định, Cho vay phi tập trung (Lending/Earn) có kỳ hạn. |
| **TK 228** | Đầu tư dài hạn khác (Long-term Investments) | Tài sản Crypto nắm giữ chiến lược cho **Spot Accumulation (Tích sản dài hạn)** lưu trữ tại ví lạnh (Cold Storage). |
| **TK 229 (2291)** | Dự phòng giảm giá chứng khoán / tài sản đầu tư | Khoản trích lập dự phòng khi giá trị thị trường (Mark-to-Market) thấp hơn giá gốc ghi sổ. |
| **TK 515** | Doanh thu hoạt động tài chính | Lãi thực hiện từ chốt lời (Realized Gain), lãi nhận được từ Funding Rate dương hoặc Staking rewards. |
| **TK 635** | Chi phí tài chính | Lỗ thực hiện khi cắt lỗ (Realized Loss), phí trả Funding Rate, phí giao dịch sàn (CEX/DEX fees). |
| **TK 412** | Chênh lệch đánh giá lại tài sản | Theo dõi biến động giá trị tài sản chưa thực hiện (Unrealized PnL) cuối kỳ kế toán. |

---

## 3. Quy tắc Định giá & Trích lập Dự phòng (Valuation & Impairment Rules)

### 3.1. Phương pháp tính giá xuất kho / thanh lý
Hệ thống mặc định áp dụng phương pháp **FIFO (Nhập trước - Xuất trước)** hoặc **Bình quân gia quyền di động (Moving Weighted Average)** cho toàn bộ giao dịch mua tích sản:
$$\text{Cost Basis} = \frac{\sum (\text{Quantity}_i \times \text{Entry Price}_i)}{\sum \text{Quantity}_i}$$

### 3.2. Quy tắc Trích lập Dự phòng (TK 2291)
Vào cuối mỗi chu kỳ kế toán (ngày cuối tháng/quý):
$$\text{Mức trích lập dự phòng} = \max(0, \text{Giá gốc ghi sổ} - \text{Giá thị trường hợp lý (Mark Price Binance)})$$
- Nếu giá trị thị trường giảm xuống dưới giá vốn $\rightarrow$ Ghi nhận Chi phí Tài chính (Nợ TK 635 / Có TK 2291).
- Nếu giá trị thị trường phục hồi $\rightarrow$ Hoàn nhập dự phòng (Nợ TK 2291 / Có TK 635).

### 3.3. Tách biệt tuyệt đối Realized vs Unrealized PnL
- **Chỉ ghi nhận vào Doanh thu Tài chính (TK 515)** khi vị thế đã được đóng hoàn toàn sang Tiền pháp định hoặc Stablecoin (USDT/USDC).
- Tuyệt đối không phân phối lợi nhuận dựa trên lợi nhuận giấy (Unrealized Paper Gains) để ngăn chặn rủi ro mất thanh khoản khi thị trường đảo chiều.
