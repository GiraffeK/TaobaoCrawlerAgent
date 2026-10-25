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
