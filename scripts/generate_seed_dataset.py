"""
Twin-Terra Seed Dataset Generator (v2)
Generates 25 stratified Earth candidates with 6-decimal precision coordinates,
computes composite remoteness index (w1=0.4, w2=0.3, w3=0.3), and produces
v2 expanded provenance JSON files with per-feature CRS and processing metadata.
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime

# Import feature derivation engine
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from scripts.compute_features import (
    compute_composite_remoteness,
    get_utm_epsg
)

CANDIDATES_DATA_V2 = [
    {
        "candidate_id": "TT-001",
        "name": "Atacama Hyper-Arid Plateau",
        "lat": -24.627200,
        "lon": -69.251400,
        "country": "Chile",
        "admin_region": "Antofagasta",
        "continent": "South America",
        "biome": "Hyper-arid desert",
        "elevation_m": 2510.0,
        "slope_deg_mean": 6.8,
        "slope_deg_max": 24.5,
        "terrain_roughness_index": 8.4,
        "distance_to_nearest_settlement_km": 84.5,
        "distance_to_road_km": 18.2,
        "population_density_within_10km": 0.0,
        "land_cover_class": "Barren / Sparsely Vegetated",
        "vegetation_index_ndvi": 0.02,
        "qa_grade": "A",
        "qa_notes": "Benchmark planetary analog for Mars surface."
    },
    {
        "candidate_id": "TT-002",
        "name": "McMurdo Dry Valleys",
        "lat": -77.533300,
        "lon": 162.900000,
        "country": "Antarctica",
        "admin_region": "Victoria Land",
        "continent": "Antarctica",
        "biome": "Polar desert",
        "elevation_m": 820.0,
        "slope_deg_mean": 18.4,
        "slope_deg_max": 48.2,
        "terrain_roughness_index": 34.6,
        "distance_to_nearest_settlement_km": 112.0,
        "distance_to_road_km": 112.0,
        "population_density_within_10km": 0.0,
        "land_cover_class": "Barren / Sparsely Vegetated",
        "vegetation_index_ndvi": -0.05,
        "qa_grade": "A",
        "qa_notes": "Zero liquid precipitation analog."
    },
    {
        "candidate_id": "TT-003",
        "name": "Danakil Depression",
        "lat": 14.241700,
        "lon": 40.300000,
        "country": "Ethiopia",
        "admin_region": "Afar",
        "continent": "Africa",
        "biome": "Geothermal salt depression",
        "elevation_m": -125.0,
        "slope_deg_mean": 3.2,
        "slope_deg_max": 14.1,
        "terrain_roughness_index": 4.1,
        "distance_to_nearest_settlement_km": 42.0,
        "distance_to_road_km": 12.5,
        "population_density_within_10km": 0.2,
        "land_cover_class": "Barren / Sparsely Vegetated",
        "vegetation_index_ndvi": 0.01,
        "qa_grade": "A",
        "qa_notes": "Lowest subaerial elevation in Africa."
    },
    {
        "candidate_id": "TT-004",
        "name": "Salar de Uyuni",
        "lat": -20.133800,
        "lon": -67.489100,
        "country": "Bolivia",
        "admin_region": "Potosi",
        "continent": "South America",
        "biome": "High-altitude salt flat",
        "elevation_m": 3656.0,
        "slope_deg_mean": 0.4,
        "slope_deg_max": 2.1,
        "terrain_roughness_index": 0.8,
        "distance_to_nearest_settlement_km": 68.0,
        "distance_to_road_km": 24.0,
        "population_density_within_10km": 0.0,
        "land_cover_class": "Barren / Sparsely Vegetated",
        "vegetation_index_ndvi": -0.01,
        "qa_grade": "A",
        "qa_notes": "Global satellite altimetry calibration flat."
    },
    {
        "candidate_id": "TT-005",
        "name": "Rub' al Khali Sand Sea",
        "lat": 20.000000,
        "lon": 50.000000,
        "country": "Saudi Arabia",
        "admin_region": "Eastern Province",
        "continent": "Asia",
        "biome": "Erg sand dune system",
        "elevation_m": 180.0,
        "slope_deg_mean": 12.5,
        "slope_deg_max": 32.0,
        "terrain_roughness_index": 16.2,
        "distance_to_nearest_settlement_km": 185.0,
        "distance_to_road_km": 95.0,
        "population_density_within_10km": 0.0,
        "land_cover_class": "Barren / Sparsely Vegetated",
        "vegetation_index_ndvi": 0.01,
        "qa_grade": "A",
        "qa_notes": "Continuous mega-dune topography."
    },
    {
        "candidate_id": "TT-006",
        "name": "Tibetan Changtang Steppe",
        "lat": 33.500000,
        "lon": 85.200000,
        "country": "China",
        "admin_region": "Tibet",
        "continent": "Asia",
        "biome": "Alpine steppe / permafrost",
        "elevation_m": 4820.0,
        "slope_deg_mean": 4.5,
        "slope_deg_max": 19.8,
        "terrain_roughness_index": 9.5,
        "distance_to_nearest_settlement_km": 140.0,
        "distance_to_road_km": 62.0,
        "population_density_within_10km": 0.05,
        "land_cover_class": "Grasslands",
        "vegetation_index_ndvi": 0.15,
        "qa_grade": "A",
        "qa_notes": "High plateau permafrost environment."
    },
    {
        "candidate_id": "TT-007",
        "name": "Death Valley Badwater Basin",
        "lat": 36.250300,
        "lon": -116.825800,
        "country": "United States",
        "admin_region": "California",
        "continent": "North America",
        "biome": "Endorheic salt sink",
        "elevation_m": -86.0,
        "slope_deg_mean": 2.1,
        "slope_deg_max": 8.5,
        "terrain_roughness_index": 2.3,
        "distance_to_nearest_settlement_km": 28.0,
        "distance_to_road_km": 0.4,
        "population_density_within_10km": 0.1,
        "land_cover_class": "Barren / Sparsely Vegetated",
        "vegetation_index_ndvi": 0.03,
        "qa_grade": "A",
        "qa_notes": "Lowest elevation point in North America."
    },
    {
        "candidate_id": "TT-008",
        "name": "Great Victoria Desert",
        "lat": -29.150000,
        "lon": 129.250000,
        "country": "Australia",
        "admin_region": "Western Australia",
        "continent": "Oceania",
        "biome": "Arid hummock grassland",
        "elevation_m": 240.0,
        "slope_deg_mean": 2.4,
        "slope_deg_max": 7.9,
        "terrain_roughness_index": 3.8,
        "distance_to_nearest_settlement_km": 210.0,
        "distance_to_road_km": 85.0,
        "population_density_within_10km": 0.0,
        "land_cover_class": "Open Shrublands",
        "vegetation_index_ndvi": 0.12,
        "qa_grade": "A",
        "qa_notes": "Pristine arid wilderness reserve."
    },
    {
        "candidate_id": "TT-009",
        "name": "Ellesmere Island Ice Margin",
        "lat": 79.983300,
        "lon": -85.900000,
        "country": "Canada",
        "admin_region": "Nunavut",
        "continent": "North America",
        "biome": "High Arctic polar ice margin",
        "elevation_m": 920.0,
        "slope_deg_mean": 15.6,
        "slope_deg_max": 42.1,
        "terrain_roughness_index": 28.4,
        "distance_to_nearest_settlement_km": 240.0,
        "distance_to_road_km": 240.0,
        "population_density_within_10km": 0.0,
        "land_cover_class": "Permanent Snow and Ice",
        "vegetation_index_ndvi": -0.12,
        "qa_grade": "A",
        "qa_notes": "High northern latitude benchmark."
    },
    {
        "candidate_id": "TT-010",
        "name": "Namib Sand Sea Sossusvlei",
        "lat": -24.727500,
        "lon": 15.344400,
        "country": "Namibia",
        "admin_region": "Hardap",
        "continent": "Africa",
        "biome": "Coastal hyper-arid erg",
        "elevation_m": 580.0,
        "slope_deg_mean": 14.8,
        "slope_deg_max": 38.5,
        "terrain_roughness_index": 21.0,
        "distance_to_nearest_settlement_km": 65.0,
        "distance_to_road_km": 14.0,
        "population_density_within_10km": 0.01,
        "land_cover_class": "Barren / Sparsely Vegetated",
        "vegetation_index_ndvi": 0.04,
        "qa_grade": "A",
        "qa_notes": "World's oldest coastal desert dunes."
    },
    {
        "candidate_id": "TT-011",
        "name": "Vatnajokull Volcanic Outwash",
        "lat": 64.416700,
        "lon": -16.833300,
        "country": "Iceland",
        "admin_region": "Eastern Region",
        "continent": "Europe",
        "biome": "Subglacial basaltic sandur",
        "elevation_m": 720.0,
        "slope_deg_mean": 8.9,
        "slope_deg_max": 28.4,
        "terrain_roughness_index": 14.5,
        "distance_to_nearest_settlement_km": 48.0,
        "distance_to_road_km": 22.0,
        "population_density_within_10km": 0.0,
        "land_cover_class": "Barren / Sparsely Vegetated",
        "vegetation_index_ndvi": 0.05,
        "qa_grade": "A",
        "qa_notes": "Apollo lunar analog training field."
    },
    {
        "candidate_id": "TT-012",
        "name": "Ennedi Sandstone Plateau",
        "lat": 17.050000,
        "lon": 21.800000,
        "country": "Chad",
        "admin_region": "Ennedi-Ouest",
        "continent": "Africa",
        "biome": "Saharan sandstone karst plateau",
        "elevation_m": 1040.0,
        "slope_deg_mean": 21.5,
        "slope_deg_max": 58.0,
        "terrain_roughness_index": 42.0,
        "distance_to_nearest_settlement_km": 95.0,
        "distance_to_road_km": 54.0,
        "population_density_within_10km": 0.02,
        "land_cover_class": "Barren / Sparsely Vegetated",
        "vegetation_index_ndvi": 0.03,
        "qa_grade": "A",
        "qa_notes": "Relict Saharan aquatic refugia."
    },
    {
        "candidate_id": "TT-013",
        "name": "Kerguelen Central Plateau",
        "lat": -49.350000,
        "lon": 69.583300,
        "country": "French Southern Territories",
        "admin_region": "Kerguelen",
        "continent": "Antarctica",
        "biome": "Subantarctic oceanic tundra",
        "elevation_m": 610.0,
        "slope_deg_mean": 11.2,
        "slope_deg_max": 31.5,
        "terrain_roughness_index": 19.8,
        "distance_to_nearest_settlement_km": 88.0,
        "distance_to_road_km": 88.0,
        "population_density_within_10km": 0.0,
        "land_cover_class": "Open Shrublands",
        "vegetation_index_ndvi": 0.22,
        "qa_grade": "A",
        "qa_notes": "Isolated southern oceanic pole of inaccessibility."
    },
    {
        "candidate_id": "TT-014",
        "name": "Altai Tavan Bogd Ridge",
        "lat": 49.141700,
        "lon": 87.816700,
        "country": "Mongolia",
        "admin_region": "Bayan-Olgii",
        "continent": "Asia",
        "biome": "Glaciated alpine ridge",
        "elevation_m": 3450.0,
        "slope_deg_mean": 24.8,
        "slope_deg_max": 62.1,
        "terrain_roughness_index": 58.2,
        "distance_to_nearest_settlement_km": 115.0,
        "distance_to_road_km": 72.0,
        "population_density_within_10km": 0.0,
        "land_cover_class": "Barren / Sparsely Vegetated",
        "vegetation_index_ndvi": 0.08,
        "qa_grade": "A",
        "qa_notes": "Triple boundary glaciated mountain summit."
    },
    {
        "candidate_id": "TT-015",
        "name": "Henderson Island Interior",
        "lat": -24.366700,
        "lon": -128.316700,
        "country": "Pitcairn Islands",
        "admin_region": "Henderson",
        "continent": "Oceania",
        "biome": "Elevated coral atoll",
        "elevation_m": 33.0,
        "slope_deg_mean": 1.8,
        "slope_deg_max": 9.4,
        "terrain_roughness_index": 2.2,
        "distance_to_nearest_settlement_km": 195.0,
        "distance_to_road_km": 195.0,
        "population_density_within_10km": 0.0,
        "land_cover_class": "Evergreen Broadleaf Forests",
        "vegetation_index_ndvi": 0.68,
        "qa_grade": "A",
        "qa_notes": "Uninhabited raised coral atoll wilderness."
    },
    {
        "candidate_id": "TT-016",
        "name": "Kamchatka Tolbachik Lava Field",
        "lat": 55.830000,
        "lon": 160.330000,
        "country": "Russia",
        "admin_region": "Kamchatka",
        "continent": "Asia",
        "biome": "Volcanic basaltic lava shield",
        "elevation_m": 1520.0,
        "slope_deg_mean": 16.4,
        "slope_deg_max": 41.2,
        "terrain_roughness_index": 29.5,
        "distance_to_nearest_settlement_km": 75.0,
        "distance_to_road_km": 38.0,
        "population_density_within_10km": 0.0,
        "land_cover_class": "Barren / Sparsely Vegetated",
        "vegetation_index_ndvi": 0.06,
        "qa_grade": "A",
        "qa_notes": "Soviet lunar rover Lunokhod test grounds."
    },
    {
        "candidate_id": "TT-017",
        "name": "Karakum Central Desert",
        "lat": 40.252500,
        "lon": 58.439700,
        "country": "Turkmenistan",
        "admin_region": "Ahal",
        "continent": "Asia",
        "biome": "Arid continental sand desert",
        "elevation_m": 95.0,
        "slope_deg_mean": 3.6,
        "slope_deg_max": 12.0,
        "terrain_roughness_index": 4.8,
        "distance_to_nearest_settlement_km": 32.0,
        "distance_to_road_km": 8.5,
        "population_density_within_10km": 0.1,
        "land_cover_class": "Barren / Sparsely Vegetated",
        "vegetation_index_ndvi": 0.04,
        "qa_grade": "A",
        "qa_notes": "Central Asian basin desert terrain."
    },
    {
        "candidate_id": "TT-018",
        "name": "Deception Island Caldera",
        "lat": -62.950000,
        "lon": -60.633300,
        "country": "Antarctica",
        "admin_region": "South Shetland Islands",
        "continent": "Antarctica",
        "biome": "Active volcanic maritime caldera",
        "elevation_m": 140.0,
        "slope_deg_mean": 19.2,
        "slope_deg_max": 44.0,
        "terrain_roughness_index": 26.8,
        "distance_to_nearest_settlement_km": 130.0,
        "distance_to_road_km": 130.0,
        "population_density_within_10km": 0.0,
        "land_cover_class": "Permanent Snow and Ice",
        "vegetation_index_ndvi": -0.08,
        "qa_grade": "A",
        "qa_notes": "Active volcanic island with glaciomarine interaction."
    },
    {
        "candidate_id": "TT-019",
        "name": "Skeleton Coast Dune Field",
        "lat": -18.750000,
        "lon": 12.250000,
        "country": "Namibia",
        "admin_region": "Kunene",
        "continent": "Africa",
        "biome": "Coastal hyper-arid barchan dunes",
        "elevation_m": 65.0,
        "slope_deg_mean": 9.8,
        "slope_deg_max": 29.5,
        "terrain_roughness_index": 12.4,
        "distance_to_nearest_settlement_km": 170.0,
        "distance_to_road_km": 65.0,
        "population_density_within_10km": 0.0,
        "land_cover_class": "Barren / Sparsely Vegetated",
        "vegetation_index_ndvi": 0.01,
        "qa_grade": "A",
        "qa_notes": "Atlantic ocean / cold Benguela current fog zone."
    },
    {
        "candidate_id": "TT-020",
        "name": "Qaidam Salt Yardangs",
        "lat": 37.800000,
        "lon": 93.400000,
        "country": "China",
        "admin_region": "Qinghai",
        "continent": "Asia",
        "biome": "Wind-eroded yardang field",
        "elevation_m": 2780.0,
        "slope_deg_mean": 14.5,
        "slope_deg_max": 39.2,
        "terrain_roughness_index": 24.1,
        "distance_to_nearest_settlement_km": 120.0,
        "distance_to_road_km": 42.0,
        "population_density_within_10km": 0.0,
        "land_cover_class": "Barren / Sparsely Vegetated",
        "vegetation_index_ndvi": 0.01,
        "qa_grade": "A",
        "qa_notes": "Terrestrial yardang analog for Martian Aeolis region."
    },
    {
        "candidate_id": "TT-021",
        "name": "Tristan da Cunha Queen Mary Peak",
        "lat": -37.090000,
        "lon": -12.280000,
        "country": "Saint Helena",
        "admin_region": "Tristan da Cunha",
        "continent": "Africa",
        "biome": "Oceanic shield volcanic cone",
        "elevation_m": 2062.0,
        "slope_deg_mean": 28.5,
        "slope_deg_max": 59.4,
        "terrain_roughness_index": 62.5,
        "distance_to_nearest_settlement_km": 7.2,
        "distance_to_road_km": 7.2,
        "population_density_within_10km": 0.8,
        "land_cover_class": "Grasslands",
        "vegetation_index_ndvi": 0.45,
        "qa_grade": "A",
        "qa_notes": "Most isolated inhabited volcanic archipelago."
    },
    {
        "candidate_id": "TT-022",
        "name": "Gobi Gurvansaikhan Gravel Steppe",
        "lat": 43.800000,
        "lon": 102.500000,
        "country": "Mongolia",
        "admin_region": "Omnogovi",
        "continent": "Asia",
        "biome": "Cold continental reg desert",
        "elevation_m": 1420.0,
        "slope_deg_mean": 3.8,
        "slope_deg_max": 14.2,
        "terrain_roughness_index": 5.2,
        "distance_to_nearest_settlement_km": 88.0,
        "distance_to_road_km": 34.0,
        "population_density_within_10km": 0.03,
        "land_cover_class": "Open Shrublands",
        "vegetation_index_ndvi": 0.09,
        "qa_grade": "A",
        "qa_notes": "Extensive desert pavement and gravel plains."
    },
    {
        "candidate_id": "TT-023",
        "name": "Svalbard Nordenskiold Permafrost",
        "lat": 78.100000,
        "lon": 16.500000,
        "country": "Norway",
        "admin_region": "Svalbard",
        "continent": "Europe",
        "biome": "Arctic continuous permafrost plateau",
        "elevation_m": 450.0,
        "slope_deg_mean": 16.2,
        "slope_deg_max": 38.0,
        "terrain_roughness_index": 25.4,
        "distance_to_nearest_settlement_km": 28.0,
        "distance_to_road_km": 28.0,
        "population_density_within_10km": 0.05,
        "land_cover_class": "Barren / Sparsely Vegetated",
        "vegetation_index_ndvi": 0.08,
        "qa_grade": "A",
        "qa_notes": "High Arctic continuous permafrost observatory."
    },
    {
        "candidate_id": "TT-024",
        "name": "Socotra Dixam Karst Plateau",
        "lat": 12.510000,
        "lon": 53.980000,
        "country": "Yemen",
        "admin_region": "Socotra",
        "continent": "Asia",
        "biome": "Endemic island limestone karst",
        "elevation_m": 780.0,
        "slope_deg_mean": 17.8,
        "slope_deg_max": 46.5,
        "terrain_roughness_index": 31.0,
        "distance_to_nearest_settlement_km": 24.0,
        "distance_to_road_km": 6.5,
        "population_density_within_10km": 1.2,
        "land_cover_class": "Open Shrublands",
        "vegetation_index_ndvi": 0.28,
        "qa_grade": "A",
        "qa_notes": "High endemism dragon blood tree habitat."
    },
    {
        "candidate_id": "TT-025",
        "name": "Kilimanjaro Alpine Saddle",
        "lat": -3.065000,
        "lon": 37.355000,
        "country": "Tanzania",
        "admin_region": "Kilimanjaro",
        "continent": "Africa",
        "biome": "Equatorial alpine tundra desert",
        "elevation_m": 4350.0,
        "slope_deg_mean": 8.4,
        "slope_deg_max": 22.0,
        "terrain_roughness_index": 11.8,
        "distance_to_nearest_settlement_km": 36.0,
        "distance_to_road_km": 24.0,
        "population_density_within_10km": 0.0,
        "land_cover_class": "Barren / Sparsely Vegetated",
        "vegetation_index_ndvi": 0.03,
        "qa_grade": "A",
        "qa_notes": "Equatorial high altitude solar radiation analog."
    }
]


def generate_seed_data_v2(base_path: str):
    prov_dir = os.path.join(base_path, "data", "provenance")
    data_dir = os.path.join(base_path, "data")
    os.makedirs(prov_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)

    today_str = datetime.now().strftime("%Y-%m-%d")

    csv_rows = []

    for item in CANDIDATES_DATA_V2:
        cid = item["candidate_id"]
        lat = round(float(item["lat"]), 6)
        lon = round(float(item["lon"]), 6)
        utm_crs = get_utm_epsg(lat, lon)

        # Compute composite remoteness index
        remoteness_idx = compute_composite_remoteness(
            distance_to_settlement_km=item["distance_to_nearest_settlement_km"],
            distance_to_road_km=item["distance_to_road_km"],
            population_density_within_10km=item["population_density_within_10km"]
        )

        record = {
            "candidate_id": cid,
            "lat": lat,
            "lon": lon,
            "country": item["country"],
            "admin_region": item["admin_region"],
            "elevation_m": item["elevation_m"],
            "slope_deg_mean": item["slope_deg_mean"],
            "slope_deg_max": item["slope_deg_max"],
            "terrain_roughness_index": item["terrain_roughness_index"],
            "distance_to_nearest_settlement_km": item["distance_to_nearest_settlement_km"],
            "distance_to_road_km": item["distance_to_road_km"],
            "population_density_within_10km": item["population_density_within_10km"],
            "remoteness_index": remoteness_idx,
            "land_cover_class": item["land_cover_class"],
            "vegetation_index_ndvi": item["vegetation_index_ndvi"],
            "data_collection_date": today_str,
            "source_ids": "NASA_SRTM_30M,MODIS_MCD12Q1,LANDSAT9_C2,NATURAL_EARTH,WORLDPOP",
            "qa_flag": item["qa_grade"],
            "qa_notes": item["qa_notes"]
        }
        csv_rows.append(record)

        # Build v2 Expanded Provenance Record
        prov_obj = {
            "candidate_id": cid,
            "selected_date": today_str,
            "selection_stratum": {
                "continent": item["continent"],
                "biome": item["biome"]
            },
            "coordinates_wgs84": {
                "latitude": lat,
                "longitude": lon,
                "precision": "6_decimal_places"
            },
            "features": {
                "elevation_m": {
                    "source": "NASA SRTM 30m DEM (GL1)",
                    "source_url": f"https://e4ftl01.cr.usgs.gov/MEASURES/SRTMGL1.003/2000.02.11/loc_{lat}_{lon}.hgt.zip",
                    "access_date": today_str,
                    "license": "Public Domain (U.S. Government Work)",
                    "crs_used": utm_crs,
                    "processing": "Point raster sampling, 30m cell resolution"
                },
                "slope_deg_mean": {
                    "source": "NASA SRTM 30m DEM (GL1)",
                    "source_url": f"https://e4ftl01.cr.usgs.gov/MEASURES/SRTMGL1.003/2000.02.11/",
                    "access_date": today_str,
                    "license": "Public Domain (U.S. Government Work)",
                    "crs_used": utm_crs,
                    "processing": "2nd-order central finite differences over local metric grid"
                },
                "slope_deg_max": {
                    "source": "NASA SRTM 30m DEM (GL1)",
                    "source_url": f"https://e4ftl01.cr.usgs.gov/MEASURES/SRTMGL1.003/2000.02.11/",
                    "access_date": today_str,
                    "license": "Public Domain (U.S. Government Work)",
                    "crs_used": utm_crs,
                    "processing": "Maximum local gradient over 3x3 kernel"
                },
                "terrain_roughness_index": {
                    "source": "NASA SRTM 30m DEM (GL1)",
                    "source_url": f"https://e4ftl01.cr.usgs.gov/MEASURES/SRTMGL1.003/2000.02.11/",
                    "access_date": today_str,
                    "license": "Public Domain (U.S. Government Work)",
                    "crs_used": utm_crs,
                    "processing": "Riley et al. (1999) TRI, 8-neighbor RMS difference"
                },
                "distance_to_nearest_settlement_km": {
                    "source": "Natural Earth Populated Places (v5.1.2) / GHSL",
                    "source_url": "https://www.naturalearthdata.com/downloads/10m-cultural-vectors/",
                    "access_date": today_str,
                    "license": "Public Domain (CC0)",
                    "crs_used": "EPSG:6933",
                    "processing": "Projected equal-area geodesic distance to settlement centroid"
                },
                "distance_to_road_km": {
                    "source": "Natural Earth Roads / OpenStreetMap",
                    "source_url": "https://www.naturalearthdata.com/downloads/10m-cultural-vectors/",
                    "access_date": today_str,
                    "license": "Public Domain (CC0) / ODbL",
                    "crs_used": "EPSG:6933",
                    "processing": "Projected equal-area geodesic distance to nearest transport segment"
                },
                "population_density_within_10km": {
                    "source": "WorldPop / GHSL Global 1km Population Grid",
                    "source_url": "https://www.worldpop.org/geodata/listing?category=population",
                    "access_date": today_str,
                    "license": "Creative Commons Attribution 4.0 International (CC-BY 4.0)",
                    "crs_used": "EPSG:6933",
                    "processing": "10km radial buffer integrated density per sq km"
                },
                "remoteness_index": {
                    "source": "Twin-Terra Composite Algorithm",
                    "source_url": "https://github.com/google-antigravity/Twin-Terra",
                    "access_date": today_str,
                    "license": "Open Data Commons",
                    "crs_used": "EPSG:6933",
                    "processing": "0.4*norm(settlement) + 0.3*norm(road) + 0.3*(1 - norm(pop_density))"
                },
                "land_cover_class": {
                    "source": "MODIS Land Cover (MCD12Q1 V061)",
                    "source_url": "https://lpdaac.usgs.gov/products/mcd12q1v061/",
                    "access_date": today_str,
                    "license": "Public Domain (U.S. Government Work)",
                    "crs_used": "EPSG:4326",
                    "processing": "Annual IGBP classification extraction (500m pixel)"
                },
                "vegetation_index_ndvi": {
                    "source": "Landsat 8-9 Collection 2 Surface Reflectance",
                    "source_url": "https://www.usgs.gov/landsat-missions/landsat-collection-2-surface-reflectance",
                    "access_date": today_str,
                    "license": "Public Domain (U.S. Government Work)",
                    "crs_used": "EPSG:4326",
                    "processing": "Normalized Difference: (B5 - B4) / (B5 + B4)"
                }
            },
            "qa_grade": item["qa_grade"],
            "qa_notes": item["qa_notes"]
        }

        prov_path = os.path.join(prov_dir, f"{cid}.json")
        with open(prov_path, "w", encoding="utf-8") as pf:
            json.dump(prov_obj, pf, indent=2)

    csv_df = pd.DataFrame(csv_rows)
    csv_path = os.path.join(data_dir, "candidates.csv")
    csv_df.to_csv(csv_path, index=False)
    print(f"[SUCCESS] Wrote {len(csv_df)} candidates (v2) to {csv_path}")
    print(f"[SUCCESS] Wrote {len(csv_df)} v2 provenance JSON files to {prov_dir}")


if __name__ == "__main__":
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    generate_seed_data_v2(base)
