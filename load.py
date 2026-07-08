import sqlite3
import pandas as pd
from pathlib import Path

DATA_DIR = Path("data")
CLEAN_CSV_PATH = DATA_DIR / "clean_generation.csv"
DB_PATH = DATA_DIR / "grid.db"


def load_clean():
    return pd.read_csv(CLEAN_CSV_PATH, parse_dates=["date"])


def build_star_schema(df):
    """Split the flat table into a star schema:
    - dim_region, dim_source, dim_date (dimension tables)
    - fact_generation (the numbers, linked by keys)."""

    # --- Dimension: region ---
    dim_region = (
        df[["region"]].drop_duplicates().reset_index(drop=True)
        .reset_index().rename(columns={"index": "region_id"})
    )

    # --- Dimension: source ---
    dim_source = (
        df[["source"]].drop_duplicates().reset_index(drop=True)
        .reset_index().rename(columns={"index": "source_id"})
    )

    # --- Dimension: date ---
    dim_date = df[["date"]].drop_duplicates().reset_index(drop=True)
    dim_date["year"] = dim_date["date"].dt.year
    dim_date["month"] = dim_date["date"].dt.month
    dim_date = dim_date.reset_index().rename(columns={"index": "date_id"})

    # --- Fact: join back to get the integer keys ---
    fact = (
        df.merge(dim_region, on="region")
          .merge(dim_source, on="source")
          .merge(dim_date[["date_id", "date"]], on="date")
    )
    fact = fact[["date_id", "region_id", "source_id", "generation_mwh", "vector"]]

    return dim_region, dim_source, dim_date, fact


def load_to_db(dims_and_fact):
    dim_region, dim_source, dim_date, fact = dims_and_fact

    with sqlite3.connect(DB_PATH) as conn:
        dim_region.to_sql("dim_region", conn, if_exists="replace", index=False)
        dim_source.to_sql("dim_source", conn, if_exists="replace", index=False)
        dim_date.to_sql("dim_date", conn, if_exists="replace", index=False)
        fact.to_sql("fact_generation", conn, if_exists="replace", index=False)

        # Indexes on the foreign keys = faster joins
        cur = conn.cursor()
        cur.execute("CREATE INDEX IF NOT EXISTS idx_fact_region ON fact_generation(region_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_fact_source ON fact_generation(source_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_fact_date ON fact_generation(date_id)")
        conn.commit()

    print(f"Loaded star schema to {DB_PATH}")
    print(f"  dim_region: {len(dim_region)} rows")
    print(f"  dim_source: {len(dim_source)} rows")
    print(f"  dim_date:   {len(dim_date)} rows")
    print(f"  fact_generation: {len(fact):,} rows")


def load(df=None):
    if df is None:
        df = load_clean()
    schema = build_star_schema(df)
    load_to_db(schema)


if __name__ == "__main__":
    load()