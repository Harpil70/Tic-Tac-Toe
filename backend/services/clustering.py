"""Spatial clustering and hot-spot detection using DBSCAN and H3 hexagonal binning."""
import math
from typing import Dict, List, Any, Optional

try:
    import h3
except ImportError:
    h3 = None

from config import H3_RESOLUTION, GUJARAT_BOUNDS
from services.scoring import compute_site_score, get_weights


def get_h3_hexagons(bounds: Optional[Dict[str, float]] = None,
                    resolution: int = H3_RESOLUTION) -> List[str]:
    """Generate H3 hexagon IDs covering the given bounds."""
    if h3 is None:
        return _generate_fallback_grid(bounds, resolution)

    if bounds is None:
        bounds = GUJARAT_BOUNDS

    hexagons = set()

    # Sample points across the bounds to find all hexagons
    lat_step = 0.1 if resolution <= 5 else 0.05 if resolution <= 7 else 0.02
    lng_step = lat_step

    lat = bounds["min_lat"]
    while lat <= bounds["max_lat"]:
        lng = bounds["min_lng"]
        while lng <= bounds["max_lng"]:
            hex_id = h3.latlng_to_cell(lat, lng, resolution)
            hexagons.add(hex_id)
            lng += lng_step
        lat += lat_step

    return list(hexagons)


def _generate_fallback_grid(bounds, resolution):
    """Fallback grid generation when H3 is not available."""
    if bounds is None:
        bounds = GUJARAT_BOUNDS

    # Generate a simple grid of points representing hex centers
    step = 0.15 if resolution <= 5 else 0.08 if resolution <= 7 else 0.04
    points = []
    lat = bounds["min_lat"]
    while lat <= bounds["max_lat"]:
        lng = bounds["min_lng"]
        row = 0
        while lng <= bounds["max_lng"]:
            # Offset every other row for hex-like pattern
            offset = step * 0.5 if int((lat - bounds["min_lat"]) / step) % 2 else 0
            points.append(f"{round(lat, 4)}_{round(lng + offset, 4)}")
            lng += step
        lat += step * 0.866  # sqrt(3)/2 for hex spacing

    return points


def hex_to_coords(hex_id: str, resolution: int = H3_RESOLUTION):
    """Convert H3 hex ID to center coordinates and boundary."""
    if h3 is not None and not "_" in hex_id:
        lat, lng = h3.cell_to_latlng(hex_id)
        boundary = h3.cell_to_boundary(hex_id)
        # Convert boundary to GeoJSON format [lng, lat]
        boundary = [[round(lng_b, 6), round(lat_b, 6)] for lat_b, lng_b in boundary]
        boundary.append(boundary[0])  # close the ring
        return lat, lng, boundary
    else:
        # Fallback: parse from our format
        parts = hex_id.split("_")
        lat, lng = float(parts[0]), float(parts[1])
        # Create hexagonal boundary
        size = 0.04 if resolution <= 5 else 0.02 if resolution <= 7 else 0.01
        boundary = []
        for i in range(6):
            angle = math.pi / 3 * i + math.pi / 6
            bx = lng + size * math.cos(angle)
            by = lat + size * math.sin(angle)
            boundary.append([round(bx, 6), round(by, 6)])
        boundary.append(boundary[0])
        return lat, lng, boundary


def compute_heatmap(bounds: Optional[Dict[str, float]] = None,
                    resolution: int = H3_RESOLUTION,
                    weights: Optional[Dict[str, float]] = None,
                    preset: Optional[str] = None,
                    max_hexagons: int = 500) -> Dict[str, Any]:
    """Compute H3 heatmap of site scores across the region."""
    if bounds is None:
        # Use focused bounds around major Gujarat cities for performance
        bounds = {
            "min_lat": 21.0,
            "max_lat": 23.5,
            "min_lng": 70.5,
            "max_lng": 73.5,
        }

    hexagons = get_h3_hexagons(bounds, resolution)

    # Limit hexagons for performance
    if len(hexagons) > max_hexagons:
        import random
        random.seed(42)
        hexagons = random.sample(hexagons, max_hexagons)

    features = []
    scores = []

    for hex_id in hexagons:
        lat, lng, boundary = hex_to_coords(hex_id, resolution)

        # Quick score computation
        result = compute_site_score(lat, lng, weights, preset, radius_km=5.0)
        score = result["composite_score"]
        scores.append(score)

        feature = {
            "type": "Feature",
            "properties": {
                "hex_id": hex_id,
                "score": score,
                "grade": result["grade"],
                "lat": lat,
                "lng": lng,
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [boundary],
            },
        }
        features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "features": features,
    }

    stats = {}
    if scores:
        scores_sorted = sorted(scores)
        stats = {
            "min": min(scores),
            "max": max(scores),
            "mean": round(sum(scores) / len(scores), 2),
            "median": scores_sorted[len(scores_sorted) // 2],
            "count": len(scores),
            "p25": scores_sorted[int(len(scores_sorted) * 0.25)],
            "p75": scores_sorted[int(len(scores_sorted) * 0.75)],
        }

    return {"geojson": geojson, "stats": stats}


def detect_clusters(heatmap_data: Dict[str, Any],
                    min_samples: int = 3,
                    eps_km: float = 10.0) -> Dict[str, Any]:
    """Run DBSCAN clustering on scored hexagons to find hot/cold spots."""
    features = heatmap_data["geojson"]["features"]
    if not features:
        return {"hot_spots": [], "cold_spots": [], "clusters": []}

    # Extract coordinates and scores
    points = []
    for f in features:
        points.append({
            "lat": f["properties"]["lat"],
            "lng": f["properties"]["lng"],
            "score": f["properties"]["score"],
            "hex_id": f["properties"]["hex_id"],
        })

    stats = heatmap_data.get("stats", {})
    p75 = stats.get("p75", 60)
    p25 = stats.get("p25", 30)

    # Simple distance-based clustering (DBSCAN-like)
    hot_points = [p for p in points if p["score"] >= p75]
    cold_points = [p for p in points if p["score"] <= p25]

    hot_clusters = _simple_dbscan(hot_points, eps_km, min_samples)
    cold_clusters = _simple_dbscan(cold_points, eps_km, min_samples)

    # Format results
    hot_spots = []
    for i, cluster in enumerate(hot_clusters):
        center_lat = sum(p["lat"] for p in cluster) / len(cluster)
        center_lng = sum(p["lng"] for p in cluster) / len(cluster)
        avg_score = sum(p["score"] for p in cluster) / len(cluster)
        hot_spots.append({
            "id": f"hot_{i}",
            "type": "hot_spot",
            "center": {"lat": round(center_lat, 4), "lng": round(center_lng, 4)},
            "avg_score": round(avg_score, 2),
            "hex_count": len(cluster),
            "hexagons": [p["hex_id"] for p in cluster],
        })

    cold_spots = []
    for i, cluster in enumerate(cold_clusters):
        center_lat = sum(p["lat"] for p in cluster) / len(cluster)
        center_lng = sum(p["lng"] for p in cluster) / len(cluster)
        avg_score = sum(p["score"] for p in cluster) / len(cluster)
        cold_spots.append({
            "id": f"cold_{i}",
            "type": "cold_spot",
            "center": {"lat": round(center_lat, 4), "lng": round(center_lng, 4)},
            "avg_score": round(avg_score, 2),
            "hex_count": len(cluster),
            "hexagons": [p["hex_id"] for p in cluster],
        })

    return {
        "hot_spots": hot_spots,
        "cold_spots": cold_spots,
        "total_hexagons": len(points),
        "stats": stats,
    }


def _simple_dbscan(points: List[Dict], eps_km: float, min_samples: int) -> List[List[Dict]]:
    """Simple DBSCAN implementation for spatial clustering."""
    from utils.spatial import haversine_distance

    n = len(points)
    if n == 0:
        return []

    visited = [False] * n
    clusters = []

    for i in range(n):
        if visited[i]:
            continue

        # Find neighbors
        neighbors = []
        for j in range(n):
            if i != j:
                dist = haversine_distance(
                    points[i]["lat"], points[i]["lng"],
                    points[j]["lat"], points[j]["lng"]
                )
                if dist <= eps_km:
                    neighbors.append(j)

        if len(neighbors) >= min_samples - 1:
            # Start new cluster
            cluster = [points[i]]
            visited[i] = True

            # Expand cluster
            queue = list(neighbors)
            while queue:
                j = queue.pop(0)
                if visited[j]:
                    continue
                visited[j] = True
                cluster.append(points[j])

                # Find j's neighbors
                j_neighbors = []
                for k in range(n):
                    if k != j:
                        dist = haversine_distance(
                            points[j]["lat"], points[j]["lng"],
                            points[k]["lat"], points[k]["lng"]
                        )
                        if dist <= eps_km:
                            j_neighbors.append(k)

                if len(j_neighbors) >= min_samples - 1:
                    for nn in j_neighbors:
                        if not visited[nn] and nn not in queue:
                            queue.append(nn)

            clusters.append(cluster)

    return clusters
