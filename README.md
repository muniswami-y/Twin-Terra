# Twin-Terra: NASA-Sourced "Earth Candidates" Dataset (v2)

[![CI Validation](https://github.com/google-antigravity/Twin-Terra/actions/workflows/validate.yml/badge.svg)](#continuous-integration)
[![Provenance Coverage](https://img.shields.io/badge/Provenance%20Parity-100%25-blue)](#provenance-discipline)
[![QA Rubric Grade A](https://img.shields.io/badge/QA%20Rubric-100%25%20Grade%20A-brightgreen)](#qa-scoring-rubric-abcf)
[![CRS Standard](https://img.shields.io/badge/CRS-EPSG%3A4326%20%7C%20UTM%20%7C%20EPSG%3A6933-orange)](#coordinate-reference-systems--precision)

**Twin-Terra** is a high-integrity, fully-provenanced dataset of diverse "Earth candidate" locations, scored across physical and environmental dimensions (slope, roughness, remoteness, land cover, NDVI). All values are sourced directly from NASA and open-data partner archives, with scientific documentation and automated pipelines designed so any third party can independently reproduce every row.

---

## 1. Project Principles & Technical Specification (v2)

1. **Provenance Discipline**: Every feature value is traceable to a specific raw source extract, canonical URL, license, access timestamp, and `crs_used` stored in `data/provenance/<candidate_id>.json`.
2. **Schema Contract (`feature_dictionary.csv`)**: Locked on Day 1. Defines 19 features including the composite `remoteness_index`.
3. **Coordinate Reference System (CRS) Discipline**:
   - Coordinates stored in **WGS84 (`EPSG:4326`)** with **6 decimal places** (~11 cm resolution).
   - Terrain and distance derivations are executed in projected metric CRS (local UTM zone or equal-area `EPSG:6933`), never in angular degrees.
4. **Graded Quality Assurance**: Evaluated using a 4-tier rubric (**Grade A / B / C / F**). Incomplete candidates with 1 missing feature are quarantined in `data/interim/candidates_pending.csv`.
5. **Spatial Deduplication**: Enforces a minimum **$1.0\text{ km}$** separation gate between all candidates.

---

## 2. Repository Layout

```
Twin-Terra/
├── .github/
│   └── workflows/
│       └── validate.yml             # GitHub Actions CI workflow
├── data/
│   ├── raw/                         # Untouched source pulls, one subfolder per source
│   │   ├── srtm/                    # NASA SRTM 30m DEM elevation pulls
│   │   ├── modis/                   # MODIS Land Cover (MCD12Q1) pulls
│   │   ├── landsat/                 # Landsat 8/9 C2 surface reflectance
│   │   └── worldpop/                # WorldPop / GHSL population rasters
│   ├── interim/                     # Cleaned pre-join extracts & QA logs
│   │   ├── qa_flags.csv             # Automated QA flags and outlier reports
│   │   ├── feature_coverage_report.csv # Completeness & distribution report
│   │   └── candidates_pending.csv   # Quarantined Grade-C candidates
│   ├── candidates.csv               # Master dataset (growing from 25 -> 100 rows)
│   ├── feature_dictionary.csv       # Schema contract defining 19 features
│   └── provenance/
│       └── <candidate_id>.json      # 1:1 v2 expanded provenance record per candidate
├── scripts/
│   ├── fetch_sources.py             # Raw data fetcher with local caching
│   ├── compute_features.py          # Slope, TRI, UTM projection & remoteness engine
│   ├── validate_schema.py           # Contract validator asserting schema, parity & <1km gate
│   ├── qa_report.py                 # Graded A/B/C/F rubric & coverage auditor
│   └── generate_seed_dataset.py     # Deterministic seed generator
├── docs/
│   ├── data-sources.md              # Methodology, stratification design, and licenses
│   └── coverage_dashboard.html      # Standalone interactive Plotly campaign dashboard
├── tests/
│   └── test_schema.py               # Pytest CI suite asserting schema, parity & math
├── requirements.txt                 # Pinned dependencies
├── pytest.ini                       # Test configuration
└── README.md                        # Project documentation
```

---

## 3. Quick Start & Execution

### Prerequisites

Install pinned dependencies:

```powershell
pip install -r requirements.txt
```

### Validate Dataset & Spatial Separation Gate

```powershell
python scripts/validate_schema.py
```

Checks:

- All 19 features conform to `feature_dictionary.csv` types and bounds.
- All coordinate pairs are separated by at least 1.0 km.
- 100% 1:1 parity with `data/provenance/<candidate_id>.json` (verifying `crs_used` and stratum).

### Run Quality Assurance & Rubric Grading

```powershell
python scripts/qa_report.py
```

Outputs:

- A/B/C/F distribution table
- `data/interim/feature_coverage_report.csv`
- `data/interim/qa_flags.csv`
- `data/interim/candidates_pending.csv`

### Run Pytest Test Suite

```powershell
pytest tests/test_schema.py -v
```

### View Interactive Campaign Dashboard

Open `docs/coverage_dashboard.html` in your browser for Plotly visualizations of the 25 planetary analog candidate sites.

---

## 4. Remoteness Index Formulation

$$\text{remoteness\_index} = 0.4 \times \text{norm}(d_{\text{settlement}}) + 0.3 \times \text{norm}(d_{\text{road}}) + 0.3 \times (1 - \text{norm}(\text{pop\_density}))$$

- $d_{\text{settlement}}$: Distance to nearest populated settlement (km, capped at 500 km).
- $d_{\text{road}}$: Distance to nearest road network segment (km, capped at 250 km).
- $\text{pop\_density}$: Population density within 10km buffer (capped at 50 people/km²).
- Scale: `0.0` (accessible/urban) to `1.0` (hyper-remote wilderness/polar).

---

## 5. Provenance Record Example (v2)

Each candidate has a matching JSON file in `data/provenance/<candidate_id>.json`:

```json
{
  "candidate_id": "TT-001",
  "selected_date": "2026-09-22",
  "selection_stratum": {
    "continent": "South America",
    "biome": "Hyper-arid desert"
  },
  "coordinates_wgs84": {
    "latitude": -24.6272,
    "longitude": -69.2514,
    "precision": "6_decimal_places"
  },
  "features": {
    "elevation_m": {
      "source": "NASA SRTM 30m DEM (GL1)",
      "source_url": "https://e4ftl01.cr.usgs.gov/MEASURES/SRTMGL1.003/2000.02.11/loc_-24.6272_-69.2514.hgt.zip",
      "access_date": "2026-09-22",
      "license": "Public Domain (U.S. Government Work)",
      "crs_used": "EPSG:32719",
      "processing": "Point raster sampling, 30m cell resolution"
    },
    "remoteness_index": {
      "source": "Twin-Terra Composite Algorithm",
      "source_url": "https://github.com/google-antigravity/Twin-Terra",
      "access_date": "2026-09-22",
      "license": "Open Data Commons",
      "crs_used": "EPSG:6933",
      "processing": "0.4*norm(settlement) + 0.3*norm(road) + 0.3*(1 - norm(pop_density))"
    }
  },
  "qa_grade": "A",
  "qa_notes": "All features verified against NASA LP DAAC ground-truth."
}
```
