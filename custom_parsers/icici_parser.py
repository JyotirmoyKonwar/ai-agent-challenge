import pdfplumber
import pandas as pd
import re
from typing import List, Optional

_HEADER_KEYWORDS = {
    "date",
    "transaction",
    "description",
    "debit",
    "credit",
    "amount",
    "balance",
    "txn",
    "details",
    "particulars",
}

_FINAL_HEADER_MAP = {
    "date": "Date",
    "transaction": "Transaction",
    "description": "Description",
    "debit": "Debit Amt",
    "credit": "Credit Amt",
    "balance": "Balance",
    "amount": "Amount",
    "txn": "Txn",
    "details": "Details",
    "particulars": "Particulars",
}


def _clean_header(cell: str) -> str:
    if not isinstance(cell, str):
        return ""
    txt = cell.strip().lower()
    replacements = {
        "txn date": "date",
        "transaction date": "date",
        "date of transaction": "date",
        "debit amt": "debit",
        "debit amount": "debit",
        "credit amt": "credit",
        "credit amount": "credit",
        "cr": "credit",
        "cr.": "credit",
        "dr": "debit",
        "dr.": "debit",
        "bal": "balance",
        "closing bal": "balance",
        "opening bal": "balance",
        "particulars": "description",
        "details": "description",
    }
    txt = replacements.get(txt, txt)
    txt = re.sub(r"\s+", " ", txt)
    txt = txt.replace("_", " ")
    return txt


def _is_header(row: List[Optional[str]]) -> bool:
    if not row:
        return False
    matches = 0
    for cell in row:
        if not isinstance(cell, str):
            continue
        lowered = cell.strip().lower()
        if any(kw in lowered for kw in _HEADER_KEYWORDS):
            matches += 1
    return matches >= 2


def _detect_footer(row: List[Optional[str]]) -> bool:
    if not row:
        return False
    txt = " ".join(str(c).lower() for c in row if c)
    foot_keywords = ["total", "closing balance", "opening balance", "page", "statement"]
    return any(k in txt for k in foot_keywords)


def _clean_amount(val: str) -> float:
    if not isinstance(val, str):
        return float("nan")
    cleaned = re.sub(r"[^\d\.\-]", "", val)
    try:
        return float(cleaned)
    except ValueError:
        return float("nan")


def _numeric_clean(series: pd.Series) -> pd.Series:
    return series.apply(_clean_amount).astype(float)


def parse(pdf_path: str) -> pd.DataFrame:
    collected_rows: List[List[str]] = []
    final_cols: List[str] = []
    header_found = False

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                if not table:
                    continue

                start_idx = 0
                if not header_found:
                    for idx, possible_header in enumerate(table):
                        if _is_header(possible_header):
                            raw_header = possible_header
                            norm = [_clean_header(c) for c in raw_header]
                            final_cols = [
                                _FINAL_HEADER_MAP.get(n, raw_header[i].strip() or f"col_{i}")
                                for i, n in enumerate(norm)
                            ]
                            start_idx = idx + 1
                            header_found = True
                            break
                else:
                    for idx, possible_header in enumerate(table):
                        if _is_header(possible_header):
                            start_idx = idx + 1
                            break

                if not header_found:
                    continue

                for raw_row in table[start_idx:]:
                    if _detect_footer(raw_row):
                        break
                    if _is_header(raw_row):
                        continue

                    row = [c if c is not None else "" for c in raw_row]

                    if len(row) < len(final_cols):
                        row += [""] * (len(final_cols) - len(row))
                    elif len(row) > len(final_cols):
                        row = row[: len(final_cols)]

                    if sum(bool(str(v).strip()) for v in row) < max(1, len(final_cols) // 2):
                        continue

                    collected_rows.append(row)

    if not final_cols:
        raise ValueError("Header not found in PDF.")

    # Merge multiline description rows
    try:
        desc_idx = final_cols.index("Description")
    except ValueError:
        desc_idx = None

    merged_rows: List[List[str]] = []
    for row in collected_rows:
        if merged_rows and desc_idx is not None:
            prev = merged_rows[-1]
            if not str(row[0]).strip() and str(row[desc_idx]).strip():
                prev[desc_idx] = f"{prev[desc_idx]} {row[desc_idx]}".strip()
                for i, val in enumerate(row):
                    if i in (0, desc_idx):
                        continue
                    if str(val).strip():
                        prev[i] = f"{prev[i]} {val}".strip()
                continue
        merged_rows.append(row)

    cleaned_rows = [r for r in merged_rows if any(str(v).strip() for v in r)]

    df = pd.DataFrame(cleaned_rows, columns=final_cols)

    # Identify numeric columns (debit, credit, amount, balance)
    numeric_keywords = ("debit", "credit", "amount", "balance")
    for col in df.columns:
        if any(k in col.lower() for k in numeric_keywords):
            df[col] = _numeric_clean(df[col])

    # If generic Amount column exists without separate Debit/Credit, split it
    if "Amount" in df.columns and not any(c in df.columns for c in ("Debit Amt", "Credit Amt")):
        amt_series = df["Amount"]
        df["Debit Amt"] = amt_series.where(amt_series < 0, float("nan"))
        df["Credit Amt"] = amt_series.where(amt_series > 0, float("nan"))
        df.drop(columns=["Amount"], inplace=True)

    # Ensure Description is stripped
    if "Description" in df.columns:
        df["Description"] = df["Description"].astype(str).str.strip()

    # Remove rows with empty date field
    date_col = next((c for c in df.columns if "date" in c.lower()), None)
    if date_col:
        df = df[df[date_col].astype(str).str.strip().astype(bool)]

    df = df.reset_index(drop=True)
    return df


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python icici_parser.py <pdf_path>")
        sys.exit(1)

    result_df = parse(sys.argv[1])
    print(result_df.head())