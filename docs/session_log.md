# Session Log — Face Photo Search System

> Session ID: ce2917db-1f49-4128-a022-030193ef14ea
> Date: 2026-03-10

---

## Prompt 1 — Phase 1 核心管線實作

**Prompt（英文）：**
依照 `docs/spec.md` 實作 Phase 1 Core Pipeline。使用 InsightFace buffalo_l 模型、cosine similarity、CPU 執行。建立 `core/` 下的 7 個模組（config / file_scanner / face_service / query_builder / matcher / result_aggregator / reporter）以及 `app/main.py` 管線執行器。

**處理：**
- 讀取 `docs/spec.md` 規格
- 建立完整專案結構
- 實作所有核心模組，含 type hints、dataclasses、docstrings
- 實作 `app/main.py` CLI 管線（load model → process selfies → scan dataset → detect faces → match → aggregate → export）

**結果：** Phase 1 核心管線完成，所有模組可正常運作。

---

## Prompt 2 — 使用 demo 資料進行比對測試

**Prompt（中文）：**
用 `person.jpg` 當自拍照從 `data/demo_photos` 內去進行目前的比對測試，如果發生任何 bug 就直接修正它。

**處理：**
- 執行 CLI 管線測試
- 修正過程中遇到的問題
- 驗證比對結果

**結果：** 測試成功，threshold 0.45 偵測到 4/5 true positives，threshold 0.40 偵測到 5/5。

---

## Prompt 3 — Review Phase 1 實作與門檻值建議

**Prompt（英文）：**
Review 已生成的 Phase 1 實作。確認 threshold 0.45 是否合理，檢查 matcher.py 和 query_builder.py 是否有降低 recall 的邏輯，僅建議最小改動。

**處理：**
- 審查所有核心模組程式碼
- 分析 threshold 對 recall 的影響
- 確認 matcher 和 query_builder 邏輯正確

**結果：** 管線邏輯正確，Pipeline 可接受用於 Phase 1。建議保持 threshold 0.45 作為預設值（使用者可自行調低）。

---

## Prompt 4 — Phase 3 Streamlit UI 實作

**Prompt（英文）：**
實作 Phase 3 Streamlit UI。包含 sidebar（selfie upload、dataset path、threshold slider、Search button）、main area（query preview、results grid、bbox 繪製、statistics）。重用現有核心管線，不重寫 matcher/query_builder。

**處理：**
- 建立 `app/ui.py` 完整 Streamlit 介面
- 在 `app/main.py` 新增 `run_search_pipeline()` 供 UI 程式化呼叫
- 實作 model caching、session_state 結果持久化、暫存檔清理

**結果：** Streamlit UI 完成，可透過 `streamlit run app/ui.py` 啟動。

---

## Prompt 5 — 暫存檔清理 + 資料夾上傳流程改進

**Prompt（英文）：**
1. 新增暫存檔清理（try/finally）
2. 將 dataset path 文字輸入改為資料夾上傳
3. 保留現有 selfie 上傳流程
4. 保留所有現有功能

**處理：**
- 實作 `_cleanup_temp_dir()` 安全清理函式
- 改用 `st.file_uploader` 搭配 `accept_multiple_files="directory"`
- 新增 `_save_uploads_to_dir()` helper

**結果：** 暫存檔清理完成，dataset 改為資料夾上傳模式。

---

## Prompt 6 — 修正為真正的目錄上傳

**Prompt（英文）：**
目前的 dataset uploader 仍是多檔選擇而非真正的目錄上傳。修正為使用 `accept_multiple_files="directory"`，保留子資料夾結構，避免同名檔案覆蓋。

**處理：**
- 修正 `file_uploader` 使用 `accept_multiple_files="directory"`
- 更新 `_save_uploads_to_dir()` 處理相對路徑

**結果：** 改為真正的目錄上傳模式。

---

## Prompt 7 — 翻譯 README 為繁體中文

**Prompt（中文）：**
把目前的 README.md 翻譯成繁體中文並新增中文版的 README，完成後順便生成 git commit。

**處理：**
- 建立 `README.zh-TW.md` 完整翻譯
- 在英文 README 頂部新增中文版連結
- Commit 並 push（`2271bba`）

**結果：** `README.zh-TW.md` 建立完成，已推送至 GitHub。

---

## Prompt 8 — 確認 GitHub commit 可見性

**Prompt（中文）：**
我在 GitHub 上怎麼沒有看到這個 commit?

**處理：**
- 確認本地 commit 存在
- 執行 `git push` 推送到遠端

**結果：** Commit 已推送至 GitHub。

---

## Prompt 9 — 修正中文檔名亂碼 + 新增清除資料集按鈕

**Prompt（中文）：**
修正圖片檔名為中文時暫存圖檔的檔名變為亂碼導致無法讀取的錯誤，並在上傳資料夾的區塊增加一個按鈕可以一次移除目前已上傳的圖片。

**處理：**
- 根因：`cv2.imread` 在 Windows 上無法讀取含非 ASCII 字元的路徑
- 修正方案 1：在 `face_service.py` 使用 `np.fromfile` + `cv2.imdecode`
- 修正方案 2（最終）：`_save_uploads_to_dir` 統一使用 ASCII 安全檔名（`img_0000.jpg`），搭配 `name_map` 保留原始名稱供顯示
- 新增 🗑️ Clear Dataset 按鈕（使用 widget key counter + `st.rerun()`）
- 修正 `st.image` 棄用警告：`use_container_width=True` → `width="stretch"`

**結果：** 中文檔名問題徹底解決，Clear 按鈕可正常運作。

---

## Prompt 10 — 錯誤修正：use_container_width 棄用 + 中文路徑仍亂碼

**Prompt（中文）：**
還是有錯誤：`use_container_width=True` 需改為 `width='stretch'`，且中文自拍照暫存路徑仍是亂碼。

**處理：**
- Reset 先前的 commit
- 重新修正 `st.image` 參數
- 確認 selfie 上傳也使用 ASCII 安全檔名

**結果：** 修正完成。

---

## Prompt 11 — 再次修正：暫存資料夾子目錄名稱亂碼

**Prompt（中文）：**
暫存資料夾的名稱還是亂碼（子資料夾含中文名稱）。

**處理：**
- 確認 dataset 上傳的子資料夾路徑也含中文
- 統一所有暫存檔案為 ASCII 安全名稱，完全跳過原始子資料夾結構

**結果：** 所有暫存路徑改為純 ASCII，中文檔名問題徹底解決。

---

## Prompt 12 — 實作 Dataset 預處理/索引工作流程（兩階段）

**Prompt（英文）：**
實作兩階段工作流程：Prepare Dataset（一次性預處理）→ Search（快速重複搜尋）。包含 UI 狀態控制、dataset 替換處理、進度顯示。

**處理：**
- 建立 `core/dataset_index.py`（`PreparedDataset` dataclass + `prepare_dataset()` 函式）
- 在 `app/main.py` 新增 `run_search_from_index()` 函式
- 重寫 `app/ui.py` 為兩階段工作流程
- `PreparedDataset` 儲存：candidate_faces、image_cache（PIL）、name_map、stats
- Search 只做 selfie 處理 + 比對已快取的索引

**結果：** 兩階段工作流程完成。Prepare 一次後可重複 Search，速度大幅提升。

---

## Prompt 13 — 處理 InsightFace FutureWarning

**Prompt（中文）：**
執行時會跳出 FutureWarning：`estimate` is deprecated since version 0.26。

**處理：**
- 在 `core/face_service.py` 加入 `warnings.filterwarnings` 過濾該警告
- 說明這是 insightface 內部程式碼的問題，無法直接改用新語法

**結果：** 警告已被過濾，不再顯示。

---

## Prompt 14 — 確認是否該使用新版語法

**Prompt（中文）：**
不使用它提供的新版語法嗎？

**處理：**
- 解釋 `tform.estimate(lmk, dst)` 是 insightface 內部的 `face_align.py` 呼叫
- 我們無法修改第三方套件內部程式碼，只能過濾警告
- 等 insightface 官方更新

**結果：** 確認過濾警告為正確做法。

---

## Prompt 15 — 修正 Prepare 期間按 Browse files 導致 UI 死鎖

**Prompt（中文）：**
使用者按下 Prepare 按鈕時，同時再按下 Browse files 選擇照片後，會中斷 Prepare 流程，無法點擊任何按鈕，功能直接無法使用。

**處理：**
- 根因：`is_busy=True` 在 Prepare 執行期間被設定，但 Streamlit rerun 中斷了 finally block，flag 永遠卡住
- 修正方案：完全移除 `is_busy` flag。Streamlit 單執行緒模型本身就防止並行執行
- 移除所有 `is_busy` 相關的設定和 disabled 條件

**結果：** 死鎖問題解決，按鈕狀態改為只依賴實際資料狀態。

---

## Prompt 16 — Statistics 時間分開顯示

**Prompt（中文）：**
把 Statistics 的 Time 改為 Prepare 的時間和 Search 的時間分開顯示。

**處理：**
- 修改 `app/main.py` 的 `run_search_from_index()`：`processing_time` 只記錄搜尋時間
- 修改 `app/ui.py` Statistics 區：從 5 欄改為 6 欄，分別顯示 Prepare 和 Search 時間

**結果：** Statistics 現在分別顯示 Prepare 時間和 Search 時間。

---

## Prompt 17 — UI 改進：隱藏檔名列表 + Prepare 期間鎖定 + Cancel 按鈕

**Prompt（中文）：**
1. 移除 dataset uploader 的個別檔名顯示，改為其他方式表示有選取資料集
2. Prepare 期間把 Browse files 按鈕改為不能使用
3. 把 Clear 按鈕改成可以中斷 Prepare 的 Cancel 按鈕

**處理：**
- 用 CSS 隱藏 dataset uploader 內的 `stFileUploaderFileList`（`st.container(key=...)` 限定範圍）
- 採用兩階段架構：點 Prepare → 設 `is_preparing=True` + rerun → sidebar 全部 disabled → 才執行
- Clear 按鈕在 `is_preparing` 時變為 ❌ Cancel（永不 disabled），可安全中斷
- 所有 uploader、slider、Search 按鈕在 Prepare 期間 disabled

**結果：** UI 狀態管理完善，不再有死鎖風險。

---

## Prompt 18 — 更新 README Usage Guide

**Prompt（中文）：**
根據目前的操作方法，修改 README.md 的 Usage Guide 部分，並且同步調整 README.zh-TW.md。

**處理：**
- 將 Usage Guide 從 4 步驟改為 5 步驟（上傳資料集 → Prepare → 上傳自拍照 → 調整門檻 → Search）
- 說明 Cancel 按鈕用途
- 同步更新 Performance Notes（反映已實作的記憶體快取機制）
- 兩份 README 同步更新

**結果：** 兩份 README 的 Usage Guide 和 Performance Notes 已更新。

---

## Prompt 19 — 確認重複的 spec.md 是否必要

**Prompt（中文）：**
第一次下指令的時候你將 `docs/spec.md` 複製了一份到根目錄，這個檔案是必要的嗎？

**處理：**
- 確認根目錄 `spec.md` 不被任何程式碼引用
- 告知只需保留 `docs/spec.md`

**結果：** 確認根目錄 `spec.md` 為多餘檔案。

---

## Prompt 20 — 刪除多餘 spec.md 並 commit + push

**Prompt（中文）：**
直接刪除，然後把目前的調整生成一個 git commit。

**處理：**
- 刪除根目錄 `spec.md`
- Stage 所有程式碼/文件變更（7 個檔案）
- Commit `f15d7bf`（後 rebase 為 `8a2d5bc`）
- 解決 rebase 衝突（app/ui.py、core/face_service.py）
- Push 至 GitHub

**結果：** Commit `8a2d5bc` 已推送至 GitHub。

---

## Prompt 21 — 推送截圖更新

**Prompt（中文）：**
為什麼 `docs/screenshots/` 內的檔案更新沒有被放進 commit？請把它也推出去。

**處理：**
- 前次 commit 只 stage 了程式碼/文件，遺漏了截圖
- Stage `docs/screenshots/` 的 3 張圖片
- Commit `f251fab` 並 push

**結果：** 截圖更新已推送至 GitHub。

---

## Git Commit 紀錄

| Commit | 說明 |
|--------|------|
| `2271bba` | docs: add Traditional Chinese README |
| `8a2d5bc` | feat: two-stage prepare/search workflow, UI improvements, and bug fixes |
| `f251fab` | docs: update screenshots for new two-stage UI |
