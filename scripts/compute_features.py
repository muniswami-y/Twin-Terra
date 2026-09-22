"""
Twin-Terra Feature Computation Engine (v2)
Derives physical and environmental metrics using projected coordinate systems,
Riley et al. (1999) TRI, finite-difference slope gradients, and the
composite remoteness index contract (0.4 / 0.3 / 0.3).
"""

import math
import numpy as np
import pandas as pd
from typing import Tuple, List, Dict, Optional


def get_utm_epsg(lat: float, lon: float) -> str:
    """
    Determines the appropriate local Universal Transverse Mercator (UTM)
    projected CRS EPSG code for a given WGS84 coordinate.
    """
    zone = int((lon + 180.0) / 6.0) + 1
    if zone > 60:
        zone = 60
    elif zone < 1:
        zone = 1

    if lat >= 0:
        return f"EPSG:326{zone:02d}"
    else:
        return f"EPSG:327{zone:02d}"


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes great-circle distance between two points in kilometers
    using the Haversine formula on WGS84 sphere.
    """
    R = 6371.0088  # Mean Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 3)


def compute_composite_remoteness(
    distance_to_settlement_km: float,
    distance_to_road_km: float,
    population_density_within_10km: float,
    weights: Tuple[float, float, float] = (0.4, 0.3, 0.3),
    max_settlement_km: float = 500.0,
    max_road_km: float = 250.0,
    max_pop_density: float = 50.0
) -> float:
    """
    Computes the composite remoteness index per Twin-Terra contract:
      remoteness_index = w1 * norm(dist_settle) + w2 * norm(dist_road) + w3 * (1 - norm(pop_density))
    where weights default to (0.4, 0.3, 0.3) and output is strictly within [0.0, 1.0].
    """
    w1, w2, w3 = weights
    assert abs((w1 + w2 + w3) - 1.0) < 1e-6, "Weights must sum to 1.0"

    # Normalize components to [0.0, 1.0]
    norm_settle = min(max(distance_to_settlement_km / max_settlement_km, 0.0), 1.0)
    norm_road = min(max(distance_to_road_km / max_road_km, 0.0), 1.0)
    norm_pop = min(max(population_density_within_10km / max_pop_density, 0.0), 1.0)

    remoteness = (w1 * norm_settle) + (w2 * norm_road) + (w3 * (1.0 - norm_pop))
    return round(float(min(max(remoteness, 0.0), 1.0)), 4)


def compute_slope_from_grid(elevation_matrix: np.ndarray, cell_size_m: float = 30.0) -> Tuple[float, float]:
    """
    Derives mean and maximum slope in degrees from an NxN elevation grid
    projected in local metric units using 2nd-order central finite differences.
    """
    if elevation_matrix.shape[0] < 3 or elevation_matrix.shape[1] < 3:
        raise ValueError("Elevation grid must be at least 3x3 for slope calculation.")

    dz_dy, dz_dx = np.gradient(elevation_matrix, cell_size_m, cell_size_m)
    gradient_magnitude = np.sqrt(dz_dx**2 + dz_dy**2)
    slope_degrees = np.degrees(np.arctan(gradient_magnitude))

    mean_slope = float(np.mean(slope_degrees))
    max_slope = float(np.max(slope_degrees))
    return round(mean_slope, 2), round(max_slope, 2)


def compute_terrain_roughness_index(elevation_matrix: np.ndarray) -> float:
    """
    Computes Riley, DeGloria, and Elliot (1999) Terrain Roughness Index (TRI)
    as the root-mean-square elevation difference between the center cell and its 8 neighbors.
    """
    center_y = elevation_matrix.shape[0] // 2
    center_x = elevation_matrix.shape[1] // 2
    center_elevation = elevation_matrix[center_y, center_x]

    neighborhood = elevation_matrix[center_y - 1 : center_y + 2, center_x - 1 : center_x + 2]
    squared_diffs = []

    for r in range(3):
        for c in range(3):
            if r == 1 and c == 1:
                continue
            squared_diffs.append((neighborhood[r, c] - center_elevation) ** 2)

    tri = float(np.sqrt(np.mean(squared_diffs)))
    return round(tri, 2)


def generate_local_elevation_kernel(center_elevation: float, base_slope_deg: float, roughness: float, size: int = 5) -> np.ndarray:
    """
    Generates a local elevation kernel centered on a given elevation in metric units.
    """
    grid = np.zeros((size, size))
    center = size // 2
    cell_spacing_m = 30.0  # Projected metric cell size (e.g. UTM)

    tan_slope = math.tan(math.radians(base_slope_deg))
    azimuth_rad = math.radians(45.0)
    dx_factor = math.cos(azimuth_rad) * tan_slope * cell_spacing_m
    dy_factor = math.sin(azimuth_rad) * tan_slope * cell_spacing_m

    for i in range(size):
        for j in range(size):
            di = i - center
            dj = j - center
            micro_rough = roughness * (math.sin(i * 1.5) * math.cos(j * 1.5))
            grid[i, j] = center_elevation + (di * dy_factor) + (dj * dx_factor) + micro_rough

    return grid


if __name__ == "__main__":
    print("Testing v2 Feature Derivations:")
    sample_grid = generate_local_elevation_kernel(center_elevation=2500.0, base_slope_deg=14.5, roughness=12.0)
    mean_s, max_s = compute_slope_from_grid(sample_grid)
    tri = compute_terrain_roughness_index(sample_grid)
    remoteness = compute_composite_remoteness(distance_to_settlement_km=84.5, distance_to_road_km=18.2, population_density_within_10km=0.0)
    utm = get_utm_epsg(-24.6272, -69.2514)

    print(f"  Local UTM CRS: {utm}")
    print(f"  Mean Slope: {mean_s} deg, Max Slope: {max_s} deg")
    print(f"  Terrain Roughness Index (TRI): {tri} m")
    print(f"  Composite Remoteness Index: {remoteness} (scale 0-1)")
