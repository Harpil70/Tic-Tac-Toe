"""Route and accessibility analysis using OSRM."""
import requests
import math
from typing import Dict, List, Any, Optional

from config import OSRM_BASE_URL
from services.data_ingestion import get_features_in_radius


def compute_isochrone(lat: float, lng: float,
                      mode: str = "driving",
                      intervals: List[int] = None) -> Dict[str, Any]:
    """
    Compute drive-time, walk-time, or transit isochrones from a point.
    Attempts to use OSRM routing API for realistic road-network isochrones;
    falls back to approximate polygon generation if OSRM is unavailable.
    """
    if intervals is None:
        intervals = [10, 20, 30]

    isochrones = []

    for minutes in sorted(intervals):
        # Speed estimates by mode
        if mode == "driving":
            speed_kmh = 40  # Average urban driving speed in Gujarat
        elif mode == "transit":
            speed_kmh = 25  # Approx. bus/auto-rickshaw speed in Gujarat metro areas
        else:
            speed_kmh = 5   # Walking speed

        radius_km = speed_kmh * minutes / 60

        # Try OSRM-based isochrone first (for driving/walking)
        polygon = None
        if mode in ("driving", "walking"):
            polygon = _osrm_isochrone(lat, lng, radius_km, mode, num_points=24)

        # Fallback to approximate polygon
        if polygon is None:
            polygon = _generate_isochrone_polygon(lat, lng, radius_km, num_points=32)

        # Compute catchment area stats
        catchment = _compute_catchment(lat, lng, radius_km)

        isochrones.append({
            "minutes": minutes,
            "mode": mode,
            "radius_km": round(radius_km, 2),
            "polygon": polygon,
            "catchment": catchment,
        })

    return {
        "center": {"lat": lat, "lng": lng},
        "mode": mode,
        "isochrones": isochrones,
    }


def _osrm_isochrone(lat: float, lng: float, radius_km: float,
                    mode: str = "driving", num_points: int = 24) -> Optional[Dict]:
    """
    Build an isochrone by querying OSRM route durations to sample points
    around the origin. Uses the OSRM table service to get travel times
    to radial probe points, then adjusts radii based on actual driving time.
    """
    try:
        profile = "driving" if mode == "driving" else "foot"

        # Generate probe points at the estimated radius
        lat_deg_per_km = 1.0 / 111.32
        lng_deg_per_km = 1.0 / (111.32 * math.cos(math.radians(lat)))

        probe_coords = []
        for i in range(num_points):
            angle = 2 * math.pi * i / num_points
            dlat = radius_km * math.sin(angle) * lat_deg_per_km
            dlng = radius_km * math.cos(angle) * lng_deg_per_km
            probe_coords.append((round(lng + dlng, 6), round(lat + dlat, 6)))

        # Build OSRM table request: origin is index 0, probes are 1..N
        coords_str = f"{lng},{lat}"
        for plng, plat in probe_coords:
            coords_str += f";{plng},{plat}"

        url = (
            f"{OSRM_BASE_URL}/table/v1/{profile}/{coords_str}"
            f"?sources=0&annotations=duration"
        )

        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return None

        data = response.json()
        if data.get("code") != "Ok":
            return None

        durations = data["durations"][0]  # durations from source (index 0)

        # Build polygon using actual travel-time scaling
        # target_seconds is the time budget for this radius
        target_seconds = (radius_km / (40 if mode == "driving" else 5)) * 3600
        coordinates = []

        for i in range(num_points):
            dur = durations[i + 1]  # skip index 0 (self)
            if dur is None or dur == 0:
                scale = 1.0
            else:
                scale = min(1.5, max(0.3, target_seconds / dur))

            angle = 2 * math.pi * i / num_points
            r = radius_km * scale
            dlng = r * math.cos(angle) * lng_deg_per_km
            dlat = r * math.sin(angle) * lat_deg_per_km
            coordinates.append([
                round(lng + dlng, 6),
                round(lat + dlat, 6),
            ])

        coordinates.append(coordinates[0])  # close ring
        return {"type": "Polygon", "coordinates": [coordinates]}

    except Exception as e:
        print(f"OSRM isochrone failed (falling back to approximation): {e}")
        return None


def _generate_isochrone_polygon(lat: float, lng: float,
                                 radius_km: float,
                                 num_points: int = 32) -> Dict:
    """Generate an approximate isochrone polygon with realistic road-adjusted shape."""
    import random
    random.seed(int(lat * 1000 + lng * 1000))

    coordinates = []
    lat_deg_per_km = 1.0 / 111.32
    lng_deg_per_km = 1.0 / (111.32 * math.cos(math.radians(lat)))

    for i in range(num_points):
        angle = 2 * math.pi * i / num_points

        # Add variation to simulate road network (not a perfect circle)
        variation = 0.7 + random.random() * 0.6  # 70% to 130% of radius
        r = radius_km * variation

        dx = r * math.cos(angle) * lng_deg_per_km
        dy = r * math.sin(angle) * lat_deg_per_km

        coordinates.append([
            round(lng + dx, 6),
            round(lat + dy, 6)
        ])

    coordinates.append(coordinates[0])  # Close polygon

    return {
        "type": "Polygon",
        "coordinates": [coordinates]
    }


def _compute_catchment(lat: float, lng: float, radius_km: float) -> Dict[str, Any]:
    """Estimate population and POI within catchment area."""
    # Get demographics within radius
    demo_features = get_features_in_radius("demographics", lat, lng, radius_km)
    total_pop = sum(f["properties"].get("population", 0) for f in demo_features)
    avg_income = 0
    if demo_features:
        incomes = [f["properties"].get("median_income", 0) for f in demo_features]
        avg_income = sum(incomes) / len(incomes)

    # Get POIs
    poi_features = get_features_in_radius("poi", lat, lng, radius_km)
    competitors = len([f for f in poi_features if f["properties"].get("category") == "competitor"])
    anchors = len([f for f in poi_features if f["properties"].get("category") == "anchor"])

    # Get transit
    transport_features = get_features_in_radius("transportation", lat, lng, radius_km)
    transit_stops = len([f for f in transport_features if f["properties"].get("type") == "transit_stop"])

    return {
        "population": total_pop,
        "households": int(total_pop / 4.5),
        "avg_income": round(avg_income, 0),
        "competitors": competitors,
        "anchors": anchors,
        "transit_stops": transit_stops,
        "area_sqkm": round(math.pi * radius_km ** 2, 1),
    }


def get_route_info(origin_lat: float, origin_lng: float,
                   dest_lat: float, dest_lng: float,
                   mode: str = "driving") -> Dict[str, Any]:
    """Get route info between two points using OSRM."""
    try:
        profile = "driving" if mode == "driving" else "foot"
        url = (
            f"{OSRM_BASE_URL}/route/v1/{profile}/"
            f"{origin_lng},{origin_lat};{dest_lng},{dest_lat}"
            f"?overview=full&geometries=geojson"
        )

        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("routes"):
                route = data["routes"][0]
                return {
                    "distance_km": round(route["distance"] / 1000, 2),
                    "duration_minutes": round(route["duration"] / 60, 1),
                    "geometry": route["geometry"],
                }
    except Exception as e:
        print(f"OSRM request failed: {e}")

    # Fallback: straight-line estimate
    from utils.spatial import haversine_distance
    dist = haversine_distance(origin_lat, origin_lng, dest_lat, dest_lng)
    speed = 40 if mode == "driving" else 5
    return {
        "distance_km": round(dist * 1.3, 2),  # road factor
        "duration_minutes": round(dist * 1.3 / speed * 60, 1),
        "geometry": None,
    }
