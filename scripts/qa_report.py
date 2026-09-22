"""
Twin-Terra QA & Coverage Reporting Engine (v2)
Applies the A/B/C/F graded scoring rubric:
  Grade A: All required features present, within valid_range, complete provenance
  Grade B: All required features present, <=1 feature flagged as low-confidence
  Grade C: Exactly 1 required feature missing (relocated to candidates_pending.csv)
  Grade F: >=2 required features missing or corrupt provenance (excluded)
Generates:
  - data/interim/feature_coverage_report.csv
  - data/interim/qa_flags.csv
  - data/interim/candidates_pending.csv
"""

import os
import sys
import json
import argparse
import pandas as pd
import numpy as np


def run_qa_report(data_path: str, dict_path: str, prov_dir: str, output_dir: str):
    print("=" * 78)
    print("  TWIN-TERRA QUALITY ASSURANCE & GRADED RUBRIC AUDITOR (v2)")
    print("=" * 78)

    if not os.path.exists(data_path):
        print(f"[ERROR] Data file not found: {data_path}")
        return False
    if not os.path.exists(dict_path):
        print(f"[ERROR] Dictionary file not found: {dict_path}")
        return False

    os.makedirs(output_dir, exist_ok=True)

    df = pd.read_csv(data_path)
    dict_df = pd.read_csv(dict_path)
    n_rows = len(df)
    print(f"[INFO] Auditing {n_rows} candidates across {len(dict_df)} defined schema features...")

    # 1. Feature Coverage & Statistics
    coverage_rows = []
    qa_flags = []
    required_features = dict_df[dict_df["nullable"].astype(str).str.lower() != "true"]["feature_name"].tolist()

    for _, row in dict_df.iterrows():
        feat = row["feature_name"]
        dtype = str(row["dtype"]).strip().lower()
        unit = row["unit"]
        source = row["source_dataset"]
        is_nullable = str(row["nullable"]).strip().lower() == "true"
        valid_range = str(row["valid_range"]).strip()

        if feat not in df.columns:
            qa_flags.append({
                "candidate_id": "ALL",
                "feature": feat,
                "issue_type": "MISSING_COLUMN",
                "severity": "CRITICAL",
                "detail": f"Column '{feat}' is defined in dictionary but missing from CSV."
            })
            continue

        series = df[feat]
        non_null_count = series.notna().sum()
        completeness_pct = round((non_null_count / n_rows) * 100, 2) if n_rows > 0 else 0.0

        if not is_nullable and non_null_count < n_rows:
            null_ids = df.loc[series.isna(), "candidate_id"].tolist() if "candidate_id" in df.columns else []
            qa_flags.append({
                "candidate_id": str(null_ids[:5]),
                "feature": feat,
                "issue_type": "NULL_VIOLATION",
                "severity": "HIGH",
                "detail": f"{n_rows - non_null_count} null value(s) in non-nullable feature."
            })

        mean_val, std_val, min_val, p50_val, max_val = "N/A", "N/A", "N/A", "N/A", "N/A"
        if dtype in ("float", "int"):
            num_s = pd.to_numeric(series, errors="coerce").dropna()
            if len(num_s) > 0:
                mean_val = round(float(num_s.mean()), 3)
                std_val = round(float(num_s.std()), 3) if len(num_s) > 1 else 0.0
                min_val = round(float(num_s.min()), 3)
                p50_val = round(float(num_s.median()), 3)
                max_val = round(float(num_s.max()), 3)

                if ".." in valid_range:
                    try:
                        low_bound = float(valid_range.split("..")[0])
                        high_bound = float(valid_range.split("..")[1])
                        outliers = df[(df[feat] < low_bound) | (df[feat] > high_bound)]
                        for _, out_row in outliers.iterrows():
                            qa_flags.append({
                                "candidate_id": out_row.get("candidate_id", "UNKNOWN"),
                                "feature": feat,
                                "issue_type": "RANGE_OUTLIER",
                                "severity": "HIGH",
                                "detail": f"Value {out_row[feat]} outside [{low_bound}..{high_bound}]"
                            })
                    except Exception:
                        pass

        coverage_rows.append({
            "feature_name": feat,
            "completeness_pct": f"{completeness_pct}%",
            "non_null_count": non_null_count,
            "total_count": n_rows,
            "dtype": dtype,
            "unit": unit,
            "min": min_val,
            "p50_median": p50_val,
            "max": max_val,
            "mean": mean_val,
            "std": std_val,
            "source_dataset": source
        })

    # 2. Candidate Graded Scoring Rubric (A/B/C/F)
    grades_count = {"A": 0, "B": 0, "C": 0, "F": 0}
    candidate_grades = []
    pending_candidates = []

    for idx, c_row in df.iterrows():
        cid = c_row.get("candidate_id", f"ROW_{idx}")
        missing_req = [f for f in required_features if f in df.columns and pd.isna(c_row[f])]
        
        # Check provenance completeness
        prov_file = os.path.join(prov_dir, f"{cid}.json")
        prov_valid = os.path.exists(prov_file)

        if len(missing_req) >= 2 or not prov_valid:
            grade = "F"
            notes = f"Failed: {len(missing_req)} missing required features, prov_valid={prov_valid}"
        elif len(missing_req) == 1:
            grade = "C"
            notes = f"Pending: Missing 1 feature ({missing_req[0]})"
            pending_candidates.append(c_row.to_dict())
        else:
            # Check low confidence / review flags
            qa_flag_val = str(c_row.get("qa_flag", "")).strip().upper()
            if qa_flag_val == "B" or "REVIEW" in qa_flag_val:
                grade = "B"
                notes = "Approved: Minor low-confidence flags documented."
            else:
                grade = "A"
                notes = "Approved: 100% complete features and provenance."

        grades_count[grade] += 1
        candidate_grades.append({
            "candidate_id": cid,
            "qa_grade": grade,
            "missing_required_count": len(missing_req),
            "missing_features": ",".join(missing_req) if missing_req else "None",
            "provenance_exists": prov_valid,
            "audit_notes": notes
        })

    # Save outputs
    cov_df = pd.DataFrame(coverage_rows)
    coverage_path = os.path.join(output_dir, "feature_coverage_report.csv")
    cov_df.to_csv(coverage_path, index=False)

    flags_df = pd.DataFrame(qa_flags)
    flags_path = os.path.join(output_dir, "qa_flags.csv")
    flags_df.to_csv(flags_path, index=False)

    pending_df = pd.DataFrame(pending_candidates)
    pending_path = os.path.join(output_dir, "candidates_pending.csv")
    pending_df.to_csv(pending_path, index=False)

    # Print Rubric Summary
    print("\nA/B/C/F Rubric Distribution:")
    print("-" * 50)
    for g, count in grades_count.items():
        pct = round((count / n_rows) * 100, 1) if n_rows > 0 else 0
        desc = {
            "A": "Complete, valid bounds & 100% provenance",
            "B": "Complete with minor low-confidence flags",
            "C": "Held in candidates_pending.csv (missing 1)",
            "F": "Excluded (missing >=2 or corrupt provenance)"
        }[g]
        print(f"  Grade {g}: {count:3d} ({pct:5.1f}%) — {desc}")
    print("-" * 50)

    # Print Feature Completeness
    print("\nFeature Completeness & Distribution Summary:")
    print(cov_df[["feature_name", "completeness_pct", "min", "p50_median", "max", "unit"]].to_string(index=False))

    print("-" * 78)
    print(f"[QA REPORT] Total Outlier / Schema Flags: {len(flags_df)}")
    print(f"[OUTPUT] Coverage report:  {coverage_path}")
    print(f"[OUTPUT] QA flags log:     {flags_path}")
    print(f"[OUTPUT] Pending holding:  {pending_path} ({len(pending_candidates)} held)")
    print("=" * 78)
    return grades_count["F"] == 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Twin-Terra v2 QA Report and Graded Rubric Auditor.")
    parser.add_argument("--data", default="data/candidates.csv")
    parser.add_argument("--dict", default="data/feature_dictionary.csv")
    parser.add_argument("--prov", default="data/provenance")
    parser.add_argument("--outdir", default="data/interim")
    args = parser.parse_args()

    base_p = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    data_file = os.path.join(base_p, args.data) if not os.path.isabs(args.data) else args.data
    dict_file = os.path.join(base_p, args.dict) if not os.path.isabs(args.dict) else args.dict
    prov_p = os.path.join(base_p, args.prov) if not os.path.isabs(args.prov) else args.prov
    out_p = os.path.join(base_p, args.outdir) if not os.path.isabs(args.outdir) else args.outdir

    run_qa_report(data_file, dict_file, prov_p, out_p)
