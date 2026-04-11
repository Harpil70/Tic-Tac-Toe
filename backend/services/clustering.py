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
        # Seed based on bounds for consistency within the same view
        seed_val = int((bounds["min_lat"] + bounds["max_lat"]) * 1000
                       + (bounds["min_lng"] + bounds["max_lng"]) * 100)
        random.seed(seed_val)
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

    # Separate hot and cold points for clustering
    hot_points = [p for p in points if p["score"] >= p75]
    cold_points = [p for p in points if p["score"] <= p25]

    hot_clusters = _sklearn_dbscan(hot_points, eps_km, min_samples)
    cold_clusters = _sklearn_dbscan(cold_points, eps_km, min_samples)

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

    # Getis-Ord Gi* Statistic
    gi_star_results = compute_getis_ord_gi(points, eps_km)

    return {
        "hot_spots": hot_spots,
        "cold_spots": cold_spots,
        "getis_ord_gi": gi_star_results,
        "total_hexagons": len(points),
        "stats": stats,
    }


def compute_getis_ord_gi(points: List[Dict], eps_km: float) -> List[Dict]:
    """Calculate Getis-Ord Gi* z-score for each point to find statistically significant clusters."""
    import math
    from utils.spatial import haversine_distance

    n = len(points)
    if n <= 1:
        return []

    # Calculate global mean and variance
    scores = [p["score"] for p in points]
    mean_score = sum(scores) / n
    variance = sum((x - mean_score) ** 2 for x in scores) / n
    std_dev = math.sqrt(variance) if variance > 0 else 0

    if std_dev == 0:
        return []

    results = []
    
    for i in range(n):
        point_i = points[i]
        
        # Spatial weights: 1 if neighbor (including self within eps_km), else 0
        w_sum = 0
        wx_sum = 0
        w_sq_sum = 0
        
        for j in range(n):
            dist = haversine_distance(
                point_i["lat"], point_i["lng"],
                points[j]["lat"], points[j]["lng"]
            )
            # Binary distance weight
            if dist <= eps_km:
                w_ij = 1
                w_sum += w_ij
                wx_sum += w_ij * points[j]["score"]
                w_sq_sum += w_ij ** 2

        if w_sum > 0:
            # Getis-Ord Gi* formula
            numerator = wx_sum - (mean_score * w_sum)
            denominator = std_dev * math.sqrt((n * w_sq_sum - w_sum**2) / (n - 1)) if n > 1 else 1
            
            z_score = numerator / denominator if denominator > 0 else 0
            
            # Classification
            if z_score > 2.58:
                significance = "hot_99"
            elif z_score > 1.96:
                significance = "hot_95"
            elif z_score > 1.65:
                significance = "hot_90"
            elif z_score < -2.58:
                significance = "cold_99"
            elif z_score < -1.96:
                significance = "cold_95"
            elif z_score < -1.65:
                significance = "cold_90"
            else:
                significance = "not_significant"

            results.append({
                "hex_id": point_i["hex_id"],
                "lat": point_i["lat"],
                "lng": point_i["lng"],
                "z_score": round(z_score, 3),
                "significance": significance
            })

    return results


def _sklearn_dbscan(points: List[Dict], eps_km: float, min_samples: int) -> List[List[Dict]]:
    """
    DBSCAN spatial clustering using scikit-learn with haversine metric.
    eps_km is converted to radians for the haversine distance metric.
    """
    import numpy as np
    from sklearn.cluster import DBSCAN

    n = len(points)
    if n == 0:
        return []

    # Prepare coordinates in radians for haversine metric
    coords_rad = np.radians([[p["lat"], p["lng"]] for p in points])

    # Convert eps from km to radians (Earth radius ≈ 6371 km)
    eps_rad = eps_km / 6371.0

    # Run scikit-learn DBSCAN with haversine metric
    db = DBSCAN(
        eps=eps_rad,
        min_samples=min_samples,
        metric="haversine",
        algorithm="ball_tree",
    )
    labels = db.fit_predict(coords_rad)

    # Group points by cluster label (label -1 = noise)
    cluster_map: Dict[int, List[Dict]] = {}
    for i, label in enumerate(labels):
        if label == -1:
            continue
        if label not in cluster_map:
            cluster_map[label] = []
        cluster_map[label].append(points[i])

    return list(cluster_map.values())

