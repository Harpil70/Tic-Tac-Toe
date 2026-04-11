"""
File upload and format conversion service.
Supports: GeoJSON, Shapefile (zipped), GeoTIFF, WKT.
Converts all formats to GeoJSON FeatureCollections for internal use.
"""
import io
import json
import os
import tempfile
import zipfile
from typing import Dict, Any, Optional, Tuple

import geopandas as gpd
import numpy as np
from shapely import wkt as shapely_wkt
from shapely.geometry import mapping, shape, Point, Polygon, MultiPolygon

from config import DATA_DIR


def convert_shapefile(file_bytes: bytes, filename: str) -> Tuple[Dict[str, Any], str]:
    """
    Convert a zipped Shapefile (.zip containing .shp, .dbf, .shx, .prj)
    to a GeoJSON FeatureCollection.
    """
    # Write to a temp zip file and extract
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "upload.zip")
        with open(zip_path, "wb") as f:
            f.write(file_bytes)

        # Extract the zip
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmpdir)

        # Find the .shp file inside the extracted contents
        shp_file = None
        for root, dirs, files in os.walk(tmpdir):
            for fname in files:
                if fname.lower().endswith(".shp"):
                    shp_file = os.path.join(root, fname)
                    break

        if not shp_file:
            raise ValueError("No .shp file found in the uploaded ZIP archive")

        # Read with GeoPandas
        gdf = gpd.read_file(shp_file)

        # Reproject to WGS84 if needed
        if gdf.crs and gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs(epsg=4326)

        # Convert to GeoJSON dict
        geojson = json.loads(gdf.to_json())

        # Assign feature IDs
        for i, feature in enumerate(geojson["features"]):
            feature["id"] = i
            if "properties" not in feature:
                feature["properties"] = {}
            feature["properties"]["id"] = i

        layer_name = os.path.splitext(filename)[0].lower().replace(" ", "_").replace("-", "_")
        return geojson, layer_name


def convert_geotiff(file_bytes: bytes, filename: str) -> Tuple[Dict[str, Any], str]:
    """
    Convert a GeoTIFF raster to a GeoJSON FeatureCollection of point samples.
    Each point represents a raster cell with its value as a property.
    """
    try:
        import rasterio
        from rasterio.transform import xy
    except ImportError:
        raise ImportError(
            "rasterio is required for GeoTIFF support. "
            "Install with: pip install rasterio"
        )

    with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        with rasterio.open(tmp_path) as src:
            band = src.read(1)
            transform = src.transform
            nodata = src.nodata
            crs = src.crs

            # Sample the raster at regular intervals for manageable size
            rows, cols = band.shape
            max_samples = 2000  # Limit total features
            step = max(1, int(np.sqrt(rows * cols / max_samples)))

            features = []
            fid = 0

            for r in range(0, rows, step):
                for c in range(0, cols, step):
                    value = float(band[r, c])

                    # Skip nodata
                    if nodata is not None and value == nodata:
                        continue
                    if np.isnan(value):
                        continue

                    # Get the geographic coordinates of this cell
                    x, y = xy(transform, r, c)

                    # If not in WGS84, transform the coordinates
                    if crs and not crs.to_epsg() == 4326:
                        from pyproj import Transformer
                        transformer = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
                        x, y = transformer.transform(x, y)

                    features.append({
                        "type": "Feature",
                        "id": fid,
                        "properties": {
                            "id": fid,
                            "value": round(value, 4),
                            "row": r,
                            "col": c,
                        },
                        "geometry": {
                            "type": "Point",
                            "coordinates": [round(x, 6), round(y, 6)],
                        },
                    })
                    fid += 1

        geojson = {"type": "FeatureCollection", "features": features}
        layer_name = os.path.splitext(filename)[0].lower().replace(" ", "_").replace("-", "_")
        return geojson, layer_name

    finally:
        os.unlink(tmp_path)


def convert_wkt(file_bytes: bytes, filename: str) -> Tuple[Dict[str, Any], str]:
    """
    Convert WKT (Well-Known Text) geometries to a GeoJSON FeatureCollection.
    Supports a file with one WKT geometry per line, or a single WKT string.
    """
    text = file_bytes.decode("utf-8", errors="replace").strip()
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    features = []
    fid = 0

    for line in lines:
        # Skip comment lines
        if line.startswith("#") or line.startswith("//"):
            continue

        # Try to parse each non-empty line as WKT
        try:
            geom = shapely_wkt.loads(line)
            features.append({
                "type": "Feature",
                "id": fid,
                "properties": {
                    "id": fid,
                    "name": f"Feature_{fid + 1}",
                    "wkt_type": geom.geom_type,
                },
                "geometry": mapping(geom),
            })
            fid += 1
        except Exception:
            # Maybe the entire file is a single multi-line WKT
            continue

    # If no individual lines parsed, try the entire text as one WKT
    if not features:
        try:
            geom = shapely_wkt.loads(text)
            features.append({
                "type": "Feature",
                "id": 0,
                "properties": {
                    "id": 0,
                    "name": "Feature_1",
                    "wkt_type": geom.geom_type,
                },
                "geometry": mapping(geom),
            })
        except Exception as e:
            raise ValueError(f"Could not parse WKT content: {e}")

    if not features:
        raise ValueError("No valid WKT geometries found in the uploaded file")

    geojson = {"type": "FeatureCollection", "features": features}
    layer_name = os.path.splitext(filename)[0].lower().replace(" ", "_").replace("-", "_")
    return geojson, layer_name


def convert_geojson(file_bytes: bytes, filename: str) -> Tuple[Dict[str, Any], str]:
    """Validate and normalize an uploaded GeoJSON file."""
    try:
        geojson = json.loads(file_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ValueError(f"Invalid GeoJSON file: {e}")

    # Handle a bare Geometry or Feature by wrapping in a FeatureCollection
    if geojson.get("type") == "Feature":
        geojson = {"type": "FeatureCollection", "features": [geojson]}
    elif geojson.get("type") != "FeatureCollection":
        # It might be a raw Geometry object
        geojson = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "id": 0,
                "properties": {"id": 0},
                "geometry": geojson,
            }],
        }

    # Ensure feature IDs
    for i, feat in enumerate(geojson.get("features", [])):
        feat["id"] = i
        if "properties" not in feat:
            feat["properties"] = {}
        feat["properties"]["id"] = i

    layer_name = os.path.splitext(filename)[0].lower().replace(" ", "_").replace("-", "_")
    return geojson, layer_name


def process_upload(file_bytes: bytes, filename: str, layer_name: Optional[str] = None) -> Tuple[Dict[str, Any], str]:
    """
    Main entry point: detect format by extension and convert to GeoJSON.
    Returns (geojson_dict, layer_name).
    """
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".zip":
        geojson, auto_name = convert_shapefile(file_bytes, filename)
    elif ext in (".tif", ".tiff"):
        geojson, auto_name = convert_geotiff(file_bytes, filename)
    elif ext in (".wkt", ".txt"):
        geojson, auto_name = convert_wkt(file_bytes, filename)
    elif ext in (".geojson", ".json"):
        geojson, auto_name = convert_geojson(file_bytes, filename)
    elif ext == ".shp":
        raise ValueError(
            "Please upload Shapefiles as a ZIP archive containing "
            "the .shp, .dbf, .shx, and .prj files together."
        )
    else:
        raise ValueError(
            f"Unsupported file format: '{ext}'. "
            f"Supported formats: .geojson, .json, .zip (Shapefile), .tif/.tiff (GeoTIFF), .wkt"
        )

    final_name = layer_name or auto_name
    return geojson, final_name


def save_uploaded_layer(geojson: Dict[str, Any], layer_name: str) -> str:
    """Save a converted GeoJSON to the data directory for persistence."""
    filepath = os.path.join(DATA_DIR, f"{layer_name}.geojson")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(geojson, f, indent=2)
    return filepath
