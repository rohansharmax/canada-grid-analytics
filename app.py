import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st
from pathlib import Path

DB_PATH = Path("data") / "grid.db"

st.set_page_config(page_title="Canada Grid Analytics", layout="wide")


@st.cache_data
def load_data():
    """Join the star schema back into a flat frame for charting."""
    with sqlite3.connect(DB_PATH) as conn:
        query = """
            SELECT d.date, d.year, d.month,
                   r.region, s.source,
                   f.generation_mwh
            FROM fact_generation f
            JOIN dim_region r ON f.region_id = r.region_id
            JOIN dim_source s ON f.source_id = s.source_id
            JOIN dim_date   d ON f.date_id   = d.date_id
        """
        df = pd.read_sql(query, conn, parse_dates=["date"])
    return df


df = load_data()

st.title("Canada Grid Analytics")
st.caption("Monthly electricity generation by province and source — StatCan table 25-10-0015-01")

# --- Sidebar filters ---
st.sidebar.header("Filters")
regions = sorted(df["region"].unique())
region = st.sidebar.selectbox("Province / Territory", regions,
                              index=regions.index("Ontario") if "Ontario" in regions else 0)

sources = sorted(df["source"].unique())
picked_sources = st.sidebar.multiselect("Sources", sources, default=sources)

year_min, year_max = int(df["year"].min()), int(df["year"].max())
year_range = st.sidebar.slider("Year range", year_min, year_max, (year_min, year_max))

# --- Apply filters ---
mask = (
    (df["region"] == region)
    & (df["source"].isin(picked_sources))
    & (df["year"].between(year_range[0], year_range[1]))
)
view = df[mask]

# --- KPIs ---
col1, col2, col3 = st.columns(3)
col1.metric("Total generation (GWh)", f"{view['generation_mwh'].sum()/1000:,.0f}")
col2.metric("Sources shown", view["source"].nunique())
col3.metric("Months covered", view["date"].nunique())

# --- Time series ---
st.subheader(f"Generation over time — {region}")
ts = view.groupby(["date", "source"], as_index=False)["generation_mwh"].sum()
fig = px.line(ts, x="date", y="generation_mwh", color="source",
              labels={"generation_mwh": "Generation (MWh)", "date": "Date"})
st.plotly_chart(fig, use_container_width=True)

# --- Source mix (latest year in range) ---
st.subheader("Source mix")
latest_year = view["year"].max()
mix = view[view["year"] == latest_year].groupby("source", as_index=False)["generation_mwh"].sum()
fig2 = px.pie(mix, names="source", values="generation_mwh",
              title=f"Generation mix by source — {latest_year}")
st.plotly_chart(fig2, use_container_width=True)