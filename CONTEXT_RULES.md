# ==============================================================================
# CRYPTOINTEL-ENGINE: ARCHITECTURAL SPECIFICATION & CONTEXT RULES
# Standard: Strict Production-Grade Quant + Multi-Agent Socratic Framework
# ==============================================================================

## 1. TỔNG QUAN HỆ THỐNG & TRIẾT LÝ CỐT LÕI (CORE PHILOSOPHY)

### 1.1. Định vị Dự án
**CryptoIntel-Engine** là hệ sinh thái kết hợp giữa **Toán học Định lượng Xác thực (Deterministic Quantitative Engine)** và **Mạng lưới Đa tác tử Phản biện (LangGraph Multi-Agent Socratic Network)**, phục vụ 2 trường phái giao dịch:
1. **Mua tích sản (Spot Accumulation / DCA thông minh)**: Tối ưu hóa điểm vào hàng dài hạn theo chu kỳ kinh tế vĩ mô và dòng tiền tích lũy ví lạnh.
2. **Giao dịch theo xu hướng (Swing/Position Trading)**: Khai thác xung lực dòng tiền ngắn-trung hạn, phòng tránh bẫy thanh lý phái sinh và đòn bẩy.

### 1.2. Nguyên tắc Bất biến (Ironclad Rules)
> [!IMPORTANT]
> **TÁCH BIỆT TUYỆT ĐỐI GIỮA QUANT VÀ AI (ZERO-HALLUCINATION QUANTITATIVE BOUNDARY)**
> - **Lớp Định lượng (Deterministic Quant Layer)**: Tính toán toán học, chỉ báo kỹ thuật, chênh lệch funding rate, open interest delta, exchange netflow z-score. Toàn bộ logic chạy bằng Python thuần (NumPy/Pandas/Polars), chạy độc lập, **AI TUYỆT ĐỐI KHÔNG ĐƯỢC TỰ TÍNH TOÁN LẠI TOÁN HỌC**.
> - **Lớp Đa tác tử AI (LangGraph Reasoning Layer)**: AI chỉ nhận đầu vào là các `Pydantic v2 Models` đã được kiểm chuẩn tính hợp lệ (validated JSON facts). AI đóng vai trò:
>   - Đọc hiểu bối cảnh liên thị trường.
>   - Giải mã hành vi động cơ (Intention & Behavioral Economics).
>   - Đóng vai **Socratic Devil's Advocate (Luật sư của quỷ)** nhằm tạt nước lạnh vào tâm lý FOMO, tìm điểm gãy của luận điểm đầu tư.
> - **Không bao giờ "Vuốt đuôi" hay "Cheerleading"**: AI không khen ngợi lệnh mua của user; AI có nhiệm vụ tìm lý do tại sao lệnh đó CÓ THỂ CHÁY HOẶC ĐU ĐỈNH.

---

## 2. 3 TRỤ CỘT DỮ LIỆU THỜI GIAN THỰC (FREE & REAL-TIME DATA STACK)

### Trụ cột 1: Real-time Market & Derivatives (Binance / Bybit Public API)
- **Phương thức kết nối**: WebSocket Streams + REST API công khai (Public Endpoints, **0 API Key required**).
- **Tham số thu thập**:
  - `Mark Price`, `Index Price`, `Last Traded Price`.
  - `Volume 24h` & `Volume Z-score` (so với trung bình 20 ngày).
  - `Open Interest (OI)` & `OI Delta` (tốc độ gia tăng hợp đồng mở theo 1h, 4h, 24h).
  - `Funding Rate` (hiện tại, dự phóng 8h tới, và annualized funding rate).
  - `Long/Short Ratio` & `Top Trader Long/Short Ratio`.
  - `Liquidation Heatmap Proxy`: Dựa trên biến động OI quanh các vùng hỗ trợ/kháng cự cục bộ.

### Trụ cột 2: Macro & Lãi suất FED (FRED API & CME FedWatch)
- **Phương thức kết nối**: FRED API (Federal Reserve Economic Data - Free API Key) + Web Scraping / Public feeds của CME FedWatch Tool.
- **Tham số thu thập**:
  - `Federal Funds Effective Rate (DFF)` & kỳ vọng tăng/giảm lãi suất kỳ họp FOMC kế tiếp.
  - `US Consumer Price Index (CPIAUCSL)` & `Core PCE`.
  - `US Dollar Index (DXY)` & `US 10Y Treasury Yield (DGS10)`.
  - `US 10Y-2Y Yield Curve Spread (T10Y2Y)`: Cảnh báo suy thoái / Đảo ngược đường cong lợi suất.
  - `M2 Money Supply YoY Delta`: Đo lường thanh khoản toàn cầu.
- **Phân loại Chế độ Vĩ mô (Macro Regime)**:
  - `RISK-ON (Expansionary)`: Lãi suất hạ, M2 tăng, DXY suy yếu $\rightarrow$ An toàn cho Spot Accumulation.
  - `RISK-OFF (Contractionary)`: Thắt chặt định lượng (QT), DXY bứt phá, Lợi suất TP tăng $\rightarrow$ Ưu tiên tiền mặt hoặc phòng hộ.
  - `STAGFLATION / UNCERTAINTY`: Lạm phát neo cao nhưng tăng trưởng suy giảm $\rightarrow$ Chỉ lướt sóng ngắn hạn (Swing), cấm đòn bẩy lớn.

### Trụ cột 3: Dấu chân Cá voi (Whale Tracking & Exchange Netflows)
- **Phương thức kết nối**: Public CEX Reserve APIs, Mempool Monitor, Whale Alert RSS/X scraper hoặc On-chain CEX Inflow/Outflow Aggregator endpoints miễn phí.
- **Tham số thu thập**:
  - `Exchange Netflow (24h)`: $Netflow = Inflow - Outflow$.
    - $Netflow \gg 0$ (Inflow đột biến): Rủi ro cá voi nạp lên sàn chuẩn bị xả hàng (Distribution Alert).
    - $Netflow \ll 0$ (Outflow đột biến): Dấu hiệu cá voi rút về ví lạnh lưu trữ lâu dài (Accumulation Sign).
  - `Whale Transaction Count (> $1,000,000)`: Số giao dịch quy mô lớn dịch chuyển trong 4h qua.
  - `Stablecoin Inflow Ratio (USDT, USDC on CEX)`: Đo lường lực mua tiềm tàng chực chờ bắt đáy.

---

## 3. CONTRACTS DỮ LIỆU ĐỊNH LƯỢNG (PYDANTIC V2 DATA SCHEMAS)

```python
from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class MacroRegime(str, Enum):
    RISK_ON = "RISK_ON"
    RISK_OFF = "RISK_OFF"
    NEUTRAL_UNCERTAIN = "NEUTRAL_UNCERTAIN"

class MarketMetrics(BaseModel):
    symbol: str = Field(..., example="BTCUSDT")
    timestamp: datetime
    current_price: float
    volume_24h: float
    volume_zscore_20d: float
    open_interest: float
    oi_change_24h_pct: float
    current_funding_rate: float
    annualized_funding_rate: float
    long_short_ratio: float
    derivatives_risk_level: str = Field(..., description="LOW, ELEVATED, EXTREME_LIQUIDATION_RISK")

class MacroMetrics(BaseModel):
    fed_funds_rate: float
    next_fomc_rate_cut_prob: float
    cpi_yoy: float
    dxy_index: float
    yield_10y: float
    yield_curve_inverted: bool
    regime: MacroRegime
    macro_score: float = Field(..., ge=-10.0, le=10.0, description="Dưới -3: Risk-off nặng; Trên +3: Risk-on")

class WhaleFlowMetrics(BaseModel):
    symbol: str
    netflow_24h_usd: float
    netflow_zscore: float
    whale_transfers_count_1m_plus: int
    exchange_reserve_trend: str = Field(..., description="DEPLETING (Good), INFLATING (Dangerous)")
    stablecoin_reserve_trend: str = Field(..., description="INFLOWING (Buying Power), OUTFLOWING")
    whale_sentiment: str = Field(..., description="ACCUMULATION, DISTRIBUTION, NEUTRAL")

class DeterministicSignals(BaseModel):
    market: MarketMetrics
    macro: MacroMetrics
    whale: WhaleFlowMetrics
    spot_accumulation_score: float = Field(..., ge=0.0, le=100.0)
    swing_trend_score: float = Field(..., ge=0.0, le=100.0)
    hard_red_flags: List[str] = Field(default_factory=list)
```

---

## 4. MẠNG LƯỚI ĐA TÁC TỬ PHẢN BIỆN (LANGGRAPH MULTI-AGENT ARCHITECTURE)

```
                       +-----------------------+
                       |    Raw Data Sources   |
                       | (Binance, FRED, CEX)  |
                       +-----------+-----------+
                                   |
                                   v
                       +-----------------------+
                       |  Deterministic Quant  | (Pure Math / Pydantic v2)
                       |  No Hallucination     |
                       +-----------+-----------+
                                   |
                                   v
                       +-----------------------+
                       |   Supervisor Agent    |
                       +-----------+-----------+
                                   |
         +-------------------------+-------------------------+
         |                         |                         |
         v                         v                         v
+------------------+     +-------------------+     +--------------------+
|  Macro & FED     |     | Whale Flow        |     | Derivatives &      |
|  Strategist      |     | Analyst Agent     |     | Sentiment Agent    |
+--------+---------+     +---------+---------+     +---------+----------+
         |                         |                         |
         +-------------------------+-------------------------+
                                   |
                                   v
                       +-----------------------+
                       |   SOCRATIC DEVIL'S    | <--- Trọng tâm phản biện FOMO
                       |    ADVOCATE AGENT     |      Đặt 3 câu hỏi triệt hạ
                       +-----------+-----------+
                                   |
                                   v
                       +-----------------------+
                       |  Synthesis & Verdict  |
                       | (Spot vs Swing Action)|
                       +-----------------------+
```

### 4.1. Chi tiết từng Tác tử trong Graph

#### 1. Supervisor Agent
- **Nhiệm vụ**: Nhận `DeterministicSignals` từ Quant Engine. Kiểm tra tính toàn vẹn của Pydantic schema, khởi tạo `CryptoIntelState`, phân luồng cho 3 tác tử phân tích chuyên sâu chạy song song.
- **Tiêu chuẩn output**: Payload chuẩn hóa, không tự biên soạn thông tin ngoài dữ liệu được nạp.

#### 2. Macro & FED Strategist Agent
- **Nhiệm vụ**: Đánh giá bối cảnh vĩ mô toàn cầu. Phân tích tác động của động thái FED, chính sách lãi suất, thanh khoản DXY đến chu kỳ dài hạn của Bitcoin và thị trường Crypto.
- **Mục tiêu**: Trả lời câu hỏi: *"Thị trường đang được bơm thanh khoản hay đang bị hút máu về trái phiếu chính phủ Mỹ?"*

#### 3. Whale Flow Analyst Agent
- **Nhiệm vụ**: Bóc trần ý đồ đằng sau các luồng nạp/rút CEX 24h. Xác định xem cá voi đang âm thầm gom hàng vào ví lạnh (Smart Money Accumulation) hay đang chuyển coin lên sàn để phân phối/xả hàng vào đầu nhỏ lẻ (Retail Distribution).
- **Mục tiêu**: Đưa ra kết luận minh bạch về trạng thái dòng tiền Smart Money.

#### 4. Derivatives & Sentiment Agent
- **Nhiệm vụ**: Soi xét rủi ro đòn bẩy. Bóc tách Funding Rate dương/âm cực đoan, tương quan biến động giá với Open Interest (OI) để phát hiện bẫy quét thanh lý (Long/Short Squeeze traps).
- **Mục tiêu**: Cảnh báo ngay lập tức nếu thị trường đang ở trạng thái "quá nóng" chuẩn bị xảy ra hiện tượng thác lũ thanh lý (Liquidation Cascade).

#### 5. Socratic Devil's Advocate Agent (Trọng tâm cốt lõi)
- **Nhiệm vụ**: Đóng vai trò kẻ hoài nghi tàn nhẫn nhất (Radical Skepticism). Giả định rằng mọi tín hiệu mua đều là bẫy và tìm mọi bằng chứng để chứng minh luận điểm mua là sai lầm.
- **Quy tắc bắt buộc**:
  1. Phải đặt ra **chính xác 3 câu hỏi chất vấn hóc búa (3 Fatal Socratic Questions)** đánh thẳng vào các điểm mù của nhà đầu tư.
  2. Xây dựng **Kịch bản Tồi tệ nhất (Worst-Case Invalidation Scenario)**: Tại mức giá nào và điều kiện nào thì luận điểm hiện tại bị khai tử hoàn toàn?
  3. Đánh giá **Chỉ số FOMO Index**: Nhận diện xem người dùng có đang mua vì sợ bỏ lỡ cơ hội hay mua dựa trên lợi thế xác suất toán học.

---

## 5. BỘ DỮ LIỆU 10 GOLDEN CASES (BENCHMARK & KIỂM ĐỊNH TỰ ĐỘNG CI/CD)

Để đảm bảo hệ thống không bao giờ gặp ảo giác và luôn phản xạ chính xác trước các biến cố kinh điển, 10 bộ dữ liệu giả lập lịch sử được đóng gói thành Test Cases chạy trong CI/CD bằng **DeepEval**:

| ID | Tên Golden Case | Bối cảnh Lịch sử | Dữ liệu Đầu vào Đặc thù | Hành vi Phản biện Bắt buộc của Socratic Agent |
|---|---|---|---|---|
| **GC-01** | **LUNA / UST Death Spiral** | Tháng 05/2022 | Netflow nạp CEX tăng 1000%, Funding Rate âm kịch khung, OI tăng vọt khi giá sập liên tục. | Ngăn chặn tuyệt đối việc bắt đáy ("falling knife"); chất vấn cơ chế thanh khoản bảo chứng của thuật toán. |
| **GC-02** | **FTX / Alameda Insolvency** | Tháng 11/2022 | Dự trữ stablecoin trên sàn bốc hơi 80%, Outflow đột biến, FTT dump mạnh, FUD trên Twitter. | Báo động đỏ rút tiền toàn diện khỏi CEX; vô hiệu hóa toàn bộ chỉ báo kỹ thuật RSI/MACD. |
| **GC-03** | **COVID Black Thursday** | Tháng 03/2020 | DXY dựng cột đứng, US 10Y crash, toàn bộ thị trường thanh lý chéo (Margin Call Cascades). | Nhận diện hiện tượng cạn kiệt thanh khoản tiền mặt (Cash Crunch); chỉ ra rằng hỗ trợ kỹ thuật đều vô nghĩa. |
| **GC-04** | **FED Pivot Trap 2024** | Kỳ vọng FED cắt lãi | CPI vẫn neo dai dẳng > 3%, FED phát biểu diều hâu (Hawkish pause), nhưng giá pump theo tin đồn. | Chất vấn: *"Bạn đang mua dựa trên số liệu thực tế hay chỉ là kỳ vọng viển vông của đám đông?"* |
| **GC-05** | **Binance Massive Whale Dump** | Đỉnh sóng tăng | Giá tạo Higher High nhưng Volume giảm (Bearish Divergence), Netflow nạp BTC lên Binance tăng vọt $2B. | Vạch trần bẫy phân phối của cá voi; ngăn chặn lệnh mua theo đà (Breakout FOMO). |
| **GC-06** | **Funding Rate Squeeze Trap** | Đỉnh FOMO | Funding Rate chạm mức +0.1% / 8h (Annualized > 100%), OI đạt ATH, Retail Long áp đảo 85%. | Cảnh báo cú quét râu Long Squeeze quét sạch Stoploss; cấm vào lệnh Long đòn bẩy. |
| **GC-07** | **Low Float / High FDV Trap** | Token mới niêm yết | Circulating Supply < 10%, FDV gấp 20 lần Market Cap, lịch mở khóa token (Vesting cliff) trong 7 ngày tới. | Chỉ ra bẫy pha loãng lạm phát token của các quỹ đầu tư mạo hiểm (VCs) chuẩn bị xả vào đầu retail. |
| **GC-08** | **Wash Trading & Fake Volume** | Altcoin thanh khoản thấp | Volume 24h tăng 500% nhưng Orderbook mỏng dính, số lượng ví hoạt động thực tế (Active Addresses) đi ngang. | Bóc trần thủ thuật tạo thanh khoản ảo bằng bot; cảnh báo trượt giá nghiêm trọng (Slippage risk). |
| **GC-09** | **Range-Low Bear Trap** | Đáy vùng tích lũy | Giá gãy hỗ trợ quan trọng, FUD ngập tràn, nhưng Exchange Outflow tăng vọt về ví lạnh cá voi. | Nhận định bẫy săn thanh khoản bán (Stop-hunt); đề xuất chiến lược DCA Spot gom hàng từng phần. |
| **GC-10** | **DeFi Bridge Exploit Contagion** | Cầu nối đa chuỗi bị hack | TVL rút chạy hàng loạt, depeg token bọc (Wrapped assets), chênh lệch giá lớn giữa các DEX. | Khóa mọi hoạt động giao dịch liên quan đến hệ sinh thái bị ảnh hưởng; yêu cầu bảo toàn vốn. |

### Tiêu chí Đánh giá Tự động qua DeepEval (CI/CD Quality Gate):
- **Faithfulness Metric**: $\ge 0.95$ (Mọi lập luận phản biện phải bắt nguồn 100% từ facts trong JSON contract, không thêu dệt).
- **Hallucination Metric**: $\le 0.05$.
- **Socratic Rigor G-Eval**: $\ge 0.90$ (Đánh giá mức độ sắc bén, tính logic của 3 câu hỏi chất vấn và khả năng dập tắt tâm lý FOMO).

---

## 6. QUY CHUẨN MÃ NGUỒN & CẤU TRÚC DỰ ÁN (PROJECT REPO STRUCTURE)

```
CryptoIntel-Engine/
├── .github/
│   └── workflows/
│       └── deepeval_ci.yml         # CI/CD chạy 10 Golden Cases kiểm chuẩn
├── config/
│   ├── settings.py                 # Pydantic BaseSettings (FRED API key, endpoints)
│   └── constants.py
├── data/
│   ├── golden_cases/               # 10 file JSON mock dữ liệu chuẩn của các case lịch sử
│   │   ├── gc01_luna_crash.json
│   │   ├── gc02_ftx_insolvency.json
│   │   └── ...
│   └── schemas/                    # Pydantic v2 Contracts
│       ├── market_schema.py
│       ├── macro_schema.py
│       ├── whale_schema.py
│       └── signal_schema.py
├── engine/
│   ├── quant/                      # Pure Deterministic Python Layer (Zero Hallucination)
│   │   ├── market_indicators.py    # Volume Z-score, OI Delta, Funding Rate math
│   │   ├── macro_regime.py         # Quy tắc phân loại Risk-On/Off từ FRED
│   │   └── whale_detector.py       # Heuristic Netflow z-score & CEX depletion logic
│   ├── ingestion/                  # Connectors lấy dữ liệu Real-time (Free/No Key)
│   │   ├── binance_ws.py           # WebSocket Binance Real-time
│   │   ├── bybit_client.py         # Bybit Public REST
│   │   └── fred_client.py          # FRED API Client
│   └── agents/                     # LangGraph Multi-Agent Network
│       ├── graph.py                # StateGraph orchestration & conditional edges
│       ├── state.py                # TypedDict CryptoIntelState
│       ├── supervisor.py           # Điều phối & phân luồng
│       ├── macro_agent.py          # Chuyên gia vĩ mô
│       ├── whale_agent.py          # Chuyên gia dòng tiền cá voi
│       ├── derivatives_agent.py    # Chuyên gia phái sinh & bẫy thanh lý
│       └── socratic_agent.py       # Tác tử Phản biện Luật sư của quỷ
├── tests/
│   ├── test_quant_math.py          # Unit test kiểm toán toán học
│   └── test_golden_cases_eval.py   # DeepEval Faithfulness & Socratic test
├── ui/
│   └── streamlit_app.py            # Dashboard giao diện trực quan hóa thời gian thực
├── .env.example
├── pyproject.toml
└── CONTEXT_RULES.md                # Tài liệu này (Single Source of Truth)
```

---

## 7. LỘ TRÌNH TRIỂN KHAI 4 GIAI ĐOẠN (EXECUTION ROADMAP: PHASE 0 -> PHASE 3)

### Phase 0: Kiến trúc nền móng & Bộ quy chuẩn phát triển (Foundation & Standards)
- [x] **Quy tắc cốt lõi**: `.cursorrules`, `CLAUDE.md`, `ADR 001` (Tách biệt Quant thuần và LangGraph Socratic).
- [x] **Bộ đặc tả hoàn chỉnh (Specs)**:
  - `docs/specs/spec_00_use_cases.md`: Use Cases chi tiết cho Spot Accumulation & Swing Trading.
  - `docs/specs/spec_01_data_contracts.md`: Pydantic v2 Schemas chặt chẽ (Market, Macro, Whale, Signals, Socratic).
  - `docs/specs/spec_02_agent_prompts.md`: System Prompts chuẩn hóa với guardrails chống hallucination.
  - `docs/specs/spec_03_eval_and_golden_dataset.md`: Tiêu chuẩn DeepEval Faithfulness $\ge 0.95$ & 10 Golden Cases.
- [x] **Chuẩn kế toán & Thiết kế State/API**:
  - `docs/specs/accounting_mapping_tt200.md`: Ánh xạ Thông tư 200/2014/TT-BTC định giá Crypto, trích lập dự phòng TK 2291, phân tách Realized vs Unrealized PnL.
  - `docs/specs/api_and_state_design.md`: Thiết kế `CryptoIntelState`, REST endpoints & WebSocket streams.
- [x] **4 Agent Skills chuyên biệt**:
  - `skills/skill_quant_math/SKILL.md`: Toán học định lượng Z-score, Annualized Funding Rate, Delta OI.
  - `skills/skill_forensic_redflags/SKILL.md`: Heuristics bóc trần cạn kiệt dự trữ sàn, pha loãng Low Float/High FDV, Wash Trading.
  - `skills/skill_multi_agent_langgraph/SKILL.md`: Mẫu Fan-out / Fan-in song song trong LangGraph.
  - `skills/skill_llmops_evals/SKILL.md`: Harness kiểm thử tự động DeepEval & Langfuse tracing.
- [x] **Khung hạ tầng & CI/CD**:
  - `pyproject.toml`, `Dockerfile`, `docker-compose.yml`, `Makefile`, `.env.example`, `.github/workflows/ci.yml`.

### Phase 1: Real-time Ingestion + Deterministic Quant Engine + Pydantic v2
- [ ] Xây dựng connectors Real-time miễn phí:
  - WebSocket & REST client cho Binance/Bybit lấy Price, 24h Volume, OI, Funding Rate không cần API key.
  - REST client cho FRED lấy US Interest Rate, CPI, DXY.
- [ ] Hoàn thiện Quant Engine: Tính toán Z-score, phân loại trạng thái Macro Regime và Whale Netflows bằng toán thuần.
- [ ] Đóng gói 10 file JSON mock dữ liệu chuẩn của các case lịch sử (`data/golden_cases/`). Đảm bảo toàn bộ unit test deterministic vượt qua 100%.

### Phase 2: LangGraph Multi-Agent + System Prompts Socratic Phản biện
- [ ] Cài đặt `CryptoIntelState` và cấu trúc `StateGraph` trong `langgraph` theo thiết kế Phase 0.
- [ ] Triển khai các Node Agents: Supervisor, Macro Agent, Whale Agent, Derivatives Agent.
- [ ] Cài đặt Node **Socratic Devil's Advocate Agent**:
  - 3 câu hỏi chất vấn triệt hạ + Kịch bản Invalidation + Điểm cảnh báo FOMO.
- [ ] Tích hợp `DeepEval` vào test suite để tự động chấm điểm Faithfulness ($\ge 0.95$) trên 10 Golden Cases.

### Phase 3: LLMOps (Langfuse, Redis Cache) + Dashboard Streamlit Real-time
- [ ] Cấu hình `Langfuse` để giám sát latency, token usage, và trace hành trình suy luận của từng Agent.
- [ ] Triển khai `Redis Cache` để lưu trữ tạm thời các snapshot số liệu thị trường và kết quả phân tích, giảm chi phí gọi LLM trùng lặp.
- [ ] Xây dựng giao diện `Streamlit`:
  - Biểu đồ nến kết hợp Heatmap thanh lý và Netflow cá voi.
  - Bảng cảnh báo trạng thái Vĩ mô & Đòn bẩy.
  - Khung hội thoại Socratic tương tác: Cho phép người dùng nhập lệnh dự kiến mua, AI sẽ lập tức phản biện và đưa ra 3 câu hỏi chất vấn trước khi người dùng bấm nút giao dịch.
  - Bảng cân đối tài sản và trích lập dự phòng theo Thông tư 200/2014/TT-BTC.
