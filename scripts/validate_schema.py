"""
Twin-Terra Schema & Proximity Validation Script (v2)
Enforces data/feature_dictionary.csv constraints against data/candidates.csv,
asserts 1:1 provenance JSON parity with v2 expanded schemas (crs_used, stratum),
and enforces a minimum 1.0 km spatial separation gate between all candidates.
"""

import os
import sys
import json
import re
import math
import argparse
import pandas as pd
import numpy as np

# Import distance function
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from scripts.compute_features import haversine_distance


def parse_range(range_str: str):
    """Parses range strings like '-90..90', '0..1', '0..5000'."""
    range_str = str(range_str).strip()
    if range_str in ("N/A", "", "nan"):
        return None, None
    if ".." in range_str:
        parts = range_str.split("..")
        try:
            low = float(parts[0])
            high = float(parts[1])
            return low, high
        except ValueError:
            return None, None
    return None, None


def validate_schema(data_path: str, dict_path: str, prov_dir: str) -> bool:
    print("=" * 75)
    print("  TWIN-TERRA DATASET CONTRACT VALIDATOR (v2)")
    print("=" * 75)

    errors = []
    warnings = []

    # 1. Load Feature Dictionary
    if not os.path.exists(dict_path):
        print(f"[CRITICAL ERROR] Feature dictionary not found at: {dict_path}")
        return False

    dict_df = pd.read_csv(dict_path)
    required_dict_cols = ["feature_name", "dtype", "valid_range", "nullable", "provenance_required"]
    for col in required_dict_cols:
        if col not in dict_df.columns:
            print(f"[CRITICAL ERROR] Feature dictionary missing schema column: '{col}'")
            return False

    print(f"[OK] Loaded feature dictionary with {len(dict_df)} feature definitions from {dict_path}")

    # 2. Load Master Candidates Dataset
    if not os.path.exists(data_path):
        print(f"[CRITICAL ERROR] Candidates dataset not found at: {data_path}")
        return False

    try:
        candidates_df = pd.read_csv(data_path)
    except Exception as e:
        print(f"[CRITICAL ERROR] Failed to parse {data_path}: {e}")
        return False

    print(f"[OK] Loaded candidates dataset with {len(candidates_df)} rows and {len(candidates_df.columns)} columns")

    # 3. Check Column Presence & Completeness
    dict_features = dict_df.set_index("feature_name").to_dict(orient="index")
    candidate_cols = set(candidates_df.columns)

    missing_cols = set(dict_features.keys()) - candidate_cols
    if missing_cols:
        for mc in missing_cols:
            errors.append(f"Missing required feature column in candidates.csv: '{mc}'")

    extra_cols = candidate_cols - set(dict_features.keys())
    if extra_cols:
        for ec in extra_cols:
            warnings.append(f"Unregistered column in candidates.csv: '{ec}'")

    # 4. Check Data Types, Nullability, and Value Ranges
    for feat_name, rule in dict_features.items():
        if feat_name not in candidates_df.columns:
            continue

        series = candidates_df[feat_name]
        expected_dtype = str(rule.get("dtype", "")).strip().lower()
        is_nullable = str(rule.get("nullable", "")).strip().lower() == "true"
        valid_range_str = str(rule.get("valid_range", "")).strip()

        # Check Nullability
        null_count = series.isna().sum()
        if not is_nullable and null_count > 0:
            errors.append(f"Feature '{feat_name}' is non-nullable but contains {null_count} null/NaN values.")

        # Check Numeric Types and Ranges
        if expected_dtype in ("float", "int"):
            numeric_series = pd.to_numeric(series, errors="coerce")
            non_numeric = series[numeric_series.isna() & series.notna()]
            if len(non_numeric) > 0:
                errors.append(f"Feature '{feat_name}' expected {expected_dtype} but found non-numeric: {non_numeric.tolist()[:3]}")

            low, high = parse_range(valid_range_str)
            if low is not None and high is not None:
                out_of_bounds = numeric_series[(numeric_series < low) | (numeric_series > high)]
                if len(out_of_bounds) > 0:
                    errors.append(
                        f"Feature '{feat_name}' has {len(out_of_bounds)} values out of range [{low} .. {high}]. Example: {out_of_bounds.tolist()[:3]}"
                    )
        elif expected_dtype == "string":
            if valid_range_str.startswith("TT-"):
                pattern = re.compile(valid_range_str)
                bad_ids = [val for val in series.dropna() if not pattern.match(str(val))]
                if bad_ids:
                    errors.append(f"Candidate IDs do not match pattern '{valid_range_str}': {bad_ids[:3]}")
            elif "|" in valid_range_str:
                allowed = [opt.strip() for opt in valid_range_str.split("|")]
                bad_enums = [val for val in series.dropna() if str(val).strip() not in allowed]
                if bad_enums:
                    errors.append(f"Feature '{feat_name}' contains invalid enum values: {bad_enums[:3]}")

    # 5. Spatial Proximity Deduplication Gate (< 1.0 km)
    print("[INFO] Checking spatial proximity (<1.0 km duplicate gate)...")
    coords = candidates_df[["candidate_id", "lat", "lon"]].dropna().to_dict(orient="records")
    proximity_violations = []
    for i in range(len(coords)):
        for j in range(i + 1, len(coords)):
            c1, c2 = coords[i], coords[j]
            dist = haversine_distance(c1["lat"], c1["lon"], c2["lat"], c2["lon"])
            if dist < 1.0:
                proximity_violations.append((c1["candidate_id"], c2["candidate_id"], dist))

    if proximity_violations:
        for v in proximity_violations:
            errors.append(f"Proximity violation: candidates '{v[0]}' and '{v[1]}' are within {v[2]:.3f} km (< 1.0 km)")
    else:
        print(f"[OK] Spatial deduplication verified: all {len(coords)} candidates are > 1.0 km apart.")

    # 6. Provenance 1:1 Parity and v2 Expanded Schema Check
    if not os.path.exists(prov_dir):
        errors.append(f"Provenance directory does not exist: {prov_dir}")
    else:
        prov_files = [f for f in os.listdir(prov_dir) if f.endswith(".json")]
        candidate_ids = candidates_df["candidate_id"].dropna().astype(str).tolist() if "candidate_id" in candidates_df.columns else []

        print(f"[INFO] Found {len(prov_files)} provenance files in {prov_dir} for {len(candidate_ids)} candidates")

        for cid in candidate_ids:
            expected_file = os.path.join(prov_dir, f"{cid}.json")
            if not os.path.exists(expected_file):
                errors.append(f"Missing provenance JSON file for candidate '{cid}': expected {expected_file}")
            else:
                try:
                    with open(expected_file, "r", encoding="utf-8") as pf:
                        prov_data = json.load(pf)

                    # v2 Structure Checks
                    for req_key in ["candidate_id", "selected_date", "selection_stratum", "features", "qa_grade"]:
                        if req_key not in prov_data:
                            errors.append(f"Provenance file '{cid}.json' missing required v2 field: '{req_key}'")

                    # Check selection stratum
                    stratum = prov_data.get("selection_stratum", {})
                    if "continent" not in stratum or "biome" not in stratum:
                        errors.append(f"Provenance '{cid}.json' selection_stratum missing 'continent' or 'biome'")

                    # Check features dictionary and crs_used
                    features_dict = prov_data.get("features", {})
                    if not isinstance(features_dict, dict) or len(features_dict) == 0:
                        errors.append(f"Provenance '{cid}.json' has empty or invalid 'features' dictionary")
                    else:
                        for f_name, f_meta in features_dict.items():
                            if "crs_used" not in f_meta:
                                errors.append(f"Provenance '{cid}.json' feature '{f_name}' missing 'crs_used' field")
                            if "source" not in f_meta or "license" not in f_meta:
                                errors.append(f"Provenance '{cid}.json' feature '{f_name}' missing source/license")

                except Exception as ex:
                    errors.append(f"Corrupt provenance JSON file for '{cid}': {ex}")

        # Check orphan provenance files
        expected_prov_names = {f"{cid}.json" for cid in candidate_ids}
        for pf in prov_files:
            if pf not in expected_prov_names:
                warnings.append(f"Orphan provenance file detected: '{pf}'")

    # 7. Summary Report
    print("-" * 75)
    if warnings:
        print(f"[WARNINGS] {len(warnings)} non-fatal warning(s) detected:")
        for w in warnings:
            print(f"  [!] {w}")
    else:
        print("[OK] Zero warnings detected.")

    print("-" * 75)
    if errors:
        print(f"[FAILED] {len(errors)} validation error(s) found:")
        for err in errors:
            print(f"  [X] {err}")
        print("=" * 75)
        return False
    else:
        print(f"[PASSED] All v2 schema rules, spatial separation, and 1:1 provenance checks passed!")
        print("=" * 75)
        return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate Twin-Terra v2 candidates against feature dictionary.")
    parser.add_argument("--data", default="data/candidates.csv")
    parser.add_argument("--dict", default="data/feature_dictionary.csv")
    parser.add_argument("--prov", default="data/provenance")
    args = parser.parse_args()

    base_p = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    data_file = os.path.join(base_p, args.data) if not os.path.isabs(args.data) else args.data
    dict_file = os.path.join(base_p, args.dict) if not os.path.isabs(args.dict) else args.dict
    prov_path = os.path.join(base_p, args.prov) if not os.path.isabs(args.prov) else args.prov

    success = validate_schema(data_file, dict_file, prov_path)
    sys.exit(0 if success else 1)
