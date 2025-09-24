import pdfplumber
import pandas as pd
import re
from typing import List, Tuple, Optional

class ICICIParseError(RuntimeError):
    """Raised when the ICICI statement cannot be parsed."""

_HEADER_KEYWORDS = {
    "date",
    "transaction date",
    "value date",
    "description",
    "particulars",
    "debit",
    "credit",
    "withdrawal",
    "deposit",
    "amount",
    "balance",
    "txn date",
    "dr",
    "cr",
    "type",
    "details",
}

_NUMERIC_COL_KEYWORDS = {"debit", "credit", "amount", "balance", "amt"}

def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def _build_table_from_words(words: List[dict], y_tolerance: float = 3.0) -> List[List[str]]:
    if not words:
        return []
    words = sorted(words, key=lambda w: (w["top"], w["x0"]))
    rows: List[List[Tuple[float, str]]] = []
    current_y: Optional[float] = None
    current_row: List[Tuple[float, str]] = []
    for w in words:
        y = w["top"]
        txt = _clean_text(w["text"])
        if not txt:
            continue
        if current_y is None or abs(y - current_y) <= y_tolerance:
            current_row.append((w["x0"], txt))
            current_y = y if current_y is None else (current_y + y) / 2
        else:
            rows.append(sorted(current_row, key=lambda t: t[0]))
            current_row = [(w["x0"], txt)]
            current_y = y
    if current_row:
        rows.append(sorted(current_row, key=lambda t: t[0]))
    table: List[List[str]] = []
    for row in rows:
        cells: List[str] = []
        buffer = ""
        last_x = None
        for x, txt in row:
            if last_x is not None and x - last_x > 15:
                cells.append(buffer.strip())
                buffer = txt
            else:
                buffer += (" " + txt) if buffer else txt
            last_x = x
        cells.append(buffer.strip())
        table.append(cells)
    return table

def _detect_header_row(table: List[List[str]]) -> Optional[int]:
    best_idx = None
    best_score = -1
    for idx, row in enumerate(table[:3]):
        score = sum(any(kw in cell.lower() for kw in _HEADER_KEYWORDS) for cell in row)
        if score > best_score:
            best_score = score
            best_idx = idx
    return best_idx if best_score > 0 else None

def _normalize_header(row: List[str]) -> List[str]:
    mapping = {
        "txn date": "Date",
        "transaction date": "Date",
        "value date": "Date",
        "date": "Date",
        "description": "Description",
        "particulars": "Description",
        "details": "Description",
        "debit": "Debit Amt",
        "dr": "Debit Amt",
        "credit": "Credit Amt",
        "cr": "Credit Amt",
        "withdrawal": "Debit Amt",
        "deposit": "Credit Amt",
        "amount": "Amount",
        "balance": "Balance",
        "type": "Type",
    }
    normalized = []
    for cell in row:
        cleaned = _clean_text(cell).title()
        key = cleaned.lower()
        normalized.append(mapping.get(key, cleaned))
    return normalized

def _merge_split_rows(rows: List[List[str]], header_len: int) -> List[List[str]]:
    merged: List[List[str]] = []
    prev: Optional[List[str]] = None
    for r in rows:
        if len(r) < header_len:
            if prev is not None:
                desc_idx = 1 if header_len > 1 else 0
                prev[desc_idx] = _clean_text(prev[desc_idx] + " " + " ".join(r))
            else:
                merged.append(r + [""] * (header_len - len(r)))
        else:
            if prev is not None:
                merged.append(prev)
            prev = r[:header_len] + (r[header_len:] if len(r) > header_len else [])
    if prev is not None:
        merged.append(prev)
    return merged

def _convert_numeric(value: str) -> Optional[float]:
    if not value:
        return None
    cleaned = re.sub(r"[^\d\.,-]", "", value)
    cleaned = cleaned.replace(",", "")
    try:
        return float(cleaned)
    except ValueError:
        return None

def _clean_and_structure(rows: List[List[str]], columns: List[str]) -> pd.DataFrame:
    filtered: List[List[str]] = []
    for r in rows:
        if not any(cell.strip() for cell in r):
            continue
        if any("total" in cell.lower() for cell in r):
            continue
        filtered.append(r)
    filtered = _merge_split_rows(filtered, len(columns))
    normalized_rows = [
        (row + [""] * (len(columns) - len(row)))[: len(columns)] for row in filtered
    ]
    df = pd.DataFrame(normalized_rows, columns=columns)
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

    # Keep Date as string to match CSV dtype
    # Convert numeric columns
    for col in df.columns:
        if any(kw in col.lower() for kw in _NUMERIC_COL_KEYWORDS):
            df[col] = df[col].apply(_convert_numeric).astype("float64")
    return df

def parse(pdf_path: str) -> pd.DataFrame:
    all_dfs: List[pd.DataFrame] = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                if not tables:
                    words = page.extract_words()
                    tables = [_build_table_from_words(words)]
                for tbl in tables:
                    if not tbl or not any(tbl):
                        continue
                    header_idx = _detect_header_row(tbl)
                    if header_idx is None:
                        continue
                    header_row = tbl[header_idx]
                    columns = _normalize_header(header_row)
                    data_rows = tbl[header_idx + 1 :]
                    if not data_rows:
                        continue
                    df_page = _clean_and_structure(data_rows, columns)
                    if not df_page.empty:
                        all_dfs.append(df_page)
        if not all_dfs:
            raise ICICIParseError("No transaction tables found in the PDF.")
        result = pd.concat(all_dfs, ignore_index=True)

        target_order = ["Date", "Description", "Debit Amt", "Credit Amt", "Balance"]
        for col in target_order:
            if col not in result.columns:
                result[col] = pd.NA
        result = result[target_order]

        return result
    except Exception as exc:
        raise ICICIParseError(f"Failed to parse ICICI statement: {exc}") from exc