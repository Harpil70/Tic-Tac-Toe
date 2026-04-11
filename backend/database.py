"""
PostGIS Database Integration for Spatial Queries.

Provides PostgreSQL/PostGIS-backed spatial storage and querying using
ST_DWithin, ST_Distance, ST_Centroid, and spatial indexing (GIST).

Falls back gracefully to in-memory Python when PostGIS is unavailable.
"""
import json
import os
from typing import Dict, List, Any, Optional

from config import DATABASE_URL

# Track PostGIS availability
_postgis_available = False
_engine = None
_SessionLocal = None


def _init_postgis():
    """Attempt to connect to PostGIS database and create tables."""
    global _postgis_available, _engine, _SessionLocal

    if not DATABASE_URL:
        print("DATABASE_URL not configured — using in-memory spatial queries")
        return False

    try:
        from sqlalchemy import (
            create_engine, Column, Integer, String, Float, Text,
            MetaData, Table, text, inspect,
        )
        from sqlalchemy.orm import sessionmaker
        from geoalchemy2 import Geometry

        _engine = create_engine(DATABASE_URL, pool_size=5, max_overflow=10)
        _SessionLocal = sessionmaker(bind=_engine)

        # Test connection
        with _engine.connect() as conn:
            result = conn.execute(text("SELECT PostGIS_Version()"))
            version = result.scalar()
            print(f"PostGIS connected — version {version}")

        # Create tables if they don't exist
        _create_tables()

        _postgis_available = True
        return True

    except Exception as e:
        print(f"PostGIS unavailable ({e}) — using in-memory spatial queries")
        _postgis_available = False
        return False


def _create_tables():
    """Create spatial tables for each geospatial layer with GIST indexes."""
    from sqlalchemy import text

    with _engine.connect() as conn:
        # Enable PostGIS extension
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        conn.commit()

        # Single unified spatial features table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS spatial_features (
                id SERIAL PRIMARY KEY,
                layer_name VARCHAR(64) NOT NULL,
                feature_id INTEGER,
                properties JSONB NOT NULL DEFAULT '{}',
                geom GEOMETRY(Geometry, 4326),
                centroid GEOMETRY(Point, 4326)
            )
        """))
        conn.commit()

        # Create spatial GIST indexes for fast ST_DWithin queries
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_spatial_features_geom
            ON spatial_features USING GIST (geom)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_spatial_features_centroid
            ON spatial_features USING GIST (centroid)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_spatial_features_layer
            ON spatial_features (layer_name)
        """))
        conn.commit()

        print("PostGIS spatial tables and GIST indexes created")


def load_layer_to_postgis(layer_name: str, geojson: Dict[str, Any]) -> int:
    """
    Load a GeoJSON FeatureCollection into the PostGIS spatial_features table.
    Returns the number of features inserted.
    """
    if not _postgis_available or not _engine:
        return 0

    from sqlalchemy import text

    features = geojson.get("features", [])
    if not features:
        return 0

    with _engine.connect() as conn:
        # Clear existing data for this layer
        conn.execute(
            text("DELETE FROM spatial_features WHERE layer_name = :layer"),
            {"layer": layer_name}
        )

        # Batch insert features
        count = 0
        for feat in features:
            geom = feat.get("geometry")
            props = feat.get("properties", {})
            fid = feat.get("id", count)

            if not geom:
                continue

            geom_json = json.dumps(geom)

            conn.execute(text("""
                INSERT INTO spatial_features (layer_name, feature_id, properties, geom, centroid)
                VALUES (
                    :layer,
                    :fid,
                    :props,
                    ST_SetSRID(ST_GeomFromGeoJSON(:geom), 4326),
                    ST_Centroid(ST_SetSRID(ST_GeomFromGeoJSON(:geom), 4326))
                )
            """), {
                "layer": layer_name,
                "fid": fid,
                "props": json.dumps(props),
                "geom": geom_json,
            })
            count += 1

        conn.commit()

    print(f"PostGIS: loaded {count} features into layer '{layer_name}'")
    return count


def postgis_features_in_radius(layer_name: str, lat: float, lng: float,
                                radius_km: float) -> List[Dict]:
    """
    Query PostGIS for features within radius_km of a point using ST_DWithin.
    Uses the GIST spatial index for efficient querying.
    Returns features in the same format as the in-memory version.
    """
    if not _postgis_available or not _engine:
        return None  # Signal caller to use fallback

    from sqlalchemy import text

    # Convert radius from km to meters for ST_DWithin with geography cast
    radius_m = radius_km * 1000

    with _engine.connect() as conn:
        # ST_DWithin with geography cast uses meters and accounts for Earth's curvature
        # ST_Distance with geography gives distance in meters
        result = conn.execute(text("""
            SELECT
                feature_id,
                properties,
                ST_AsGeoJSON(geom) AS geom_json,
                ST_Distance(
                    centroid::geography,
                    ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography
                ) / 1000.0 AS distance_km
            FROM spatial_features
            WHERE layer_name = :layer
              AND ST_DWithin(
                  centroid::geography,
                  ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography,
                  :radius_m
              )
            ORDER BY distance_km ASC
        """), {
            "layer": layer_name,
            "lat": lat,
            "lng": lng,
            "radius_m": radius_m,
        })

        features = []
        for row in result:
            feature = {
                "type": "Feature",
                "id": row.feature_id,
                "properties": json.loads(row.properties) if isinstance(row.properties, str) else row.properties,
                "geometry": json.loads(row.geom_json),
                "distance_km": round(row.distance_km, 3),
            }
            features.append(feature)

    return features


def postgis_layer_count(layer_name: str) -> int:
    """Get feature count for a layer from PostGIS."""
    if not _postgis_available or not _engine:
        return 0

    from sqlalchemy import text

    with _engine.connect() as conn:
        result = conn.execute(
            text("SELECT COUNT(*) FROM spatial_features WHERE layer_name = :layer"),
            {"layer": layer_name}
        )
        return result.scalar() or 0


def postgis_layer_bounds(layer_name: str) -> Optional[Dict]:
    """Get the bounding box of all features in a layer using ST_Extent."""
    if not _postgis_available or not _engine:
        return None

    from sqlalchemy import text

    with _engine.connect() as conn:
        result = conn.execute(text("""
            SELECT
                ST_XMin(ST_Extent(geom)) AS min_lng,
                ST_YMin(ST_Extent(geom)) AS min_lat,
                ST_XMax(ST_Extent(geom)) AS max_lng,
                ST_YMax(ST_Extent(geom)) AS max_lat
            FROM spatial_features
            WHERE layer_name = :layer
        """), {"layer": layer_name})
        row = result.fetchone()
        if row and row.min_lng is not None:
            return {
                "min_lat": round(row.min_lat, 4),
                "max_lat": round(row.max_lat, 4),
                "min_lng": round(row.min_lng, 4),
                "max_lng": round(row.max_lng, 4),
            }
    return None


def is_postgis_available() -> bool:
    """Check if PostGIS is connected and available."""
    return _postgis_available


def init_database():
    """Initialize PostGIS connection (called on app startup)."""
    return _init_postgis()
