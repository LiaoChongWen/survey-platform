# 問卷填答與即時統計分析平台

一套基於 **FastAPI** 的問卷管理與即時統計分析 Web 平台，支援管理員後台建立問卷、學生端填答、以及即時圖表分析，一鍵啟動，開箱即用。

---

## 功能特色

- **問卷管理**：新增、編輯、刪除問卷與題目，支援多種題型
- **學生填答**：QR Code 掃描即可進入填答頁面，行動裝置友善
- **即時統計**：填答後自動更新統計圖表，支援長條圖、圓餅圖等視覺化呈現
- **文字雲分析**：針對開放式問題自動產生中文文字雲（使用 jieba 斷詞）
- **資料匯出**：支援匯出 Excel（`.xlsx`）格式
- **管理員認證**：JWT Token 登入保護，Cookie-based session 管理
- **自動 SSL**：自動生成自簽憑證，支援 HTTPS 模式
- **一鍵啟動**：`run.py` 自動安裝依賴、初始化資料庫、啟動伺服器

---

## 技術棧

| 類別 | 技術 |
|------|------|
| 後端框架 | FastAPI + Uvicorn |
| 資料庫 | SQLAlchemy（SQLite） |
| 模板引擎 | Jinja2 |
| 認證機制 | python-jose（JWT） + passlib（bcrypt） |
| 資料分析 | pandas、numpy、matplotlib |
| 中文斷詞 | jieba |
| 文字雲 | wordcloud + Pillow |
| QR Code | qrcode |
| SSL 憑證 | cryptography |
| Excel 匯出 | openpyxl |

---

## 快速開始

### 環境需求

- Python **3.8** 以上
- （選用）`openssl` 指令（用於備援 SSL 憑證生成）

### 安裝與啟動

```bash
# 複製專案
git clone https://github.com/liaochongwen/東山範例.git
cd 東山範例

# 一鍵啟動（自動安裝依賴 + 初始化資料庫 + 啟動伺服器）
python run.py
```

> **注意**：預設 Port 為 `8501`，若需使用 Port 443（HTTPS）則需要 root 權限：
> ```bash
> sudo python run.py --port 443
> ```

### 啟動參數

| 參數 | 預設值 | 說明 |
|------|--------|------|
| `--port` | `8501` | 監聽 Port |
| `--host` | `0.0.0.0` | 監聽 Host |
| `--skip-install` | — | 跳過套件安裝步驟 |

範例：
```bash
python run.py --port 8080 --host 127.0.0.1
```

---

## 目錄結構

```
東山範例/
├── run.py              # 一鍵啟動腳本
├── requirements.txt    # Python 依賴套件清單
├── app/
│   ├── main.py         # FastAPI 應用程式入口
│   ├── models.py       # 資料庫 ORM 模型
│   ├── schemas.py      # Pydantic 資料驗證 Schema
│   ├── database.py     # 資料庫連線與初始化
│   ├── auth.py         # JWT 認證邏輯
│   ├── config.py       # 系統設定（管理員帳號、金鑰）
│   ├── routers/
│   │   ├── admin.py    # 管理員後台路由
│   │   ├── forms.py    # 問卷 CRUD API
│   │   ├── responses.py# 填答路由
│   │   ├── analytics.py# 統計分析 API
│   │   └── student.py  # 學生填答頁面路由
│   ├── services/       # 商業邏輯層
│   ├── templates/      # Jinja2 HTML 模板
│   └── static/         # 靜態資源（CSS、JS、圖片）
├── cert/               # SSL 憑證（自動生成）
└── data/               # 資料庫與設定檔（自動生成）
    └── config.json     # 管理員密碼等設定
```

---

## 預設管理員帳號

首次啟動時會**自動生成**管理員帳號，並顯示於終端機：

```
┌─────────────────────────────────┐
│  管理者帳號：admin               │
│  管理者密碼：（隨機生成）          │
└─────────────────────────────────┘
```

密碼儲存於 `data/config.json`，可手動修改。

登入網址：`http://localhost:8501/admin/login`

---

## 手動安裝依賴

若不使用 `run.py` 自動安裝，可手動執行：

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8501
```

---

## 授權

本專案僅供教學與範例使用。
