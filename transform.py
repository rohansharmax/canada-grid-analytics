import pandas as pd
from pathlib import Path

DATA_DIR = Path("data")
RAW_CSV_PATH = DATA_DIR / "raw_generation.csv"
CLEAN_CSV_PATH = DATA_DIR / "clean_generation.csv"


def load_raw():
    """Load the raw extract saved by extract.py."""
    return pd.read_csv(RAW_CSV_PATH, low_memory=False)


def select_and_rename(df):
    """Keep only useful columns, rename to clean lowercase names."""
    keep = {
        "REF_DATE": "date",
        "GEO": "region",
        "Class of electricity producer": "producer_class",
        "Type of electricity generation": "source",
        "VALUE": "generation_mwh",
        "VECTOR": "vector",
    }
    df = df[list(keep.keys())]   # keep only these columns, in this order
    df = df.rename(columns=keep) # rename them
    return df


def parse_dates(df):
    """Convert 'date' from text like '2008-01' into a real datetime."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m")
    return df


def filter_totals(df):
    """Remove aggregate rows to avoid double-counting.
    Keep: provinces (not Canada), individual sources (not 'Total'),
    and only the 'Total all classes' producer level."""
    df = df.copy()

    # 1. Drop the national total — we keep provinces, can re-sum later
    df = df[df["region"] != "Canada"]

   # 2. Drop ALL total/subtotal source rows — keep only real generation types
    df = df[~df["source"].str.startswith("Total")]

    # 3. Keep ONLY the total-all-classes producer level (avoid class double-count)
    df = df[df["producer_class"] == "Total all classes of electricity producer"]

    # producer_class is now one constant value — drop the column, it's dead weight
    df = df.drop(columns=["producer_class"])

    return df


def drop_missing(df):
    """Remove rows with no generation value — can't use them."""
    df = df.copy()
    before = len(df)
    df = df.dropna(subset=["generation_mwh"])
    after = len(df)
    print(f"Dropped {before - after:,} rows with missing generation values")
    return df


def transform(save=True):
    """Run the full transform pipeline. Returns clean DataFrame."""
    df = load_raw()
    print(f"Loaded {len(df):,} raw rows")

    df = select_and_rename(df)
    df = parse_dates(df)
    df = filter_totals(df)
    df = drop_missing(df)

    # Sort for sanity — chronological, grouped by region + source
    df = df.sort_values(["region", "source", "date"]).reset_index(drop=True)

    print(f"Final clean dataset: {len(df):,} rows")

    if save:
        df.to_csv(CLEAN_CSV_PATH, index=False)
        print(f"Saved to {CLEAN_CSV_PATH}")

    return df


if __name__ == "__main__":
    df = transform()
    print(df.head())
    print(f"\nShape: {df.shape}")
    print(f"Regions: {df['region'].nunique()}")
    print(f"Sources: {df['source'].nunique()}")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")