
# GPT Session Log

## 專案名稱
Face Photo Search System

## 文件用途
本文件整理本次與 GPT 協作的完整開發過程摘要，內容對應競賽要求的開發過程紀錄，特別強調：

- 問題分析與設計思路
- Prompt / AI 協作方式
- 技術選擇與架構說明
- 開發過程中的迭代紀錄
- 遇到的問題與解決方式
- 每一步的選擇、取捨與決策理由

---

# 1. 問題分析與設計思路

## 1.1 題目理解
競賽題目要求從大量相片中找出包含特定人員的照片。輸入是一張或多張自拍，輸出是從大量照片中找出可能包含該人物的相片。

一開始先明確拆解問題本質，不把它當成單純圖片分類，而是拆成以下幾個子問題：

1. 人臉偵測：在自拍與資料集照片中找出臉部位置
2. 特徵抽取：將人臉轉成 embedding 向量
3. 相似度搜尋：將自拍 embedding 與資料集中人臉 embedding 比對
4. 結果聚合：將臉層級命中結果整理成照片層級結果
5. 可視化與互動：讓使用者能上傳自拍、調整 threshold、看到結果與統計

### 選擇與取捨
- 沒有把題目當成整張圖片分類問題，因為背景、構圖與多人合照會造成高干擾。
- 選擇做人臉層級比對，是為了直接對應題目需求：找出「人」而不是找出「相似照片」。
- 一開始就排除身分驗證或安全監控等高風險定位，避免專案走向與競賽題目不同的方向。

## 1.2 MVP 定義
在討論初期曾考慮三種層級：

- A：最小可跑版
- B：可展示版
- C：強化版

最終選擇 **B 可展示版 + 支援多張自拍** 作為 MVP，並定義為：

- 支援 1 張或多張自拍
- 掃描一批照片資料
- 找出可能包含該人物的照片
- 顯示匹配人臉框、相似度分數與排序
- 後續可擴充為離線索引 / embedding cache

### 選擇與取捨
- 沒有選 A，因為雖然最容易做出結果，但展示力不足，不足以說服評審。
- 沒有直接做 C，因為一開始就做完整索引、複雜排序與多策略搜尋，會讓 scope 爆炸。
- 選擇 B，是在「可完成性」與「可展示性」之間取得平衡。
- 將「多張自拍」納入 MVP，是因為題目沒有要求只能單張，而且多張自拍明顯有助於提高穩定度。

## 1.3 多自拍策略
多自拍查詢沒有直接採用 embedding average，而是選擇：

- 逐張搜尋
- 結果聯集
- 同一照片取最高分聚合

### 選擇與取捨
- 沒有直接做 embedding average，因為早期希望保留查詢結果的可解釋性，且低品質自拍可能拉偏平均向量。
- 採聯集 + 最高分，是因為這個策略邏輯簡單、容易實作，也方便對評審說明。
- 這是一個偏 recall 的策略，後續再透過 threshold 與 UI 做 precision 調整。

---

# 2. 技術選擇與架構說明

## 2.1 為什麼選 Python
在一開始先討論語言，而不是直接進入實作。結論是：

- Python 在 AI / CV 生態最成熟
- InsightFace / OpenCV / NumPy / Streamlit 整合順
- AI 生成 Python 程式碼穩定度高
- 很適合快速做出競賽 MVP 與 Demo

### 選擇與取捨
- 沒有選 C#：雖然結構穩定，但 AI / CV 套件整合成本較高。
- 沒有選 TypeScript 當核心：前端漂亮，但核心 AI 工作仍大概率要回 Python。
- 沒有選 Rust / C++：雖然效能高，但開發與維護成本遠高於競賽 MVP 需求。
- 選 Python，是以「開發速度、AI 協作穩定度、套件成熟度」優先，而不是理論上的最佳效能。

## 2.2 模型與技術選型
經過討論，最終選擇：

- 語言：Python 3.12
- 人臉模型：InsightFace `buffalo_l`
- UI：Streamlit
- 相似度：Cosine similarity
- 影像處理：OpenCV / Pillow
- 後續優化：embedding cache / index，必要時再考慮 FAISS

### 選擇與取捨
- 沒有選 OpenCV Haar / dlib / face_recognition：考量到精度、穩定性、可擴充性，最後認為不如 InsightFace。
- 沒有先選 DeepFace：封裝高但控制力較弱，不利於後續優化。
- 選 `buffalo_l`：早期階段先以辨識品質為主，而不是急著換小模型求速度。
- 沒有先選 `buffalo_s`：避免在未確認真正瓶頸前，就先犧牲辨識準確度。
- 沒有一開始就用 FAISS：因為資料量與瓶頸當時都不足以支撐它作為第一優先優化方向。
- UI 選 Streamlit，是以快速完成可展示介面為優先，而不是追求最完整的前端工程化。

## 2.3 架構設計
專案架構拆成：

- `app/ui.py`：Streamlit UI
- `app/main.py`：主流程 / pipeline orchestration
- `core/config.py`
- `core/file_scanner.py`
- `core/face_service.py`
- `core/query_builder.py`
- `core/matcher.py`
- `core/result_aggregator.py`
- `core/reporter.py`

後續再加入：

- `core/dataset_index.py`
- `PreparedDataset`
- `prepare_dataset()`
- `run_search_from_index()`

### 選擇與取捨
- 沒有把所有邏輯塞在單一檔案，因為這會讓後續 debug 與迭代變得困難。
- 也沒有切得過細，以免產生過多模組與接口，反而增加 AI 生成時的混亂。
- 最終採「中等粒度模組化」，兼顧清晰結構與 AI 可實作性。

## 2.4 文件架構
在寫程式之前，先建立完整文件：

- `docs/spec.md`
- `docs/vibe_log.md`
- `docs/architecture_overview.md`
- `README.md`

### 選擇與取捨
- 沒有讓 AI 一開始就直接寫完整專案，因為沒有固定規格時，AI 很容易自行腦補需求。
- 先做 spec 再做 code，是以文件換穩定性、以前期成本換後期少返工。
- 將 spec 放在 `docs/`，而不是 root 與 docs 各一份，是為了維持單一來源、避免版本混亂。

---

# 3. Prompt / AI 協作方式

## 3.1 協作策略
整體不是一次叫 AI 寫完整專案，而是採用分階段 Vibe Coding：

1. 先定義需求與規格
2. 再讓 AI 依 spec 產生 Phase 1 核心程式
3. 先人工與實測驗證
4. 再讓 AI review
5. 再進行 UI 建置
6. 最後做效能優化與文件整理

### 選擇與取捨
- 沒有一次請 AI 寫完整系統，因為那樣最容易得到不可控、難維護的程式。
- 改用小步迭代，每一步都驗證，雖然步驟較多，但更穩定、更容易定位問題。

## 3.2 規格先行
在真正寫程式前，先用 GPT 逐步定義：

- 專案目標
- 輸入 / 輸出
- 使用流程
- 成功標準
- 非目標
- 技術架構
- 模組設計
- 開發里程碑
- 風險與限制
- Demo 設計

之後再將這些整理成 `spec.md`，作為給 Claude Opus 的實作依據。

### 選擇與取捨
- 這使得第一版程式出現得比較慢，但明顯提高了 AI 後續生成品質。
- 這是一種「前期慢、後期穩」的取捨。

## 3.3 AI 實作節奏
與 AI 協作時，主要採取以下節奏：

- Prompt 1：生成核心 pipeline
- 實際跑測試資料
- Prompt 2：review 現有實作
- Prompt 3：加入 Streamlit UI
- 後續 prompt：UI polish、dataset folder upload、兩階段索引流程

### 選擇與取捨
- 沒有把 review 與 implementation 混在一起，因為 AI 若同時 review 與重構，很容易動到已經可用的部分。
- 先測試再 review，是因為真實執行結果比理論判斷更能定位問題。

## 3.4 協作原則
協作時特別要求：

- 不要重寫整個專案
- 不要改壞已經可用的 core pipeline
- UI 要重用既有 pipeline
- 每次只做 focused improvement
- 如果要記錄開發過程，優先用 append-ready 摘要，而不是整份重寫

### 選擇與取捨
- 對 AI 加上範圍限制，是用自由度換穩定性。
- 不讓 AI 自動維護整份 vibe_log，是因為實作與摘要之間常有落差，保留人工最後把關更可靠。

---

# 4. 開發過程中的迭代紀錄

## Iteration 1 — 題目分析與 MVP 定義
先從競賽題目出發，定義專案本質，並選定 B 可展示版 + 多自拍支援作為 MVP。

### 取捨
- 可展示性優先於極致完整性
- 先做能說服評審的版本，而不是最重工程化的版本

## Iteration 2 — 規格文件建置
逐步補完 `spec.md` 內容，包括：

- Input / Output
- Workflow
- Success Criteria
- Out of Scope
- Technology Stack
- Module Design
- Milestones
- Risks
- Demo Plan

### 取捨
- 先投入時間在文件，而不是立刻寫 code
- 用規格完整度換 AI 實作穩定度

## Iteration 3 — 根據 AI review 補強 spec
將 spec 交給 Claude Opus review 後，補上：

- API / dataclass 介面
- default threshold
- InsightFace 初始化細節
- requirements 版本範圍
- UI layout appendix

### 取捨
- 接受對生成品質有直接幫助的 review 建議
- 不全盤推翻原 spec，而是用 appendix 方式補強

## Iteration 4 — Phase 1 核心 pipeline 實作
由 AI 依 spec 生成：

- `face_service.py`
- `file_scanner.py`
- `query_builder.py`
- `matcher.py`
- `result_aggregator.py`
- `reporter.py`
- `main.py`

CLI 可運行並產生 `results.json`。

### 取捨
- 先做 CLI / pipeline，不先做 UI
- 先證明「能找得到」，再追求「找得好看」

## Iteration 5 — Phase 1 驗證與 review
以真實小資料測試：

- 1 張自拍
- 8 張合照
- Ground truth positive = 5 張

結果：

- threshold 0.45：抓到 4 / 5
- threshold 0.40：抓到 5 / 5

之後再用 Prompt 2 讓 AI review，結論是：

- `matcher.py` 邏輯正確
- `query_builder.py` 沒有降低 recall 的問題
- default threshold 0.45 可保留
- 問題主要屬於 threshold 邊界，而不是 pipeline 錯誤

### 取捨
- 沒有立即重寫 pipeline，因為它已經可用
- 保留 0.45 當預設，是為了維持較保守的 precision；0.40 作為使用者可調整的 UI 選項

## Iteration 6 — Streamlit UI 建置
接著用 AI 製作 Streamlit UI，要求：

- 不重寫 core pipeline
- 重用 `app/main.py`
- 上傳自拍
- 指定 dataset
- threshold slider
- 結果 grid
- bbox
- statistics
- error handling

UI 成功完成且可用。

### 取捨
- 不在 `ui.py` 內自行複製一套搜尋流程
- 以共用 pipeline 換取一致性與可維護性

## Iteration 7 — UI polish：資料夾上傳 / cleanup
後續再針對 UI 做 focused improvement：

- dataset input 改成 directory upload
- `accept_multiple_files="directory"`
- temp cleanup
- `session_state` 保存結果圖
- Clear Dataset 重設 uploader
- 改善錯誤訊息與 UX

### 取捨
- 不保留手動路徑輸入，因為對 demo 體驗不友善
- 改用資料夾上傳，雖然增加了檔案上傳流程，但整體操作更直覺
- 增加 cleanup 與 state 管理，換來更乾淨、更穩定的 UI 執行行為

## Iteration 8 — 效能問題出現
實際測試發現：

- 348 張圖片搜尋時間約 1607 秒

因此重新分析瓶頸，判斷真正耗時的是：

- 讀圖
- face detection
- embedding extraction

而不是單純 cosine similarity。

因此決定 **不優先換 `buffalo_s`，也不把 FAISS 當第一優先**，而是先做：

- dataset preprocessing
- embedding cache / index

### 取捨
- 不先換小模型，避免在未證實 bottleneck 前就犧牲辨識品質
- 不先上 FAISS，因為目前最慢的是前處理，不是向量搜尋本身
- 選擇 index / cache，是以架構改動換取真正對症的效能改善

## Iteration 9 — 兩階段流程：Prepare Dataset + Search
接著再讓 AI 實作兩階段 UX / 架構：

1. Prepare Dataset
2. Search

新增：

- `PreparedDataset`
- `prepare_dataset()`
- `run_search_from_index()`
- dataset state 管理
- `is_preparing`
- `dataset_ready`
- search disabled until prepared
- clear dataset invalidates index
- 搜尋時與預處理時鎖定按鈕

這讓 dataset embeddings 不必每次 search 都重算。

### 取捨
- 不做成上傳後自動預處理，而是改成明確兩階段流程
- 這樣做會多一個按鈕與步驟，但能大幅降低狀態混亂與重複建 index 的風險
- 在 prepare/search 過程中鎖住按鈕，是以操作自由度換取執行正確性

## Iteration 10 — 文件整理與 GitHub 發佈準備
最後整理：

- `README.md`
- `docs/spec.md`
- `docs/vibe_log.md`
- `docs/architecture_overview.md`
- screenshots
- `.gitignore`
- `LICENSE`

並確認：

- venv clean test 可跑
- Streamlit UI 可跑
- requirements 可安裝
- GitHub repo 結構乾淨

### 取捨
- README 放精簡入口資訊
- 詳細設計與紀錄放 docs
- 用分層文件結構平衡「快速理解」與「完整過程保存」

---

# 5. 遇到的問題與解決方式

## 5.1 Spec 不夠精確
### 問題
最早 spec 只有模組名稱，沒有 API / dataclass / default threshold，交給 AI 容易亂補。

### 解法
補上：

- API interface appendix
- default threshold = 0.45
- requirements
- model init
- UI layout

### 取捨
- 增加 spec 複雜度
- 換取 AI 生成時更穩定的介面與較少重工

## 5.2 pipeline 驗證時漏掉一張正解
### 問題
在 8 張合照中，5 張是正解，threshold 0.45 只抓到 4 張。

### 解法
改測 0.40 後可以抓到第 5 張。  
之後用 AI review 確認不是邏輯錯誤，而是 threshold 邊界問題，因此保留 0.45 作為預設值，並在 UI 中讓使用者可調整。

### 取捨
- 預設值保留在 0.45，偏保守
- 不硬改成 0.40，而是讓使用者根據資料集自行調整

## 5.3 UI dataset 上傳體驗不佳
### 問題
一開始 dataset 是手動輸入資料夾路徑，對 demo 不友善。

### 解法
改成 Streamlit directory upload，讓使用者用瀏覽器選資料夾。

### 取捨
- 失去本機資料夾路徑直讀的簡單性
- 換來更直覺、更適合 demo 的瀏覽器交互方式

## 5.4 暫存檔問題
### 問題
上傳檔案會先寫到 temp directory，如果不清理會累積垃圾檔案。

### 解法
加入 `try/finally` cleanup，並先將結果圖 cache 進 session_state。

### 取捨
- 增加 state 管理複雜度
- 換取更乾淨的執行環境與穩定的重複 demo 體驗

## 5.5 dataset 搜尋速度太慢
### 問題
348 張圖搜尋約 1607 秒，重複查詢不實際。

### 解法
重新分析瓶頸後，先做 dataset preprocessing / indexing，而不是直接換模型或先加 FAISS。

### 取捨
- 放棄「換小模型」這種直覺但可能錯誤的解法
- 採用需要更多架構調整，但更貼合 bottleneck 的索引方案

## 5.6 使用者更換 dataset 時狀態會混亂
### 問題
若 dataset 改變，但沿用舊搜尋結果 / 舊 index，會產生錯誤或誤導。

### 解法
加入：

- Clear Dataset
- invalidate prepared dataset
- 清除舊 search_result
- Search 需在 dataset prepared 後才啟用

### 取捨
- 增加 UI 狀態機複雜度
- 換取使用者操作一致性與結果可信度

---

# 6. 最終設計決策總結

## 核心決策
- 語言：Python 3.12
- 人臉模型：InsightFace `buffalo_l`
- UI：Streamlit
- 相似度：Cosine similarity
- 多自拍策略：逐張搜尋 + 聯集 + 同照片取最高分
- threshold 預設：0.45
- 首要效能優化方向：dataset preprocessing / embedding cache
- 文件結構：README + docs/ 規格與開發紀錄

## 為什麼沒有先換 `buffalo_s`
因為要先保留辨識品質，並且瓶頸主要不在 similarity search，而在 dataset 每次都重做 face detection / embedding。

## 為什麼沒有先加 FAISS
因為目前第一瓶頸不是向量搜尋，而是資料集前處理。  
當資料集 embeddings 已經能被重複使用後，若還要支援更大規模或更多次查詢，再考慮 FAISS 才合理。

## 為什麼文件與 repo 要這樣分層
- README：快速理解與執行
- docs/spec.md：完整規格
- docs/vibe_log.md：AI 開發過程
- docs/architecture_overview.md：圖解架構

這樣可以同時滿足：
- 評審快速閱讀
- 競賽要求的流程紀錄
- 開源專案的清楚結構

---

# 7. 最終產出

## 程式
- Core pipeline
- Streamlit UI
- Prepare Dataset / Search 兩階段索引版流程

## 文件
- `README.md`
- `docs/spec.md`
- `docs/vibe_log.md`
- `docs/architecture_overview.md`
- screenshots

## 可展示成果
- 使用者上傳自拍
- 上傳 dataset folder
- Prepare Dataset
- Search
- 顯示 bbox、score、statistics
- 輸出 `results.json`

---

# 8. 結語

這次開發不是單純「讓 AI 寫程式」，而是透過逐步定義問題、建立規格、驗證輸出、再做 focused improvement 的方式，完成一個可展示、可測試、可上 GitHub 的人臉搜尋系統。

整個過程中，AI 主要扮演：

- 規格整理者
- 程式生成者
- reviewer
- 文件協作工具

而最終的關鍵決策，例如 MVP 範圍、threshold、資料夾上傳 UX、dataset preprocessing / indexing 優先順序，則由人工根據測試結果與工程判斷做出決策。

也就是說，本專案真正重視的不是「AI 幫忙寫了多少程式」，而是「如何透過 AI 協作逐步做出正確的選擇與取捨」。
