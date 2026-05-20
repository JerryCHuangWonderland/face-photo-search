
# GPT Prompt Log

## 文件用途
本文件整理本次與 GPT 協作過程中的所有主要 prompt / reply 紀錄。  
格式採逐輪摘要，保留每次使用者輸入重點、GPT 回覆重點，以及該輪產生的主要選擇與取捨。

---

## Turn 1
### User Prompt
提供競賽題目：從大量相片中找出包含特定人員的相片，希望先理解題目與可行做法。

### GPT Reply Summary
分析題目本質是人臉偵測、embedding 抽取、相似度搜尋與結果聚合。提出 A/B/C 三種方案，建議以 Python + InsightFace + Streamlit 做競賽 MVP，並說明 Demo 與過程記錄方式。

### Key Choices / Trade-offs
- 不把題目當成一般圖片分類
- 先選可展示的系統路線，而不是研究型模型訓練

---

## Turn 2
### User Prompt
希望一步一步釐清，先產生詳細 md 再交給 AI 實作；先問為什麼選 Python。

### GPT Reply Summary
說明應先定義 MVP 與需求，而不是直接決定語言；分析 Python 在 AI / CV 生態、原型開發速度、AI 協作能力上的優勢；建議先做 requirement / project definition。

### Key Choices / Trade-offs
- 先定義問題，再選技術
- Python 勝出是因為綜合開發效率，而非理論性能最強

---

## Turn 3
### User Prompt
要求一步一步確認。

### GPT Reply Summary
規劃整體步驟：MVP、輸入輸出、流程、成功標準、非目標、技術方案、模組拆分、最後整理成 md。

### Key Choices / Trade-offs
- 用流程控制 scope
- 不一開始就邊做邊改

---

## Turn 4
### User Prompt
選擇 B 可展示版，並支援多張自拍；認為可以做結果聯集。

### GPT Reply Summary
確認 MVP 為 B + 多自拍；建議採「逐張搜尋 + 結果聯集 + 同照片取最高分」的整合規則。

### Key Choices / Trade-offs
- 不選 A，因為展示不足
- 不直接做 embedding average，先選聯集 + 最高分

---

## Turn 5
### User Prompt
進入 Step 2：輸入 / 輸出定義。

### GPT Reply Summary
定義自拍輸入、dataset folder、支援格式、遞迴掃描子資料夾、JSON 輸出、統計資訊、資料規模 100~3000 張。

### Key Choices / Trade-offs
- 選資料夾輸入，避免一開始走資料庫路線
- 保留 JSON 輸出，利於 debug 與驗證

---

## Turn 6
### User Prompt
進入 Step 3。

### GPT Reply Summary
定義使用者操作流程與系統處理流程；建議 MVP 先採即時掃描搜尋，但保留未來可擴充為索引模式；確認要有 threshold 調整與統計資訊。

### Key Choices / Trade-offs
- MVP 先做即時掃描
- 先不做索引化，但保留未來升級路線

---

## Turn 7
### User Prompt
進入 Step 4。

### GPT Reply Summary
定義功能成功標準、結果品質成功標準、展示成功標準與效能目標；建議加入測試資料集概念。

### Key Choices / Trade-offs
- 不寫過死的 benchmark
- 用競賽 demo 可驗證標準替代學術指標

---

## Turn 8
### User Prompt
進入 Step 5。

### GPT Reply Summary
定義 Out of Scope：不自行訓練模型、不做影片 / 即時攝影機、不做帳號權限、不做大型分散式搜尋、不做身分驗證、不做完整影像管理。

### Key Choices / Trade-offs
- 主動砍 scope
- 保證專案可完成、可展示

---

## Turn 9
### User Prompt
進入 Step 6。

### GPT Reply Summary
比較 OpenCV / dlib / DeepFace / InsightFace，最終建議採用 InsightFace；比較相似度搜尋方式，MVP 先不用 FAISS；建議 UI 用 Streamlit。

### Key Choices / Trade-offs
- InsightFace 勝在品質、可控性與成熟度
- FAISS 不作為第一優先，因為早期資料量與瓶頸不匹配

---

## Turn 10
### User Prompt
確定用 buffalo_l 和 Streamlit。

### GPT Reply Summary
確認核心技術棧：Python、InsightFace buffalo_l、Streamlit、cosine similarity，並進入 Step 7 模組設計。

### Key Choices / Trade-offs
- 先保留高辨識品質
- 不先拿小模型換速度

---

## Turn 11
### User Prompt
同意進入 Step 7。

### GPT Reply Summary
設計模組：config、file_scanner、face_service、query_builder、matcher、result_aggregator、reporter、ui、main；給出資料結構與專案目錄。

### Key Choices / Trade-offs
- 中等粒度模組化
- 平衡清晰度與 AI 實作可行性

---

## Turn 12
### User Prompt
同意進入 Step 8。

### GPT Reply Summary
規劃開發里程碑：Phase 1 core pipeline、Phase 2 aggregation/reporter、Phase 3 Streamlit UI、Phase 4 demo polish，並標出 P0/P1/P2 優先級。

### Key Choices / Trade-offs
- 先讓核心能跑
- UI 與 polish 後置

---

## Turn 13
### User Prompt
同意進入 Step 9。

### GPT Reply Summary
整理風險與限制：小臉、角度、遮擋、相似人物誤判、threshold 選擇困難、CPU 效能、大量資料限制、資料隱私。

### Key Choices / Trade-offs
- 主動承認限制
- 以誠實與工程判斷換可信度

---

## Turn 14
### User Prompt
同意進入 Step 10。

### GPT Reply Summary
設計 Demo 資料集、操作流程、講解劇本、技術亮點與評審可能問題。

### Key Choices / Trade-offs
- 把 demo 視為設計的一部分
- 不是做完 code 才補想展示方式

---

## Turn 15
### User Prompt
要求直接產出可下載的 spec.md。

### GPT Reply Summary
整理前面所有決策成完整 `spec.md` 檔案，供後續 AI 實作使用。

### Key Choices / Trade-offs
- 先凍結規格
- 用 spec 當作 AI implementation contract

---

## Turn 16
### User Prompt
貼出 Claude Opus 對 spec 的 review，詢問是否要補完。

### GPT Reply Summary
分析 review，判斷哪些是必補：API interfaces、threshold default、onnxruntime、InsightFace init；建議用 appendix 方式補強 spec。

### Key Choices / Trade-offs
- 不照單全收
- 只採納真正影響實作品質的部分

---

## Turn 17
### User Prompt
同意補強 spec，但不要標 V2。

### GPT Reply Summary
重新生成補強版 `spec.md`，加入 appendix 與 requirements 等內容。

### Key Choices / Trade-offs
- 避免 V2 命名造成版本誤解
- 以單一正式 spec 為主

---

## Turn 18
### User Prompt
詢問 `vibe_log.md` 如何自動記錄。

### GPT Reply Summary
解釋不能真正自動記錄，建議用結構化模板與 iteration 方式留存，並提出 `docs/vibe_log.md` 的設計概念。

### Key Choices / Trade-offs
- 不追求全自動
- 改用模板降低紀錄成本並保留準確性

---

## Turn 19
### User Prompt
同意產生 `vibe_log.md` 模板。

### GPT Reply Summary
生成 `vibe_log.md` 模板，包含 project info、iteration template、issues、future improvements、demo checklist。

### Key Choices / Trade-offs
- 先用模板建立紀錄框架
- 後續再逐步填實際內容

---

## Turn 20
### User Prompt
詢問原本 spec 是否應移到 `docs/spec.md` 並加入 `vibe_log.md`。

### GPT Reply Summary
建議將 spec 放到 `docs/`，不要同時保留 root 與 docs 兩份，以維持 repo 乾淨與文件一致性。

### Key Choices / Trade-offs
- 採 docs 單一來源
- 避免重複文件造成維護風險

---

## Turn 21
### User Prompt
同意，要求 README。

### GPT Reply Summary
產生 README 內容，包含專案介紹、架構、技術選型、執行方法與 docs 文件位置。

### Key Choices / Trade-offs
- README 做入口
- 詳細內容放 docs

---

## Turn 22
### User Prompt
要求直接產 README 檔下載。

### GPT Reply Summary
生成 `README.md` 下載檔。

### Key Choices / Trade-offs
- 直接給檔案
- 避免聊天室 Markdown 排版問題

---

## Turn 23
### User Prompt
同意取得第一個 Vibe Coding prompt。

### GPT Reply Summary
提供 Prompt 1，要求 AI 依 `docs/spec.md` 實作 Phase 1 core pipeline。

### Key Choices / Trade-offs
- 只做 core pipeline
- 不讓第一輪同時碰 UI 與 demo 細節

---

## Turn 24
### User Prompt
詢問 Prompt 1 執行完是否直接下 Prompt 2。

### GPT Reply Summary
建議先人工檢查與最小測試，再下 Prompt 2 review；指出應檢查 InsightFace 初始化、cosine similarity、embedding shape 等。

### Key Choices / Trade-offs
- 先人工驗證，再交 AI review
- 避免過度相信 AI 的靜態檢查

---

## Turn 25
### User Prompt
執行 `python -m app.main` 但缺少 `--selfies` 和 `--dataset`，詢問是否要先準備測試資料。

### GPT Reply Summary
確認這代表 CLI pipeline 正常，只是需要測試資料與參數；建議建立 `data/demo_selfies` 與 `data/demo_photos` 做最小測試。

### Key Choices / Trade-offs
- 不先改 code
- 先補足最小測試場景

---

## Turn 26
### User Prompt
測試完成：8 張合照中 5 張是答案，抓到 4 張。

### GPT Reply Summary
判定 Prompt 1 成果約 80 分；建議先試不同 threshold，再對 `matcher.py` / `query_builder.py` 做 focused review，而不是重寫。

### Key Choices / Trade-offs
- 不急著推翻重做
- 先判斷問題來源是邏輯還是參數

---

## Turn 27
### User Prompt
補充 0.4 threshold 就會出現第 5 張。

### GPT Reply Summary
判斷核心 pipeline 大致正確，問題主要是 threshold 邊界；建議先記錄到 vibe_log，再進 UI。

### Key Choices / Trade-offs
- 保留 0.45 預設值
- 讓 UI slider 解決不同資料集差異

---

## Turn 28
### User Prompt
依 Prompt 2 回應判斷可繼續下一步。

### GPT Reply Summary
確認 Prompt 2 review 認為 pipeline acceptable，可直接進 Phase 3：Streamlit UI；提供 Prompt 3。

### Key Choices / Trade-offs
- 不在 core 微調上耗太久
- 轉向 UI，提高展示完成度

---

## Turn 29
### User Prompt
要求可直接貼入 `vibe_log.md` 的紀錄文字。

### GPT Reply Summary
撰寫 Phase 1 Validation and Review 的正式 Markdown 版本。

### Key Choices / Trade-offs
- 把驗證結果正式文件化
- 讓後續決策有可追溯依據

---

## Turn 30
### User Prompt
同意取得 UI Prompt。

### GPT Reply Summary
提供 Prompt 3：要求 AI 以最小侵入方式在既有 core pipeline 之上建 Streamlit UI。

### Key Choices / Trade-offs
- 限制改動範圍
- 用穩定性換取功能擴充

---

## Turn 31
### User Prompt
上傳 `ui.py` 讓我 review。

### GPT Reply Summary
評估 UI 生成品質約 90 分，肯定 model cache、bbox、progress、session_state 等實作；建議進入 dataset / demo polish。

### Key Choices / Trade-offs
- 不大改已可用 UI
- 把精力放在使用者體驗與 demo polish

---

## Turn 32
### User Prompt
要求加入 cleanup、資料夾選取，並詢問 `vibe_log.md` 是否可讓 Opus 自動維護。

### GPT Reply Summary
解釋 Streamlit 的 folder upload 與本機資料夾路徑的差異；建議不要完全自動維護 vibe_log，而是要求 append-ready 摘要；提供 focused prompt。

### Key Choices / Trade-offs
- 不追求直接讀本機路徑
- 以瀏覽器資料夾上傳換 UI 體驗
- 不把文件維護完全交給模型

---

## Turn 33
### User Prompt
要求移除自動更新 vibe_log 的要求。

### GPT Reply Summary
提供移除 vibe_log 要求後的精簡版 UI polish prompt。

### Key Choices / Trade-offs
- 精簡 prompt
- 讓 AI 專注主任務

---

## Turn 34
### User Prompt
回報 AI 做成多選檔案，不是資料夾。

### GPT Reply Summary
指出目前仍是 `accept_multiple_files=True`，不是 `"directory"`；提供修正 prompt，要求真 directory upload 並保留資料夾結構。

### Key Choices / Trade-offs
- 不接受近似解
- 持續用更精準 prompt 修正行為

---

## Turn 35
### User Prompt
回報已改成真正的 directory upload。

### GPT Reply Summary
確認這版已達成選資料夾體驗，且 cleanup、image cache、state 管理都合理；建議更新 vibe_log。

### Key Choices / Trade-offs
- 在需求滿足時停止重構
- 轉向文件同步更新

---

## Turn 36
### User Prompt
要求直接產當前 `vibe_log.md` 下載檔。

### GPT Reply Summary
整理當前迭代內容，生成更新版 `vibe_log.md`。

### Key Choices / Trade-offs
- 持續同步文件
- 不等最後才一次補紀錄

---

## Turn 37
### User Prompt
要求再加上 embedding cache / search optimization design。

### GPT Reply Summary
新增 Iteration 7 到 `vibe_log.md`，描述 indexing / cache / FAISS 的設計方向。

### Key Choices / Trade-offs
- 先留下設計思考
- 為後續效能優化鋪路

---

## Turn 38
### User Prompt
要求圖解版 Markdown 下載。

### GPT Reply Summary
生成 `architecture_overview.md`，以 Mermaid 圖說明整體架構、pipeline、UI 與未來效能優化方向。

### Key Choices / Trade-offs
- 用圖補強文字說明
- 提升評審閱讀效率

---

## Turn 39
### User Prompt
詢問 architecture_overview / spec 是否整合進 README，並要求補上執行步驟與使用說明。

### GPT Reply Summary
建議 README 放精簡版，docs 保留完整版本；重新整合生成更完整的 README，加入 installation、usage、architecture 與 docs 入口。

### Key Choices / Trade-offs
- README 精簡
- docs 詳細
- 分層文件避免資訊爆量

---

## Turn 40
### User Prompt
要求加上 screenshot 說明。

### GPT Reply Summary
說明該截三張圖、放在 `docs/screenshots/`，並生成含 screenshot 區塊的 README。

### Key Choices / Trade-offs
- 只放關鍵三圖
- 不讓 README 被大量圖片淹沒

---

## Turn 41
### User Prompt
要求 README 再加入 venv、`py -3.12` 等實際使用方式，並移除 Codex 字樣。

### GPT Reply Summary
重新生成 README，加入 Python 3.12、venv、Windows 啟動方式，並移除 Codex。

### Key Choices / Trade-offs
- 文件以真實使用流程為準
- 不保留未使用工具名稱

---

## Turn 42
### User Prompt
要求不要再有很多最終版，直接把覺得該做的都做完。

### GPT Reply Summary
整合所有應做內容，生成單一完整版 README，包含 demo、architecture、installation、usage、repo structure、performance notes。

### Key Choices / Trade-offs
- 停止多版本文件循環
- 以單一可交付檔案收斂

---

## Turn 43
### User Prompt
同意進一步做 GitHub 發佈準備。

### GPT Reply Summary
生成 `.gitignore`、`LICENSE`、`repo_settings.txt` 的打包檔案，並建議 GitHub description / topics。

### Key Choices / Trade-offs
- 提前完成 repo hygiene
- 降低上 GitHub 前的最後整理成本

---

## Turn 44
### User Prompt
詢問是否該將專案放上 GitHub。

### GPT Reply Summary
確認目前已具備完整專案條件，建議立刻上 GitHub，並提供 init / commit / push / topics / description 建議。

### Key Choices / Trade-offs
- 不再延後發佈
- 在可執行、可展示、文件齊備時即上線

---

## Turn 45
### User Prompt
實測 repo 可跑，問 root 與 docs 各有一份 `spec.md` 是否都要保留。

### GPT Reply Summary
建議只保留 `docs/spec.md`，刪除 root `spec.md`，維持 repo 文件單一來源。

### Key Choices / Trade-offs
- 單一來源優先於方便存取
- 避免文件同步風險

---

## Turn 46
### User Prompt
提出效能問題：348 張圖搜尋花 1607 秒，詢問應該選 `buffalo_s` 還是 FAISS。

### GPT Reply Summary
分析後指出瓶頸主要在 dataset 每次都重做 face detection / embedding，不是 similarity search；建議先做 dataset preprocessing / cache，而非先換 `buffalo_s` 或先上 FAISS。

### Key Choices / Trade-offs
- 不先犧牲辨識品質
- 不先上與瓶頸不匹配的工具
- 先做真正有用的架構優化

---

## Turn 47
### User Prompt
要求考量使用者更換資料夾、預處理時機、預處理與搜尋時要不要鎖住按鈕，並附目前 `ui.py`。

### GPT Reply Summary
建議改成兩階段 UX：Prepare Dataset + Search；引入狀態機、dataset invalidation、disabled buttons 與 reusable prepared dataset index；並提供 focused prompt。

### Key Choices / Trade-offs
- 不自動預處理
- 明確拆成兩階段，提升操作可控性與狀態正確性

---

## Turn 48
### User Prompt
回報兩階段索引版 UI 已實測沒問題，問是否要新增 vibe_log。

### GPT Reply Summary
建議一定要新增，因為這是架構級優化；撰寫 Iteration 8 的內容，描述 dataset preprocessing 與 indexed search implementation。

### Key Choices / Trade-offs
- 將架構優化納入正式開發紀錄
- 不把它視為小修而略過

---

## Turn 49
### User Prompt
詢問 Iteration 8 在 vibe_log 中的位置，是否放在最底部 / Demo Preparation Checklist 下。

### GPT Reply Summary
說明 Iteration 屬於 Development Timeline，應該放在 Iteration 7 之後、Issues and Lessons Learned 之前，而不是文件最底部。

### Key Choices / Trade-offs
- 保持文件結構邏輯
- 不為了省事破壞文件一致性

---

## Turn 50
### User Prompt
要求在 Iteration 8 補上 performance comparison。

### GPT Reply Summary
撰寫可直接貼入 Iteration 8 的 Performance Comparison 段落，說明從每次全資料集重算到一次 Prepare、多次 Search 的複雜度轉換與效能意義。

### Key Choices / Trade-offs
- 不只記錄做了什麼
- 也記錄為什麼這樣做更有工程價值

---

## Turn 51
### User Prompt
根據競賽繳交要求，要求整理成 `gpt_session_log.md` 與 `gpt_prompt_log.md`。

### GPT Reply Summary
將整段開發過程整理成：
- `gpt_session_log.md`：符合競賽開發過程紀錄要求
- `gpt_prompt_log.md`：按時間順序整理本次所有主要 user prompt 與 GPT reply 摘要

### Key Choices / Trade-offs
- 將「流程導向文件」與「對話導向文件」分開
- 同時滿足競賽提交與開發追溯需求
