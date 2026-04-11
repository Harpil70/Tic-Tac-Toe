"""Application configuration for GeoSpatial Site Readiness Analyzer."""
import os

# Data directory
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# PostGIS database URL (set to "" to disable PostGIS and use in-memory only)
# Override via environment variable: export DATABASE_URL="postgresql://user:pass@host:5432/dbname"
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/geospatial"
)

# H3 resolution for hexagonal binning
H3_RESOLUTION = 7  # ~5.16 km² per hexagon

# OSRM public demo server
OSRM_BASE_URL = "https://router.project-osrm.org"

# Default scoring weights (sum to 1.0)
DEFAULT_WEIGHTS = {
    "demographics": 0.25,
    "transportation": 0.20,
    "poi": 0.20,
    "landuse": 0.15,
    "environmental": 0.20,
}

# Use-case presets
WEIGHT_PRESETS = {
    "retail_store": {
        "demographics": 0.30,
        "transportation": 0.20,
        "poi": 0.25,
        "landuse": 0.10,
        "environmental": 0.15,
    },
    "ev_charging": {
        "demographics": 0.15,
        "transportation": 0.35,
        "poi": 0.15,
        "landuse": 0.15,
        "environmental": 0.20,
    },
    "warehouse": {
        "demographics": 0.10,
        "transportation": 0.30,
        "poi": 0.10,
        "landuse": 0.30,
        "environmental": 0.20,
    },
    "telecom_tower": {
        "demographics": 0.30,
        "transportation": 0.10,
        "poi": 0.10,
        "landuse": 0.20,
        "environmental": 0.30,
    },
    "solar_farm": {
        "demographics": 0.05,
        "transportation": 0.15,
        "poi": 0.05,
        "landuse": 0.30,
        "environmental": 0.45,
    },
}

# Distance decay parameters
DISTANCE_DECAY_RATE = 0.5  # km^-1, exponential decay rate

# Scoring thresholds
SCORE_THRESHOLDS = {
    "min_population_5km": 5000,
    "min_road_density_km": 2.0,
    "max_flood_risk": 0.7,
    "max_earthquake_risk": 0.8,
}

# Gujarat bounding box (approximate)
GUJARAT_BOUNDS = {
    "min_lat": 20.1,
    "max_lat": 24.7,
    "min_lng": 68.1,
    "max_lng": 74.5,
}

# Major cities in Gujarat (lat, lng)
GUJARAT_CITIES = {
    "Ahmedabad": (23.0225, 72.5714),
    "Surat": (21.1702, 72.8311),
    "Vadodara": (22.3072, 73.1812),
    "Rajkot": (22.3039, 70.8022),
    "Gandhinagar": (23.2156, 72.6369),
    "Bhavnagar": (21.7645, 72.1519),
    "Jamnagar": (22.4707, 70.0577),
    "Junagadh": (21.5222, 70.4579),
    "Anand": (22.5645, 72.9289),
    "Navsari": (20.9467, 72.9520),
    "Morbi": (22.8173, 70.8370),
    "Mehsana": (23.5880, 72.3693),
    "Bharuch": (21.7051, 72.9959),
    "Vapi": (20.3893, 72.9106),
    "Gandhidham": (23.0753, 70.1337),
}

# Server config
HOST = "0.0.0.0"
PORT = 8000
