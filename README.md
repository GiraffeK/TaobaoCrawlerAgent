# TaobaoCrawlerAgent 🛒🤖

> 一款基於 Playwright 與 AI Agent 架構的淘寶（Taobao）智慧商品爬蟲與分析助手。

---

## 🌟 核心特色

1. **智慧搜尋與數據擷取**：支援關鍵字搜尋、價格區間過濾與銷量排序。
2. **持久化登入狀態（Session Persistence）**：內建 `login` 模式，支援掃碼登入並持久化儲存 Cookie/StorageState，避免重複登入觸發風控。
3. **防爬蟲與瀏覽器偽裝**：自動移除 `navigator.webdriver` 標記、客製化 User-Agent 與視窗參數。
4. **結構化資料導出**：支援自動匯出為 JSON、CSV 等格式。
5. **模組化 Agent 架構**：方便後續擴充 LLM 模型（OpenAI、DeepSeek、Gemini）以進行商品比價、評論分析與智慧推薦。

---

## 📁 專案目錄結構

```
TaobaoCrawlerAgent/
├── .env.example              # 環境變數設定範本
├── .gitignore                # Git 忽略設定
├── pyproject.toml            # 專案建置與套件相依性定義
├── requirements.txt          # Python 相依清單
├── main.py                   # CLI 主要入口點
├── data/
│   ├── sessions/             # 瀏覽器 Session 與 Cookie 暫存區（不進入 Git）
│   └── outputs/              # 爬蟲與 Agent 輸出結果檔案
├── src/
│   └── taobao_crawler_agent/
│       ├── __init__.py
│       ├── config.py         # 設定檔管理（Pydantic Settings）
│       ├── models.py         # 核心資料模型（ProductItem, SearchQuery）
│       ├── agent/            # AI Agent 決策與推薦邏輯
│       │   └── core.py
│       ├── crawler/          # 爬蟲核心（瀏覽器控制、網頁解析）
│       │   ├── browser.py
│       │   ├── search.py
│       │   └── parser.py
│       ├── storage/          # 資料儲存與匯出
│       │   └── exporter.py
│       └── utils/            # 輔助模組（Loguru 結構化日誌）
│           └── logger.py
└── tests/                    # 單元測試
    └── test_basic.py
```

---

## 🚀 快速開始

### 1. 建立與啟動虛擬環境

```bash
# 建立虛擬環境 (Python 3.10+)
python -m venv .venv

# 啟動虛擬環境
# Windows PowerShell:
.\.venv\bin\Activate.ps1
# 或 Windows CMD:
.\.venv\bin\activate.bat
```

### 2. 安裝相依套件與 Playwright 瀏覽器

```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. 設定環境變數

複製設定檔範本：
```bash
cp .env.example .env
```
（可根據需要調整 `.env` 中的瀏覽器行為或 LLM API Key）

---

## 💡 使用方式

### 1. 登入淘寶（儲存 Cookie Session）

淘寶搜尋通常需要登入帳號以防反爬。首次使用請執行：

```bash
python main.py login
```

這將開啟視覺化瀏覽器視窗，請使用手機淘寶 App 掃碼登入。登入成功後，Session 將自動保存在 `data/sessions/`。

### 2. 執行商品搜尋與分析

```bash
# 預設無頭模式搜尋商品並輸出 CSV
python main.py search "人體工學椅"
python main.py search "rtx3080" --pages 10 --max-sku 100 --deep-sku --min-price 1800 --no-headless

# 顯示瀏覽器視窗以即時觀察過程
python main.py search "機械鍵盤" --no-headless
python main.py search "rtx3080" --pages 10 --max-sku 100 --deep-sku --min-price 1800 --no-headless

# 匯出為 JSON 格式
python main.py search "咖啡機" --format json
```

### 3. 查看版本資訊

```bash
python main.py version
```

---

## 🧪 執行測試

```bash
pytest
```

---

## ⚠️ 免責聲明與注意事項

本專案僅供學術研究與個人學習使用。請遵守淘寶官方的《使用者服務協議》與相關法律法規，請勿將本專案用於大規模高頻發爬取或商業盈利活動。

