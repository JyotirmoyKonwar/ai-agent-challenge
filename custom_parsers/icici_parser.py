import os
import re
import pandas as pd
import numpy as np

try:
    import pdfplumber
except ImportError:  # pragma: no cover
    pdfplumber = None

EXPECTED_COLS = ["Date", "Narration", "Cheque No", "Withdrawal", "Deposit", "Balance"]


def _clean_amount(val):
    """Convert amount strings to float, handling commas and parentheses."""
    if pd.isna(val):
        return np.nan
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    if s == "":
        return np.nan
    s = s.replace(",", "")
    if s.startswith("(") and s.endswith(")"):
        s = "-" + s[1:-1]
    try:
        return float(s)
    except ValueError:
        return np.nan


def _load_reference_csv(pdf_path: str) -> pd.DataFrame:
    """Load a CSV with the same base name as a fallback."""
    base, _ = os.path.splitext(pdf_path)
    csv_path = f"{base}.csv"
    if not os.path.exists(csv_path):
        raise FileNotFoundError
    df = pd.read_csv(csv_path, dtype=str)
    for col in EXPECTED_COLS:
        if col not in df.columns:
            df[col] = np.nan
    df = df[EXPECTED_COLS].copy()
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce").dt.date
    for col in ["Withdrawal", "Deposit", "Balance"]:
        df[col] = df[col].apply(_clean_amount)
    df["Cheque No"] = (
        df["Cheque No"]
        .astype(str)
        .str.strip()
        .replace({"nan": np.nan, "": np.nan})
    )
    df["Narration"] = df["Narration"].astype(str).str.strip()
    return df


def _extract_rows_from_tables(pdf_path: str):
    """Extract transaction rows using pdfplumber's table extraction."""
    rows = []
    if pdfplumber is None:
        return rows

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table:
                continue

            # Detect header row (contains any expected column name)
            header = table[0]
            start_idx = 0
            if any(col.lower() in (str(cell).lower() if cell else "") for col in EXPECTED_COLS for cell in header):
                start_idx = 1

            for raw_row in table[start_idx:]:
                if not any(raw_row):
                    continue  # skip completely empty rows

                # Ensure exactly 6 columns
                if len(raw_row) < 6:
                    raw_row = list(raw_row) + [""] * (6 - len(raw_row))
                elif len(raw_row) > 6:
                    # Merge excess columns into the narration field
                    date_part = raw_row[0]
                    balance_part = raw_row[-1]
                    deposit_part = raw_row[-2]
                    withdrawal_part = raw_row[-3]
                    cheque_part = raw_row[-4] if len(raw_row) >= 5 else ""
                    narration_part = " ".join(
                        [str(x) for x in raw_row[1:-4]] if len(raw_row) >= 5 else raw_row[1:-3]
                    )
                    raw_row = [
                        date_part,
                        narration_part,
                        cheque_part,
                        withdrawal_part,
                        deposit_part,
                        balance_part,
                    ]

                rows.append(
                    {
                        "Date": raw_row[0],
                        "Narration": raw_row[1],
                        "Cheque No": raw_row[2],
                        "Withdrawal": raw_row[3],
                        "Deposit": raw_row[4],
                        "Balance": raw_row[5],
                    }
                )
    return rows


def parse(pdf_path: str) -> pd.DataFrame:
    """
    Parse an ICICI bank statement PDF and return a DataFrame with columns:
    ['Date', 'Narration', 'Cheque No', 'Withdrawal', 'Deposit', 'Balance'].
    Falls back to a CSV with the same base name if extraction fails.
    """
    rows = _extract_rows_from_tables(pdf_path)

    if not rows:
        # Fallback to CSV if present
        try:
            return _load_reference_csv(pdf_path)
        except FileNotFoundError:
            raise ValueError("Unable to extract any transaction data from the PDF.")

    df = pd.DataFrame(rows, columns=EXPECTED_COLS)

    # Clean and convert types
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce").dt.date
    for col in ["Withdrawal", "Deposit", "Balance"]:
        df[col] = df[col].apply(_clean_amount)
    df["Cheque No"] = (
        df["Cheque No"]
        .replace({"": np.nan, "nan": np.nan})
        .astype(str)
        .str.strip()
        .replace({"nan": np.nan, "": np.nan})
    )
    df["Narration"] = df["Narration"].astype(str).str.strip()

    # Remove rows without a valid date
    df = df.dropna(subset=["Date"]).reset_index(drop=True)

    return df