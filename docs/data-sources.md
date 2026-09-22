# Twin-Terra: Data Sources, Methodology & Provenance Catalog (v2)

This document serves as the authoritative methodology and catalog for all datasets, spatial standards, and sampling strata integrated into the Twin-Terra "Earth candidates" dataset.

---

## 1. Primary Data Sources Summary

| Source Dataset                           | Domain                          | Agency / Provider                             | NASA Source? | Access Method & Endpoint                         | Auth Required          | License                | Update Cadence |
| :--------------------------------------- | :------------------------------ | :-------------------------------------------- | :----------- | :----------------------------------------------- | :--------------------- | :--------------------- | :------------- |
| **SRTM 30m DEM (GL1)**                   | Elevation & Terrain             | NASA / USGS LP DAAC                           | **Yes**      | LP DAAC / Earthdata Search / USGS 3DEP API       | Earthdata Login (free) | Public Domain (US Gov) | Static (v3.0)  |
| **MODIS Land Cover (MCD12Q1)**           | Biome & Land Cover              | NASA EOSDIS / LP DAAC                         | **Yes**      | Earthdata OpenDAP / AppEEARS API                 | Earthdata Login (free) | Public Domain (US Gov) | Annual         |
| **Landsat 8/9 OLI/TIRS C2**              | Spectral NDVI & Reflectance     | NASA / USGS                                   | **Yes**      | USGS EarthExplorer / AWS STAC                    | None for STAC on AWS   | Public Domain (US Gov) | 16-day cycle   |
| **NASA POWER**                           | Climate & Solar Radiation       | NASA Langley Research Center                  | **Yes**      | REST API (`power.larc.nasa.gov/api`)             | None (Public Open API) | Public Domain (US Gov) | Daily updates  |
| **WorldPop Gridded Population**          | Population Density & Remoteness | WorldPop Research Group (Univ of Southampton) | **Partner**  | REST API / Cloud-Optimized GeoTIFF               | None                   | CC-BY 4.0              | Annual         |
| **Global Human Settlement Layer (GHSL)** | Built-up Presence & Settlements | European Commission JRC                       | **Partner**  | Open Data portal / WMS / GeoTIFF                 | None                   | CC-BY 4.0              | Multi-year     |
| **Natural Earth (1:10m)**                | Populated Places, Roads, Admin  | Natural Earth Contributors                    | **Partner**  | GeoPackage via `naturalearthdata.com`            | None                   | Public Domain (CC0)    | Periodic       |
| **OpenStreetMap (Overpass API)**         | Roads, Tracks & Infrastructure  | OpenStreetMap Foundation                      | **Partner**  | Overpass API (`overpass-api.de/api/interpreter`) | Rate-limited / Free    | ODbL 1.0               | Real-time      |

---

## 2. Coordinate Reference System (CRS) & Spatial Discipline

Spatial calculations must never be performed directly in angular degrees to avoid severe geometric distortion across latitudes. Twin-Terra adheres to strict CRS rules:

1. **Storage CRS**: All candidate coordinates in `candidates.csv` are stored as **WGS84 (`EPSG:4326`)** in decimal degrees rounded to **6 decimal places** (~11 cm ground resolution).
2. **Local Terrain Calculations**: Slope, aspect, and Terrain Roughness Index (TRI) are computed on DEM tiles reprojected into the candidate's **local UTM zone** (`EPSG:32601`–`EPSG:32660` for Northern Hemisphere, `EPSG:32701`–`EPSG:32760` for Southern Hemisphere).
3. **Global Geodesic & Distance Operations**: Distance to settlements and roads is calculated using ellipsoidal geodesics (Haversine/Karney) or projected equal-area CRS (**`EPSG:6933` World Cylindrical Equal Area**).
4. **Provenance Metadata**: Every computed feature in `data/provenance/<candidate_id>.json` explicitly declares the `crs_used`.

---

## 3. Physical & Environmental Derivations

### 3.1 Slope & Roughness Formulas

- **Slope in Degrees**:
  $$\text{slope\_deg} = \arctan\left(\sqrt{\left(\frac{\partial z}{\partial x}\right)^2 + \left(\frac{\partial z}{\partial y}\right)^2}\right) \times \frac{180}{\pi}$$
  Computed using 2nd-order central finite differences across $30\text{m} \times 30\text{m}$ projected grid nodes.
- **Terrain Ruggedness Index (TRI)** (Riley et al. 1999):
  $$\text{TRI} = \frac{1}{8} \sum_{i=1}^{8} \left| z_{\text{center}} - z_{\text{neighbor}, i} \right|$$
  Computed across a fixed $3 \times 3$ neighborhood window (and cross-checked over $90\text{m} \times 90\text{m}$).

### 3.2 Composite Remoteness Index Contract

To eliminate ambiguity, `remoteness_index` is defined as a bounded normalized weighted composite:
$$\text{remoteness\_index} = w_1 \cdot \text{norm}(d_{\text{settlement}}) + w_2 \cdot \text{norm}(d_{\text{road}}) + w_3 \cdot (1 - \text{norm}(\text{pop\_density}))$$

- **Locked Weights**:
  - $w_1 = 0.4$ (Distance to nearest settlement)
  - $w_2 = 0.3$ (Distance to nearest road)
  - $w_3 = 0.3$ (Inverse population density within 10 km)
- **Normalization Bounds**:
  - $d_{\text{settlement}}$ capped at $500\text{ km}$ ($1.0 = \ge 500\text{ km}$)
  - $d_{\text{road}}$ capped at $250\text{ km}$ ($1.0 = \ge 250\text{ km}$)
  - $\text{pop\_density}$ capped at $50\text{ people/km}^2$ ($1.0 = \ge 50\text{ people/km}^2$)

---

## 4. Stratified Sampling Design

To prevent geographic clustering or bias toward easily accessible regions, candidate selection is balanced across three stratification axes:

1. **Continent Strata**:
   - ~15–20 candidates per inhabited continent (Africa, Asia, Europe, North America, South America, Oceania) plus benchmark sites in Antarctica.
2. **Biome & Terrain Strata** (based on WWF Terrestrial Ecoregions / Köppen climate classes):
   - _Hyper-arid / Erg Desert_: Atacama, Rub' al Khali, Namib, Gobi
   - _Polar Desert & Continuous Permafrost_: McMurdo Dry Valleys, Ellesmere Island, Svalbard
   - _High-Altitude Plateau & Alpine_: Tibetan Changtang, Altai, Andes (Salar de Uyuni)
   - _Endorheic Depression & Salt Sink_: Danakil Depression, Death Valley
   - _Active Volcanic & Lava Field_: Kamchatka Tolbachik, Iceland Vatnajökull, Deception Island
   - _Isolated Oceanic Island & Atoll_: Henderson Island, Kerguelen, Tristan da Cunha, Socotra
3. **Remoteness Variance**:
   - Deliberately includes both hyper-remote wilderness locations ($d > 200\text{ km}$) and intermediate sites ($d \sim 10\text{–}50\text{ km}$) to ensure non-degenerate variance across the remoteness spectrum.
4. **Spatial Deduplication Constraint**:
   - Minimum separation of **$1.0\text{ km}$** between any two candidate points (enforced in CI).

---

## 5. Provenance JSON Schema (v2 Expanded)

Each candidate has a companion JSON in `data/provenance/<candidate_id>.json`:

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
    "longitude": -69.2514
  },
  "features": {
    "elevation_m": {
      "source": "NASA SRTM 30m DEM (GL1)",
      "source_url": "https://e4ftl01.cr.usgs.gov/MEASURES/SRTMGL1.003/2000.02.11/",
      "access_date": "2026-09-22",
      "license": "Public Domain (U.S. Government Work)",
      "crs_used": "EPSG:32719",
      "processing": "2nd-order central differences, 30m resolution"
    },
    "remoteness_index": {
      "source": "Computed Composite Index",
      "source_url": "Internal Algorithm",
      "access_date": "2026-09-22",
      "license": "Open Data Commons",
      "crs_used": "EPSG:6933",
      "processing": "0.4*norm(dist_settle) + 0.3*norm(dist_road) + 0.3*(1-norm(pop_density))"
    }
  },
  "qa_grade": "A",
  "qa_notes": "All features verified against NASA LP DAAC ground-truth."
}
```

---

## 6. QA Scoring Rubric (A/B/C/F)

| Grade | Meaning                                                                       | Action                                        |
| :---- | :---------------------------------------------------------------------------- | :-------------------------------------------- |
| **A** | All required features present, within `valid_range`, 100% provenance complete | Approved for master `candidates.csv`          |
| **B** | All required features present, $\le 1$ feature flagged as low-confidence      | Approved for master `candidates.csv`          |
| **C** | Exactly 1 required feature missing, flagged and documented                    | Held in `data/interim/candidates_pending.csv` |
| **F** | $\ge 2$ required features missing or provenance corrupt/missing               | Excluded from dataset                         |
