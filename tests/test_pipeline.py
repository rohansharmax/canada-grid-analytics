import pandas as pd
import pytest
from transform import select_and_rename, parse_dates, filter_totals
from quality import check_negatives, check_duplicates, QualityError, NEGATIVE_THRESHOLD_MWH


def sample_raw():
    return pd.DataFrame({
        "REF_DATE": ["2020-01", "2020-01"],
        "GEO": ["Ontario", "Canada"],
        "Class of electricity producer": ["Total all classes of electricity producer"] * 2,
        "Type of electricity generation": ["Hydraulic turbine", "Total all types of electricity generation"],
        "VALUE": [100.0, 500.0],
        "VECTOR": ["v1", "v2"],
    })


def test_rename_produces_clean_columns():
    df = select_and_rename(sample_raw())
    assert "generation_mwh" in df.columns
    assert "region" in df.columns


def test_parse_dates_returns_datetime():
    df = parse_dates(select_and_rename(sample_raw()))
    assert pd.api.types.is_datetime64_any_dtype(df["date"])


def test_filter_removes_canada_and_totals():
    df = filter_totals(parse_dates(select_and_rename(sample_raw())))
    assert "Canada" not in df["region"].values
    assert "Total all types of electricity generation" not in df["source"].values
    assert len(df) == 1


def test_small_negatives_pass():
    df = pd.DataFrame({
        "date": pd.to_datetime(["2020-01-01"]),
        "region": ["Ontario"], "source": ["Wind"],
        "generation_mwh": [-50.0],
    })
    check_negatives(df)


def test_big_negatives_raise():
    df = pd.DataFrame({
        "date": pd.to_datetime(["2020-01-01"]),
        "region": ["Ontario"], "source": ["Wind"],
        "generation_mwh": [NEGATIVE_THRESHOLD_MWH - 1],
    })
    with pytest.raises(QualityError):
        check_negatives(df)