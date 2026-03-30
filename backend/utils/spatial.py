"""Spatial utility functions."""
import math
from typing import List, Tuple


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in km between two points using Haversine formula."""
    R = 6371.0  # Earth's radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def exponential_decay(distance_km: float, decay_rate: float = 0.5) -> float:
    """Exponential distance decay: closer = higher score (0-1)."""
    return math.exp(-decay_rate * distance_km)


def linear_decay(distance_km: float, max_distance_km: float) -> float:
    """Linear distance decay: 1 at 0km, 0 at max_distance."""
    if distance_km >= max_distance_km:
        return 0.0
    return 1.0 - (distance_km / max_distance_km)


def gaussian_decay(distance_km: float, sigma_km: float = 5.0) -> float:
    """Gaussian distance decay."""
    return math.exp(-(distance_km ** 2) / (2 * sigma_km ** 2))


def normalize_score(value: float, min_val: float = 0.0, max_val: float = 100.0) -> float:
    """Normalize a value to 0-100 range."""
    if max_val == min_val:
        return 50.0
    normalized = (value - min_val) / (max_val - min_val) * 100.0
    return max(0.0, min(100.0, normalized))


def competitive_density_score(competitor_count: int, optimal_min: int = 2, optimal_max: int = 8) -> float:
    """
    Score based on competitor density.
    Too few = no market validation, too many = saturated.
    Returns 0-100.
    """
    if competitor_count == 0:
        return 20.0  # No competitors = uncertain market
    elif competitor_count < optimal_min:
        return 40.0 + (competitor_count / optimal_min) * 30.0
    elif competitor_count <= optimal_max:
        # Optimal range
        mid = (optimal_min + optimal_max) / 2
        distance_from_mid = abs(competitor_count - mid) / (optimal_max - optimal_min) * 2
        return 100.0 - distance_from_mid * 20.0
    else:
        # Over-saturated
        over = competitor_count - optimal_max
        return max(10.0, 60.0 - over * 10.0)


def point_in_polygon_approx(lat: float, lng: float, polygon_coords: List[List[float]]) -> bool:
    """Ray-casting algorithm for point-in-polygon test."""
    n = len(polygon_coords)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = polygon_coords[i]
        xj, yj = polygon_coords[j]
        if ((yi > lat) != (yj > lat)) and (lng < (xj - xi) * (lat - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def get_grade(score: float) -> str:
    """Convert numeric score to letter grade."""
    if score >= 90:
        return "A+"
    elif score >= 80:
        return "A"
    elif score >= 70:
        return "B+"
    elif score >= 60:
        return "B"
    elif score >= 50:
        return "C+"
    elif score >= 40:
        return "C"
    elif score >= 30:
        return "D"
    else:
        return "F"


def km_to_degrees(km: float, at_latitude: float = 22.5) -> float:
    """Approximate conversion from km to degrees at a given latitude."""
    lat_deg = km / 111.32
    lng_deg = km / (111.32 * math.cos(math.radians(at_latitude)))
    return (lat_deg + lng_deg) / 2  # average


def degrees_to_km(degrees: float, at_latitude: float = 22.5) -> float:
    """Approximate conversion from degrees to km at a given latitude."""
    return degrees * 111.32 * math.cos(math.radians(at_latitude / 2))
