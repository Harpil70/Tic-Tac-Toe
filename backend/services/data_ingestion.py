"""
Load and index geospatial data layers.

Uses PostGIS for spatial queries (ST_DWithin, GIST indexes) when available,
with automatic fallback to in-memory Python spatial queries.
"""
import json
import os
from typing import Dict, List, Any, Optional

from config import DATA_DIR

# In-memory data store (always populated for layer serving and fallback)
_layers: Dict[str, Any] = {}


def load_all_layers() -> Dict[str, Any]:
    """Load all GeoJSON data layers from disk and optionally into PostGIS."""
    global _layers

    # Initialize PostGIS connection (graceful — won't fail if unavailable)
    from database import init_database, is_postgis_available, load_layer_to_postgis
    init_database()

    layer_files = {
        "demographics": "demographics.geojson",
        "transportation": "transportation.geojson",
        "poi": "poi.geojson",
        "landuse": "landuse.geojson",
        "environmental": "environmental.geojson",
    }

    for layer_name, filename in layer_files.items():
        filepath = os.path.join(DATA_DIR, filename)
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                _layers[layer_name] = json.load(f)
            feat_count = len(_layers[layer_name]['features'])
            print(f"Loaded {layer_name}: {feat_count} features")

            # Also load into PostGIS if available
            if is_postgis_available():
                load_layer_to_postgis(layer_name, _layers[layer_name])
        else:
            print(f"WARNING: {filepath} not found!")
            _layers[layer_name] = {"type": "FeatureCollection", "features": []}

    if is_postgis_available():
        print("All layers loaded into PostGIS with GIST spatial indexes")
    else:
        print("Using in-memory spatial queries (PostGIS not available)")

    return _layers


def get_layer(layer_name: str) -> Optional[Dict[str, Any]]:
    """Get a specific data layer."""
    return _layers.get(layer_name)


def get_all_layers() -> Dict[str, Any]:
    """Get all loaded data layers."""
    return _layers


def register_layer(layer_name: str, geojson: Dict[str, Any]) -> None:
    """Register a new layer (e.g. from file upload) into the in-memory store and PostGIS."""
    global _layers
    _layers[layer_name] = geojson
    feat_count = len(geojson.get('features', []))
    print(f"Registered uploaded layer '{layer_name}': {feat_count} features")

    # Also load into PostGIS
    from database import is_postgis_available, load_layer_to_postgis
    if is_postgis_available():
        load_layer_to_postgis(layer_name, geojson)


def get_layer_names() -> List[str]:
    """Get list of available layer names."""
    return list(_layers.keys())


def get_layer_summary() -> List[Dict[str, Any]]:
    """Get summary info about each layer."""
    from database import is_postgis_available

    summaries = []
    layer_meta = {
        "demographics": {
            "display_name": "Demographics",
            "description": "Population density, income, age distribution",
            "color": "#4fc3f7",
            "icon": "people",
        },
        "transportation": {
            "display_name": "Transportation",
            "description": "Roads, highways, transit stops",
            "color": "#ff8a65",
            "icon": "directions_car",
        },
        "poi": {
            "display_name": "Points of Interest",
            "description": "Competitors, anchors, complementary businesses",
            "color": "#ba68c8",
            "icon": "store",
        },
        "landuse": {
            "display_name": "Land Use & Zoning",
            "description": "Commercial, residential, industrial zones",
            "color": "#81c784",
            "icon": "map",
        },
        "environmental": {
            "display_name": "Environmental Risk",
            "description": "Flood zones, earthquake risk, air quality",
            "color": "#e57373",
            "icon": "warning",
        },
    }

    for name, layer_data in _layers.items():
        meta = layer_meta.get(name, {})
        summaries.append({
            "name": name,
            "display_name": meta.get("display_name", name.title()),
            "description": meta.get("description", ""),
            "color": meta.get("color", "#888"),
            "icon": meta.get("icon", "layers"),
            "feature_count": len(layer_data.get("features", [])),
            "storage": "postgis" if is_postgis_available() else "in-memory",
        })

    return summaries


def get_features_in_radius(layer_name: str, lat: float, lng: float, radius_km: float) -> List[Dict]:
    """
    Get all features from a layer within a given radius of a point.

    Uses PostGIS ST_DWithin with GIST index when available for efficient
    spatial queries. Falls back to in-memory Python haversine scan otherwise.
    """
    # Try PostGIS first
    from database import postgis_features_in_radius
    postgis_result = postgis_features_in_radius(layer_name, lat, lng, radius_km)
    if postgis_result is not None:
        return postgis_result

    # Fallback: in-memory spatial query
    return _inmemory_features_in_radius(layer_name, lat, lng, radius_km)


def _inmemory_features_in_radius(layer_name: str, lat: float, lng: float, radius_km: float) -> List[Dict]:
    """In-memory fallback: scan all features and compute haversine distance."""
    from utils.spatial import haversine_distance

    layer = get_layer(layer_name)
    if not layer:
        return []

    nearby = []
    for feature in layer["features"]:
        geom = feature["geometry"]
        if geom["type"] == "Point":
            flng, flat = geom["coordinates"]
            dist = haversine_distance(lat, lng, flat, flng)
            if dist <= radius_km:
                feat_copy = {**feature, "distance_km": round(dist, 3)}
                nearby.append(feat_copy)
        elif geom["type"] == "Polygon":
            # Use centroid for distance calc
            coords = geom["coordinates"][0]
            clng = sum(c[0] for c in coords) / len(coords)
            clat = sum(c[1] for c in coords) / len(coords)
            dist = haversine_distance(lat, lng, clat, clng)
            if dist <= radius_km:
                feat_copy = {**feature, "distance_km": round(dist, 3)}
                nearby.append(feat_copy)
        elif geom["type"] == "LineString":
            # Use midpoint for distance
            coords = geom["coordinates"]
            mid_idx = len(coords) // 2
            mlng, mlat = coords[mid_idx]
            dist = haversine_distance(lat, lng, mlat, mlng)
            if dist <= radius_km * 1.5:  # slightly larger buffer for lines
                feat_copy = {**feature, "distance_km": round(dist, 3)}
                nearby.append(feat_copy)

    return nearby
