**CLI Usage**

簡短說明：專案已提供一個乾淨且已測試的命令列介面 `analyze_cli.py`，建議把它當作 canonical CLI 使用；`analyze_one.py` 曾遭受多次程式化編輯，內容可能不穩定，因此不建議直接使用該檔案。

- **基本執行（PowerShell / Windows）**：

```
.venv\\Scripts\\python.exe analyze_cli.py \\
  --home "New York Knicks" \\
  --away "Miami Heat" \\
  --home-odds 1.53 \\
  --away-odds 4.50 \\
  --output-json reports/last_analysis.json \\
  --output-csv reports/last_analysis.csv
```

- **快速說明（參數）**:
  - `--home` / `--away`: 主隊與客隊名稱（字串）。
  - `--home-odds` / `--away-odds`: 市場的十進位賠率（decimal odds），例如 `1.53`、`4.50`。
  - `--output-json`: 若指定，會把詳細分析寫入該 JSON 檔案（例如 `reports/last_analysis.json`）。
  - `--output-csv`: 若指定，會把摘要寫入 CSV（例如 `reports/last_analysis.csv`）。
  - `--bet-side`, `--bankroll`, `--kelly-fraction`: 選擇計算 Kelly 建議下注相關參數（如要使用請參考程式說明）。

- **使用 `run.ps1`（簡化命令）**：

```
# 在 PowerShell 中
.\\run.ps1 -Action analyze -Args '--home','New York Knicks','--away','Miami Heat','--home-odds','1.53','--away-odds','4.50'
# 或啟動 Streamlit UI
.\\run.ps1 -Action app
```

- **Streamlit UI**：
  - 如果想要圖形介面，執行：
  ```powershell
  .venv\\Scripts\\python.exe -m streamlit run app.py
  ```
  - UI 會呼叫 `analyze_cli.py` 並把結果寫入 `reports/`。

- **關於 `analyze_one.py`**：
  - 專案中曾嘗試把 CLI 合併到 `analyze_one.py`，但該檔案在多次自動編輯後出現重複與縮排錯誤。若需要我可以替換為乾淨實作或改名為備份（`analyze_one.py.bak`）。

如果你要我把說明放進 `README.md`，或要我把 `analyze_one.py` 改名/覆寫，請回覆想要的選項（我可以馬上處理並提交變更）。
