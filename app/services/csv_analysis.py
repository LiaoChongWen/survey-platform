import json
import pandas as pd
import numpy as np
from pathlib import Path


def detect_column_type(series: pd.Series) -> str:
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    try:
        pd.to_numeric(series.dropna())
        return "numeric"
    except (ValueError, TypeError):
        pass
    if series.nunique() <= max(20, len(series) * 0.05):
        return "categorical"
    return "text"


def read_csv_safe(file_path: str) -> pd.DataFrame:
    import os
    if not os.path.exists(file_path):
        raise ValueError(f"找不到檔案：{file_path}")
    for enc in ("utf-8", "utf-8-sig", "big5", "gbk", "cp950", "latin1"):
        try:
            return pd.read_csv(file_path, encoding=enc)
        except UnicodeDecodeError:
            continue
        except Exception as e:
            raise ValueError(f"CSV 讀取錯誤：{e}")
    raise ValueError("無法讀取 CSV 檔案，請另存為 UTF-8 格式再上傳")


def get_column_info(df: pd.DataFrame) -> list:
    info = []
    for col in df.columns:
        ctype = detect_column_type(df[col])
        info.append({
            "name": col,
            "type": ctype,
            "missing": int(df[col].isna().sum()),
            "unique": int(df[col].nunique()),
        })
    return info


def get_preview(df: pd.DataFrame, n: int = 50) -> dict:
    preview = df.head(n)
    rows = []
    for _, row in preview.iterrows():
        rows.append([None if (isinstance(v, float) and np.isnan(v)) else v for v in row])
    return {
        "columns": list(df.columns),
        "rows": rows,
        "total_rows": len(df),
        "total_cols": len(df.columns),
    }


def analyze(df: pd.DataFrame, chart_type: str, x_col: str, y_col: str = None) -> dict:
    if x_col not in df.columns:
        return {"error": f"欄位 {x_col} 不存在"}

    if chart_type == "pie":
        counts = df[x_col].value_counts()
        return {
            "type": "pie",
            "labels": counts.index.astype(str).tolist(),
            "data": counts.values.tolist(),
            "title": f"{x_col} 分布",
        }

    elif chart_type == "bar":
        if y_col and y_col in df.columns:
            grouped = df.groupby(x_col)[y_col].mean().round(2)
            return {
                "type": "bar",
                "labels": grouped.index.astype(str).tolist(),
                "data": grouped.values.tolist(),
                "title": f"{x_col} vs 平均 {y_col}",
                "y_label": f"平均 {y_col}",
            }
        else:
            counts = df[x_col].value_counts().sort_index()
            return {
                "type": "bar",
                "labels": counts.index.astype(str).tolist(),
                "data": counts.values.tolist(),
                "title": f"{x_col} 次數分布",
                "y_label": "次數",
            }

    elif chart_type == "scatter":
        if not y_col or y_col not in df.columns:
            return {"error": "散布圖需要 Y 軸欄位"}
        sub = df[[x_col, y_col]].copy()
        sub.columns = ["_x", "_y"]
        sub = sub.dropna()
        try:
            x_vals = pd.to_numeric(sub["_x"], errors="raise").tolist()
            y_vals = pd.to_numeric(sub["_y"], errors="raise").tolist()
        except (ValueError, TypeError):
            return {"error": "散布圖需要數值型欄位"}
        return {
            "type": "scatter",
            "data": [{"x": x, "y": y} for x, y in zip(x_vals, y_vals)],
            "title": f"{x_col} vs {y_col}",
            "x_label": x_col,
            "y_label": y_col,
        }

    elif chart_type == "mean":
        try:
            val = pd.to_numeric(df[x_col].dropna()).mean()
            return {"type": "stat", "label": "平均數", "value": round(float(val), 4), "column": x_col}
        except Exception:
            return {"error": "平均數需要數值型欄位"}

    elif chart_type == "variance":
        try:
            val = pd.to_numeric(df[x_col].dropna()).var()
            return {"type": "stat", "label": "變異數", "value": round(float(val), 4), "column": x_col}
        except Exception:
            return {"error": "變異數需要數值型欄位"}

    elif chart_type == "std":
        try:
            val = pd.to_numeric(df[x_col].dropna()).std()
            return {"type": "stat", "label": "標準差", "value": round(float(val), 4), "column": x_col}
        except Exception:
            return {"error": "標準差需要數值型欄位"}

    elif chart_type == "crosstab":
        if not y_col or y_col not in df.columns:
            return {"error": "交叉表需要 Y 軸欄位"}
        ct = pd.crosstab(df[x_col], df[y_col])
        return {
            "type": "crosstab",
            "index": ct.index.astype(str).tolist(),
            "columns": ct.columns.astype(str).tolist(),
            "data": ct.values.tolist(),
            "title": f"{x_col} × {y_col} 交叉表",
        }

    elif chart_type == "correlation":
        if not y_col or y_col not in df.columns:
            return {"error": "相關係數需要 Y 軸欄位"}
        if x_col == y_col:
            return {
                "type": "stat",
                "label": "皮爾森相關係數",
                "value": 1.0,
                "column": f"{x_col} & {y_col}",
            }
        try:
            common = df[[x_col, y_col]].dropna()
            x_num = pd.to_numeric(common[x_col])
            y_num = pd.to_numeric(common[y_col])
            corr = x_num.corr(y_num)
            return {
                "type": "stat",
                "label": "皮爾森相關係數",
                "value": round(float(corr), 4),
                "column": f"{x_col} & {y_col}",
            }
        except Exception:
            return {"error": "相關係數需要數值型欄位"}

    return {"error": f"不支援的圖表類型: {chart_type}"}
