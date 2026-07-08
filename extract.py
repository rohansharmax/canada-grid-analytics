import requests
import zipfile
import io
import pandas as pd
from pathlib import Path

# StatCan Web Data Service
BASE_URL = "https://www150.statcan.gc.ca/t1/wds/rest"
PRODUCT_ID = "25100015"  # Electricity generation, monthly, by province + source

# Where we stash the raw pull
DATA_DIR = Path("data")
RAW_CSV_PATH = DATA_DIR / "raw_generation.csv"


def get_download_url():
    """Ask StatCan for the zip download link for our table."""
    endpoint = f"{BASE_URL}/getFullTableDownloadCSV/{PRODUCT_ID}/en"
    response = requests.get(endpoint)
    response.raise_for_status()  # crash loud if API errored (404, 500...)

    payload = response.json()
    if payload.get("status") != "SUCCESS":
        raise RuntimeError(f"API did not return success: {payload}")

    return payload["object"]  # the actual zip URL


def download_and_extract(zip_url):
    """Download the zip, unzip in memory, load the CSV into a DataFrame."""
    response = requests.get(zip_url)
    response.raise_for_status()

    # Hold the zip bytes in memory instead of writing a .zip to disk
    zip_bytes = io.BytesIO(response.content)

    with zipfile.ZipFile(zip_bytes) as z:
        # The zip holds the data CSV + a metadata CSV. We want the data one.
        csv_name = f"{PRODUCT_ID}.csv"
        with z.open(csv_name) as csv_file:
            df = pd.read_csv(csv_file, low_memory=False)

    return df


def extract(force_refresh=False):
    """Run full extract. Returns a DataFrame.
    Uses cached raw copy unless force_refresh=True."""
    DATA_DIR.mkdir(exist_ok=True)  # make data/ if missing

    # Use cache if we already pulled it (reproducible + polite to API)
    if RAW_CSV_PATH.exists() and not force_refresh:
        print(f"Loading cached raw data from {RAW_CSV_PATH}")
        return pd.read_csv(RAW_CSV_PATH, low_memory=False)

    print("Fetching fresh data from StatCan API...")
    zip_url = get_download_url()
    df = download_and_extract(zip_url)

    # Freeze the snapshot
    df.to_csv(RAW_CSV_PATH, index=False)
    print(f"Saved {len(df):,} rows to {RAW_CSV_PATH}")

    return df


if __name__ == "__main__":
    df = extract()
    print(df.head())
    print(f"\nShape: {df.shape}")
    print(f"Columns: {list(df.columns)}")