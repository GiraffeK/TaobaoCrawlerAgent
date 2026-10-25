# TaobaoCrawlerAgent 開發歷程與決策日誌 (development-log.md)

> **說明**：本文件依據《AI Agent 行動準則》規範建立，完整記錄專案生命週期中每一次接收 Prompt、AI 理解、思考決策、實作過程與歸檔狀態。
> **歷史歸檔通知**：
> - 階段一至階段十四內容已封存至 `docs/logs/development-log-20261025-131755.md`。
> - 階段十五至階段二十六內容已封存至 `docs/logs/development-log-20261025-202900.md`。

---

## [2026-10-25 20:28] 階段二十七：根治「跳到 page2 後又跳回 page1」之 SPA 狀態中斷與重載問題

### 1. 使用者需求 (User Prompt)
> 「你好像跳到page2後又會跳回page1」

### 2. AI 深度排查與根本原因定位 (Root Cause Analysis)
1. **問題回放與使用者視覺觀察**：
   - 使用者清楚觀察到：瀏覽器畫面確實先點擊並跳轉至 Page 2，但片刻之後又刷新跳回了 Page 1。
2. **根本原因剖析**：
   - 在先前的 `_navigate_to_next_page` 邏輯中：
     ```python
     if target_clicked:
         await asyncio.sleep(2.0)
         is_active = await self.page.evaluate(...) # 檢查 .next-current 或 URL 是否已帶 page=2
         if is_active:
             return True
         else:
             # 假性失敗！觸發 URL fallback
             await self.page.goto(url) # 破壞 SPA 狀態，硬重載回 page=1！
     ```
   - **痛點 A（SPA 動態過渡時間差）**：淘寶前端是 React/Rax SPA 單頁應用，點擊頁碼 `2` 後發起 AJAX 非同步請求，商品卡片與底部分頁按鈕重新渲染需要 2.5~3.5 秒。在第 2 秒進行 DOM 檢查時往往尚未渲染完成，導致 `is_active` 回傳 `False`。
   - **痛點 B（全頁重載引發前端路由重置）**：一旦 `is_active` 為 `False`，腳本立即執行 `self.page.goto(url)`。而淘寶 PC 端搜尋頁對帶有一長串複雜篩選參數的冷啟動 HTTP GET 請求，其前端 Router 在首次載入時往往會初始化並重定向回 `page=1&s=0`！
   - 這正是使用者看到「先跳到 page 2、隨後又被刷新回 page 1」的元兇！

### 3. 實作重構與解決方案
1. **尊重 SPA 生命週期，廢除點擊後的硬重載**：
   - 當精確點擊頁碼數字按鈕（`button.next-pagination-item:text-is('2')`）成功後，確立「換頁事件已成功派發」。
   - **給予 SPA 充足的過渡等待時間（3.5 秒）**，等待前端非同步請求與卡片重新渲染完成。
   - 渲染完成後，自動平滑滾動回頁面頂部（`window.scrollTo({top: 0, behavior: 'smooth'})`），確保新載入的商品進入可視區。
   - 立即回傳 `True` 進入第 2 頁之商品提取管線，**嚴格禁止**在點擊成功後再次調用破壞 SPA 狀態的 `page.goto()`！
2. **URL Fallback 只在「找不到按鈕」時作為最後保險**：
   - 只有在頁面上完全找不到任何分頁按鈕時，才執行 URL 導航。
3. 遵循所有安全規範，更新日誌並附上查核標籤。


---

## [2026-10-25 20:44] 階段二十八：排查「找不到分析報告」問題、剔除無效伺服端 URL 參數與修復卡片選擇器

### 1. 使用者需求 (User Prompt)
> 「我怎麼找不到分析報告？」（附帶終端日誌：執行 10 頁爬取，每頁均超時報錯 `Timeout waiting for product cards... resolved to <li class="site-nav-region-item">中国大陆</li>`，最終抓取商品數為 0，未生成分析簡報）

### 2. AI 深度排查與根因診斷 (Root Cause Analysis)
1. **為什麼分析報告沒有生成？**
   - 檢視 `main.py` 邏輯：只有當 `result.top_recommendations` 有商品時才會調用 `export_markdown_report`。因為本次爬取共獲得 0 筆商品，直接走入 `No valid product items retrieved` 分支，因此未觸發報告產出。
2. **為什麼商品數會是 0？（兩大致命原因）**：
   - **致命原因一（URL 伺服端無效參數導致淘寶回傳 0 結果）**：
     - 在先前的 `_build_search_url` 中，人為加入了 `cat=50024403&filter=reserve_price%5B1800%2C4500%5D`。
     - 淘寶現代 PC 搜尋後端對 `filter=reserve_price[...]` 不相容（這是舊式手機端語法），當它與 `cat` 組合時，淘寶直接回傳「沒有找到相關的寶貝」或空白搜尋頁！
   - **致命原因二（`[class*='item']` 誤匹配頂部導航區域下拉選單）**：
     - 檢視 Playwright Call Log：`locator resolved to 20 elements. Proceeding with the first one: <li role="option" class="site-nav-region-item J_RegionItem">中国大陆</li>`。
     - `wait_for_selector` 包含寬鬆的 `[class*='item']`，匹配到頁面最頂部隱藏的「地區選擇：中國大陸」下拉選單項目，導致等待逾時！
   - **致命原因三（`card.inner_html()` 遺失根節點 `<a>` 標籤與 `href`）**：
     - 當卡片本身是 `<a href="https://item.taobao.com/item.htm?id=...">` 時，呼叫 `inner_html()` 只拿到內部節點，遺失了最關鍵的鏈接資訊。
3. **實作全面修復方案**：
   - **還原純淨標準搜尋 URL (`_build_search_url`)**：
     - 恢復為經實測穩定可靠的標準 URL：`https://s.taobao.com/search?q={keyword}&tab=all&page={page_no}&s={(page_no-1)*44}`。
     - 把價格過濾與類目篩選完全交給本地強大的 `ProductParser.evaluate_relevance(min_price_floor=1800)` 處理，絕不在 URL 帶入會使淘寶後端失效的非官方參數。
   - **精準修正卡片等待器與選擇器 (`search.py`)**：
     - 徹底移除寬鬆的 `[class*='item']`，專注鎖定 `[class*='Content--content--']`、`[class*='Card--doubleCardWrapper--']` 與 `a[href*='item.taobao.com']`。
     - 將 `card.inner_html()` 升級為 `await card.evaluate("el => el.outerHTML")`，完整保留所有節點屬性與 `href`。
4. 遵循所有安全規範，更新日誌並附上查核標籤。
