# v0.1.1 — Streamlit UI & CLI merge

## 主要新增/修正

- 新增 Streamlit 控制面板 `app.py`：提供簡單 UI，可透過按鈕執行單場分析、執行測試，並檢視 / 匯出 `reports/last_analysis.json`、`reports/last_analysis.csv`。
- 合併並清理 CLI：將乾淨的 CLI 實作合併到 `analyze_one.py`（保留 `analyze_cli.py` 作相容選項），修復先前出現的重複/巢狀內容問題。
- 新增 Windows PowerShell helper：`run.ps1`（支援 `test`、`app`、`analyze` 三個 action），簡化常用命令在 Windows 上的執行。
- 儲存測試輸出：已執行 pytest，並將完整結果寫入 `reports/pytest_output.txt`（已 commit）。
- Streamlit 改善：`app.py` 會嘗試使用 `NBADataCollector` 自動取得隊伍清單填入下拉選單，並新增儲存/載入設定到 `reports/config.json` 的功能（由 UI 觸發）。

## 變更檔案（高階）

- 修改：`analyze_one.py`, `app.py`
- 新增：`run.ps1`, `reports/pytest_output.txt`（以及 UI 保存時會建立 `reports/config.json`）

## 使用說明（快速）

- 執行測試（PowerShell）：
  - `./run.ps1 -Action test`
  - 或：`.venv\Scripts\python.exe -m pytest -vv`
- 啟動 Streamlit UI（PowerShell）：
  - `./run.ps1 -Action app`
  - 或：`.venv\Scripts\python.exe -m streamlit run app.py`
- 單場比賽 CLI 範例（PowerShell）：
  - `./run.ps1 -Action analyze -Args '--home','New York Knicks','--away','Miami Heat'`

## 注意事項 / 相容性

- `NBADataCollector` 可能會呼叫外部 API；若 API 無法存取，app 會使用內建 fallback 的隊伍清單以確保 UI 可用。
- 本地測試已通過：`4 passed`（完整輸出見 `reports/pytest_output.txt`）。

## 版本說明（為何升級）

- 小功能釋出：新增 UI 與 helper script，並整理 CLI，屬於非破壞性功能新增。
