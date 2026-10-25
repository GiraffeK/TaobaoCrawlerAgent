# TaobaoCrawlerAgent 開發歷程與決策日誌 (development-log.md)

> **說明**：本文件依據《AI Agent 行動準則》規範建立，完整記錄專案生命週期中每一次接收 Prompt、AI 理解、思考決策、實作過程與歸檔狀態。當本文件長度超過 500 行或 50KB 時，將依照輪替機制將歷史內容封存至 `docs/logs/development-log-YYYYMMDD-HHMMSS.md`。

---

## [2026-10-25 11:26] 階段一：專案基礎建設與初始架構建立

### 1. 使用者需求 (User Prompt)
> 「請先幫我建一個專案名稱：TaobaoCrawlerAgent」

### 2. AI 的理解與架構分析
- 使用者要求建立名為 `TaobaoCrawlerAgent` 的專案。
- 分析當前工作目錄為 `c:\Users\AdminSean\Coding\Personal\TaobaoCrawlerAgent`，已有本機 Python 3.14 環境。
- 專案定位為「淘寶智慧商品爬蟲與分析 Agent」，需具備：
  1. 瀏覽器自動化與持久化 Session (Playwright) 以因應淘寶反爬與登入機制。
  2. 結構化資料模型 (Pydantic)。
  3. CLI 操作界面 (Typer + Rich)。
  4. 多格式資料匯出 (CSV/JSON)。
  5. 結構化日誌 (Loguru)。
  6. Git 版本控制與忽略規則。

### 3. 思考與解決方案
- 建立標準現代 Python 專案目錄，分離 `src/` 核心代碼、`data/` 資料儲存、`tests/` 測試模組。
- 設定 `.gitignore` 排除虛擬環境、敏感憑證與 `data/sessions`（避免 Cookie 外洩）。
- 建立 CLI 入口 `main.py`，內建 `login`（掃碼登入保存 Session）與 `search`（商品爬取與比價分析）命令。

### 4. 具體產出檔案
- `pyproject.toml` & `requirements.txt`
- `.gitignore` & `.env.example`
- `main.py`
- `src/taobao_crawler_agent/`：
  - `config.py`、`models.py`
  - `crawler/` (`browser.py`, `search.py`, `parser.py`)
  - `agent/` (`core.py`)
  - `storage/` (`exporter.py`)
  - `utils/` (`logger.py`)
- `tests/test_basic.py`
- `README.md`
- Git 初始提交：`f33df2b feat: initialize TaobaoCrawlerAgent project structure`

---

## [2026-10-25 11:34] 階段二：建立 AI Agent 行動準則與履約系統架構

### 1. 使用者需求 (User Prompt)
> 當我請AI Agent寫程式時，也請附上此附件，做為AI Agent的行動準則，以下請AI Agent遵守：
> 1. 接受 user prompt 後必讀規範，任務結束時主動告知並證明遵守，末尾附標準履約查核標籤。
> 2. 全程記錄程式開發過程至 `development-log.md`，過長時輪替歸檔至 `docs/logs/`。
> 3. 建立 `Bulletin.json` 作為外部支援公告欄，疊加任務支援需求並完成狀態閉環。
> 4. 授權 workspace 內檔案管理不用再問，但嚴禁修改/刪除 `.git/`、模型權重目錄（如 `C:\models\`）及敏感憑證金鑰。
> 5. 終端機防彈原則（寫入 `.antigravityrules`）：
>    a. 禁止終端機進行檔案與字串搜尋（禁止 Select-String, Get-ChildItem, git grep），改用內建原生工具。
>    b. 任何單行測試、查詢或環境檢查一律覆寫至 `test_safe_command.py` 後執行 `python test_safe_command.py`，禁止在終端跑單行指令。
> 6. 開放對話修改此文件使之更完整。

### 2. AI 的理解與分析
- 使用者要求建立一套嚴謹的 Agent 行動準則 (Guardrails & Auditability)，旨在：
  - 確保開發透明度（全過程可溯源）。
  - 減少權限中斷干擾（規範化終端機指令以防止安全彈窗干擾流暢度）。
  - 建立跨工具/Agent/MCP 協作的標準溝通總線（`Bulletin.json`）。
  - 明確安全性邊界（保護 `.git/`、本機權重、金鑰）。
  - 自我審計證明（每輪對話標明規範遵循狀態）。

### 3. 思考與實作步驟
1. **建立 `Bulletin.json`**：設計具備 `version`、`description` 及 `bulletins` 列表的結構，支援 timestamp、請求類型、說明、狀態與閉環解法。
2. **建立 `development-log.md`**：正式建立本開發日誌，詳細記載當前與先前的 prompt 與思考過程，建立 `docs/logs/` 輪替路徑。
3. **建立 `test_safe_command.py`**：提供安全執行的樣板腳本，避免終端單行執行觸發不必要的中斷。
4. **檢查並同步 `.antigravityrules`**：確保系統級規則包含 5a (禁止終端機搜尋) 與 5b (單行查詢轉移至 test_safe_command.py)。
5. **落實履約證明查核標籤**：於每則回覆末尾生成包含 6 項準則遵循狀態的 Markdown 標籤塊。


---

## [2026-10-25 11:42] 階段三：解析 Gemini 外部對話紀錄與專案原始藍圖

### 1. 使用者需求 (User Prompt)
> `https://share.gemini.google/0640Y866ePHU`

### 2. AI 的理解與背景脈絡解析
- 使用者提供了一個 Google Gemini 的對話分享連結。
- 透過安全執行腳本 `test_safe_command.py` 結合本機 Edge 瀏覽器（`--headless=new --dump-dom --virtual-time-budget=12000`）成功擷取並解析該連結的完整 816 行對話文本（封存於 `docs/logs/extracted_conversation.txt`）。
- **對話全貌與專案起源**：
  1. **硬體評估階段**：使用者起初探討支援 900GB/s 頻寬與 256GB/384GB 以上的本地 AI 工作站架構（比較了 Mac Studio M5 Ultra 512GB、NVIDIA GB300、4x RTX PRO 6000、8x RTX 5090、以及 GLM-5.2 744B MoE 模型的推論速度與 Prefill 效能）。
  2. **淘寶搜尋痛點**：使用者隨後要求 Gemini「幫我進淘宝搜索rtx3080比較價格」，並要求「模仿人類動作慢慢進入操作」。
  3. **雲端限制與轉向本地**：Gemini 表明雲端環境無瀏覽器實體與滑鼠模擬能力，無法直接繞過淘寶 WAF 與滑塊驗證，進而為使用者規劃了一套**在本地 Antigravity 環境中透過 Playwright Stealth + 持久化 Session + Antigravity Skill 自建爬蟲 Agent** 的完整技術藍圖。
  4. **核心功能規格**：
     - 使用 `launch_persistent_context` 保持已登入之淘寶 Session/Cookie。
     - 設置黑名單關鍵字防坑（過濾「定金」、「維修」、「壞卡」、「散熱器」、「外殼」、「回收」等引流假價格）。
     - 設定價格區間過濾（1200 RMB ~ 4500 RMB）。
     - 封裝成 Antigravity Skill（包含 `SKILL.md` 與自動化呼叫指令 `/taobao-rtx-hunter`）。

### 3. 思考與架構對齊方案
- 我們的 `TaobaoCrawlerAgent` 專案正是此藍圖的具體落地實作！
- 我們目前的專案架構（`BrowserManager`、`ProductParser`、`DataExporter`、`TaobaoAgent`）與該藍圖完全吻合，且具備更高的模組化標準。
- 下一步可為使用者：
  1. 將 Gemini 對話中的淘寶比價與防坑過濾邏輯（引流價、黑名單關鍵字）整合進現有爬蟲解析器。
  2. 在專案中封裝 `.agents/skills/taobao-rtx-hunter/`，讓使用者能在 Antigravity 中透過 `/taobao-rtx-hunter` 直接呼叫。

---

## [2026-10-25 11:50] 階段四：依 Antigravity 規範配置 Playwright MCP Server

### 1. 使用者需求 (User Prompt)
> 「依照 Antigravity 規範，幫我在專案中配置好 Playwright MCP Server（使用 `npx -y @playwright/mcp@latest`）。」

### 2. AI 的理解與 Antigravity 規範分析
- 依據 Antigravity 自定義系統規範（`agy-customizations`），專案層級（Workspace-scoped）的 MCP 伺服器標準路徑為專案根目錄下的 `.agents/mcp_config.json`。
- 本機原先設定包含 `@modelcontextprotocol/server-playwright`，使用者指定替換為微軟官方最新發布之 `@playwright/mcp@latest`。
- 透過安全執行腳本 `test_safe_command.py` 驗證微軟官方 `@playwright/mcp@latest` 之 CLI 參數相容性，確認支援標準 stdio 傳輸協議與各項瀏覽器控制旗標。

### 3. 思考與實作步驟
1. 檢視與更新 `.agents/mcp_config.json`：
   - 伺服器識別名稱：`playwright`
   - 執行命令：`npx`
   - 參數陣列：`["-y", "@playwright/mcp@latest"]`
   - 超時設定：`timeoutSeconds: 600`（避免人工掃碼或頁面載入延遲導致逾時中斷）
2. 保持 `test_safe_command.py` 乾淨重置。
3. 遵循檔案邊界保護與無終端搜尋規則。

---

## [2026-10-25 11:55] 階段五：指引 Antigravity IDE 介面中的 MCP 與工具設定位置

### 1. 使用者需求 (User Prompt)
> 「哪裡有Additional Options」（附帶 IDE 截圖）

### 2. AI 的理解與截圖分析
- 使用者根據前一輪說明尋找管理 MCP 伺服器的介面位置。
- 檢視使用者截圖：
  - 使用者目前位於 Antigravity IDE (基於 VS Code)。
  - 右側 Chat 標頭的三個點選單顯示的是 Conversation 相關選項（Rename, Pin, Archive, Settings）。
  - 中間已開啟 **Antigravity Settings** 分頁：
    - 在 **General** 標籤下，清楚顯示了 **`Tool Permissions (9)`**（說明：*Modify permissions for file, terminal, and MCP tools.*），右側有 **`Open`** 按鈕。
    - 左側 **Projects** 清單中亦有當前專案 **`TaobaoCrawlerAgent`**。
- 說明目標：精準指引使用者透過中間已開啟的 Settings 分頁中的 `Tool Permissions [Open]`，或左側專案選項直接查看與管理 MCP 工具。

---

## [2026-10-25 11:59] 階段六：說明 MCP Tools 權限設定頁面機制與伺服器載入方式

### 1. 使用者需求 (User Prompt)
> 「哪來清單？」（附帶 MCP Tools 空白規則設定介面截圖）

### 2. AI 的理解與截圖分析
- 使用者點進了 `Settings > General > Tool Permissions > MCP Tools`，發現下方沒有預設的工具清單。
- **介面本質解析**：
  1. 此畫面為 **「權限存取控制規則表 (Permission Rules)」**，用於手動設定針對特定 Tool 或 Server 的 `Allow`（允許）、`Deny`（拒絕）或 `Ask`（每次詢問）。
  2. 因尚未手動新增過任何自定義放行/攔截規則，此處呈現空白是正常的。使用者若希望免授權直接使用，可在輸入框鍵入 `playwright` 並點擊 `Add`。
- **MCP 伺服器生效與檢視方式**：
  1. 專案的 `.agents/mcp_config.json` 是在當前交談（Conversation）進行中才建立的。
  2. Antigravity 需在**新開交談**（點擊聊天視窗右上角的 `+`）或重新載入視窗（`Ctrl+Shift+P` -> `Reload Window`）時，才會初始化背景的 MCP Server 進程。
  3. 伺服器啟動後，在聊天對話框輸入 `@` 即可看見由 MCP 注入的工具清單。
