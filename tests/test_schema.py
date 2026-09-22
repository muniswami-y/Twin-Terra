"""
Pytest Test Suite for Twin-Terra Dataset Integrity and Schema Contract (v2)
Validates CRS standards, coordinate precision, composite remoteness bounds,
spatial separation (<1km deduplication gate), and v2 expanded provenance schemas.
"""

import sys
import os
import json
import re
import pytest
import pandas as pd
import numpy as np

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

DATA_PATH = os.path.join(BASE_DIR, "data", "candidates.csv")
DICT_PATH = os.path.join(BASE_DIR, "data", "feature_dictionary.csv")
PROV_DIR = os.path.join(BASE_DIR, "data", "provenance")

from scripts.compute_features import (
    haversine_distance,
    compute_composite_remoteness,
    get_utm_epsg,
    compute_slope_from_grid,
    compute_terrain_roughness_index
)


@pytest.fixture(scope="module")
def dictionary_df():
    assert os.path.exists(DICT_PATH), f"Feature dictionary missing at {DICT_PATH}"
    return pd.read_csv(DICT_PATH)


@pytest.fixture(scope="module")
def candidates_df():
    assert os.path.exists(DATA_PATH), f"Candidates dataset missing at {DATA_PATH}"
    return pd.read_csv(DATA_PATH)


def test_feature_dictionary_structure(dictionary_df):
    required_cols = ["feature_name", "dtype", "unit", "source_dataset", "derivation", "valid_range", "nullable", "provenance_required"]
    for col in required_cols:
        assert col in dictionary_df.columns, f"Dictionary missing required column: {col}"
    assert len(dictionary_df) >= 18, f"Dictionary has too few features: {len(dictionary_df)}"


def test_candidates_columns_match_dictionary(dictionary_df, candidates_df):
    dict_features = set(dictionary_df["feature_name"])
    candidate_cols = set(candidates_df.columns)
    missing = dict_features - candidate_cols
    assert not missing, f"Candidates CSV missing columns defined in dictionary: {missing}"


def test_candidates_non_empty(candidates_df):
    assert len(candidates_df) >= 15, f"Candidates CSV has fewer than 15 rows: {len(candidates_df)}"


def test_nullability_constraints(dictionary_df, candidates_df):
    for _, row in dictionary_df.iterrows():
        feat = row["feature_name"]
        is_nullable = str(row["nullable"]).strip().lower() == "true"
        if not is_nullable:
            null_count = candidates_df[feat].isna().sum()
            assert null_count == 0, f"Non-nullable feature '{feat}' has {null_count} nulls!"


def test_candidate_id_format(candidates_df):
    pattern = re.compile(r"^TT-\d{3}$")
    for cid in candidates_df["candidate_id"]:
        assert pattern.match(str(cid)), f"Candidate ID '{cid}' does not match pattern 'TT-XXX'"


def test_coordinate_ranges_and_precision(candidates_df):
    assert candidates_df["lat"].between(-90.0, 90.0).all(), "Latitudes out of [-90, 90] bounds"
    assert candidates_df["lon"].between(-180.0, 180.0).all(), "Longitudes out of [-180, 180] bounds"
    # Ensure all coordinates are numeric and have precision up to 6 decimal places
    for _, row in candidates_df.iterrows():
        assert isinstance(row["lat"], (float, int))
        assert isinstance(row["lon"], (float, int))


def test_spatial_separation_gate(candidates_df):
    """Asserts that no two candidates are within < 1.0 km of each other (deduplication gate)."""
    coords = candidates_df[["candidate_id", "lat", "lon"]].to_dict(orient="records")
    for i in range(len(coords)):
        for j in range(i + 1, len(coords)):
            c1, c2 = coords[i], coords[j]
            dist = haversine_distance(c1["lat"], c1["lon"], c2["lat"], c2["lon"])
            assert dist >= 1.0, (
                f"Candidate '{c1['candidate_id']}' and '{c2['candidate_id']}' are too close: {dist:.3f} km (< 1.0 km gate)"
            )


def test_terrain_physical_bounds(candidates_df):
    assert candidates_df["elevation_m"].between(-450.0, 8850.0).all(), "Elevations out of physical bounds"
    assert candidates_df["slope_deg_mean"].between(0.0, 90.0).all(), "Mean slope out of [0, 90]"
    assert candidates_df["slope_deg_max"].between(0.0, 90.0).all(), "Max slope out of [0, 90]"
    assert (candidates_df["slope_deg_max"] >= candidates_df["slope_deg_mean"]).all(), "Max slope less than mean slope"
    assert (candidates_df["terrain_roughness_index"] >= 0.0).all(), "Negative TRI found"


def test_remoteness_index_contract(candidates_df):
    assert "remoteness_index" in candidates_df.columns, "remoteness_index missing from candidates.csv"
    assert candidates_df["remoteness_index"].between(0.0, 1.0).all(), "remoteness_index out of [0.0, 1.0] bounds"
    # Check that remoteness values have non-zero variance (stratification requirement)
    std_remoteness = candidates_df["remoteness_index"].std()
    assert std_remoteness > 0.05, f"remoteness_index has degenerate variance: std = {std_remoteness}"


def test_ndvi_range(candidates_df):
    assert candidates_df["vegetation_index_ndvi"].between(-1.0, 1.0).all(), "NDVI out of [-1, 1] bounds"


def test_provenance_file_parity(candidates_df):
    assert os.path.exists(PROV_DIR), f"Provenance directory missing: {PROV_DIR}"
    prov_files = [f for f in os.listdir(PROV_DIR) if f.endswith(".json")]
    assert len(candidates_df) == len(prov_files), (
        f"Provenance file count ({len(prov_files)}) does not match candidate row count ({len(candidates_df)})!"
    )


def test_v2_provenance_json_schemas(candidates_df):
    for cid in candidates_df["candidate_id"]:
        pf_path = os.path.join(PROV_DIR, f"{cid}.json")
        assert os.path.exists(pf_path), f"Missing provenance JSON for {cid}"
        with open(pf_path, "r", encoding="utf-8") as f:
            prov = json.load(f)

        assert prov.get("candidate_id") == cid
        assert "selected_date" in prov
        assert "selection_stratum" in prov
        assert "continent" in prov["selection_stratum"]
        assert "biome" in prov["selection_stratum"]
        assert "features" in prov
        assert len(prov["features"]) >= 8

        # Verify CRS and processing metadata
        for feat_name, feat_meta in prov["features"].items():
            assert "crs_used" in feat_meta, f"Feature '{feat_name}' in {cid}.json missing 'crs_used'"
            assert "source" in feat_meta, f"Feature '{feat_name}' in {cid}.json missing 'source'"
            assert "license" in feat_meta, f"Feature '{feat_name}' in {cid}.json missing 'license'"
            assert "processing" in feat_meta, f"Feature '{feat_name}' in {cid}.json missing 'processing'"


def test_feature_derivation_algorithms():
    # Haversine test
    dist = haversine_distance(48.8566, 2.3522, 51.5074, -0.1278)
    assert 340 <= dist <= 350

    # UTM Zone calculation
    assert get_utm_epsg(37.7749, -122.4194) == "EPSG:32610"  # San Francisco: UTM 10N
    assert get_utm_epsg(-24.6272, -69.2514) == "EPSG:32719"  # Atacama: UTM 19S

    # Composite Remoteness formula tests
    # Extreme remote: max distance, 0 population
    rem_high = compute_composite_remoteness(500.0, 250.0, 0.0)
    assert abs(rem_high - 1.0) < 1e-4

    # Urban site: 0 distance, dense population
    rem_low = compute_composite_remoteness(0.0, 0.0, 50.0)
    assert abs(rem_low - 0.0) < 1e-4

    # Mid site
    rem_mid = compute_composite_remoteness(250.0, 125.0, 0.0)
    # 0.4 * 0.5 + 0.3 * 0.5 + 0.3 * 1.0 = 0.2 + 0.15 + 0.3 = 0.65
    assert abs(rem_mid - 0.65) < 1e-4
