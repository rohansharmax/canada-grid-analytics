import pandas as pd
from pathlib import Path

DATA_DIR = Path("data")
CLEAN_CSV_PATH = DATA_DIR / "clean_generation.csv"

# Threshold: small net-negatives are legit (idle plants consume > produce).
# Anything below this is a real anomaly worth flagging.
NEGATIVE_THRESHOLD_MWH = -150_000  # -150 GWh


class QualityError(Exception):
    """Raised when data fails a hard quality gate."""


def load_clean():
    return pd.read_csv(CLEAN_CSV_PATH, parse_dates=["date"])


def check_no_nulls(df):
    """Hard gate: key columns must have no missing values."""
    key_cols = ["date", "region", "source", "generation_mwh"]
    nulls = df[key_cols].isnull().sum()
    if nulls.any():
        raise QualityError(f"Null values found:\n{nulls[nulls > 0]}")
    print("PASS: no nulls in key columns")


def check_duplicates(df):
    """Hard gate: one row per region + source + date."""
    dupes = df.duplicated(subset=["region", "source", "date"]).sum()
    if dupes > 0:
        raise QualityError(f"{dupes} duplicate region/source/date rows")
    print("PASS: no duplicate region/source/date combos")


def check_date_range(df):
    """Hard gate: dates must be sane (not future-dated beyond next month)."""
    latest = df["date"].max()
    cutoff = pd.Timestamp.now() + pd.DateOffset(months=2)
    if latest > cutoff:
        raise QualityError(f"Suspicious future date: {latest}")
    print(f"PASS: latest date {latest.date()} is sane")


def check_negatives(df):
    """Soft gate: allow small net-negatives, flag big ones.
    StatCan reports NET generation — idle plants can consume more than
    they produce, so small negatives are legitimate. Only large negatives
    signal a real data problem."""
    negatives = df[df["generation_mwh"] < 0]
    anomalies = df[df["generation_mwh"] < NEGATIVE_THRESHOLD_MWH]

    print(f"INFO: {len(negatives):,} net-negative rows (expected, legitimate)")

    if len(anomalies) > 0:
        raise QualityError(
            f"{len(anomalies)} rows below {NEGATIVE_THRESHOLD_MWH:,} MWh — "
            f"real anomaly, investigate:\n"
            f"{anomalies[['region','source','generation_mwh']].head()}"
        )
    print(f"PASS: no values below {NEGATIVE_THRESHOLD_MWH:,} MWh threshold")


def run_quality_checks(df=None):
    """Run all gates. Raises QualityError on any hard failure."""
    if df is None:
        df = load_clean()

    print(f"Running quality checks on {len(df):,} rows...\n")
    check_no_nulls(df)
    check_duplicates(df)
    check_date_range(df)
    check_negatives(df)
    print("\nAll quality checks passed.")
    return df


if __name__ == "__main__":
    run_quality_checks()