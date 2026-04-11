"""Site Readiness Scoring Engine."""
from typing import Dict, List, Any, Optional, Tuple
from config import DEFAULT_WEIGHTS, WEIGHT_PRESETS, SCORE_THRESHOLDS, DISTANCE_DECAY_RATE
from services.data_ingestion import get_features_in_radius
from utils.spatial import (
    haversine_distance, exponential_decay, competitive_density_score,
    normalize_score, get_grade
)


def get_weights(custom_weights: Optional[Dict[str, float]] = None,
                preset: Optional[str] = None) -> Dict[str, float]:
    """Get scoring weights from custom, preset, or default."""
    if custom_weights is not None:
        total = sum(custom_weights.values())
        if total > 0:
            return {k: v / total for k, v in custom_weights.items()}
        else:
            # User explicitly passed weights but all are 0 (all toggled off)
            return custom_weights

    if preset and preset in WEIGHT_PRESETS:
        return WEIGHT_PRESETS[preset]
    return DEFAULT_WEIGHTS


def score_demographics(lat: float, lng: float, radius_km: float) -> Tuple[float, Dict]:
    """Score based on nearby demographics."""
    features = get_features_in_radius("demographics", lat, lng, radius_km)

    if not features:
        return 15.0, {"population_nearby": 0, "tracts": 0, "avg_income": 0}

    total_pop = 0
    weighted_income = 0
    weighted_density = 0
    total_weight = 0

    for f in features:
        props = f["properties"]
        dist = f.get("distance_km", 1)
        decay = exponential_decay(dist, DISTANCE_DECAY_RATE)

        pop = props.get("population", 0)
        total_pop += pop
        weighted_income += props.get("median_income", 0) * decay
        weighted_density += props.get("population_density", 0) * decay
        total_weight += decay

    if total_weight == 0:
        return 15.0, {"population_nearby": 0, "tracts": 0, "avg_income": 0}

    avg_income = weighted_income / total_weight
    avg_density = weighted_density / total_weight

    # Score components
    pop_score = normalize_score(total_pop, 0, 500000) * 0.4
    density_score = normalize_score(avg_density, 0, 30000) * 0.3
    income_score = normalize_score(avg_income, 8000, 80000) * 0.3

    score = pop_score + density_score + income_score

    details = {
        "population_nearby": total_pop,
        "tracts": len(features),
        "avg_income": round(avg_income, 0),
        "avg_density": round(avg_density, 1),
        "pop_score": round(pop_score, 1),
        "density_score": round(density_score, 1),
        "income_score": round(income_score, 1),
    }

    return round(min(100, score), 2), details


def score_transportation(lat: float, lng: float, radius_km: float) -> Tuple[float, Dict]:
    """Score based on transportation network proximity."""
    features = get_features_in_radius("transportation", lat, lng, radius_km)

    if not features:
        return 10.0, {"roads": 0, "transit_stops": 0, "nearest_highway_km": None}

    highways = [f for f in features if f["properties"].get("category") in ("national_highway", "state_highway")]
    transit = [f for f in features if f["properties"].get("type") == "transit_stop"]
    arterials = [f for f in features if f["properties"].get("type") == "arterial"]

    # Highway proximity (exponential decay)
    highway_score = 0
    nearest_highway = None
    if highways:
        nearest_hw = min(highways, key=lambda f: f.get("distance_km", 999))
        nearest_highway = nearest_hw.get("distance_km", 999)
        highway_score = exponential_decay(nearest_highway, 0.3) * 100 * 0.35

    # Transit density
    transit_score = normalize_score(len(transit), 0, 15) * 0.30

    # Road density
    road_density = len(features)
    road_score = normalize_score(road_density, 0, 20) * 0.20

    # Transit ridership
    ridership_score = 0
    if transit:
        avg_ridership = sum(f["properties"].get("daily_ridership", 0) for f in transit) / len(transit)
        ridership_score = normalize_score(avg_ridership, 0, 30000) * 0.15

    score = highway_score + transit_score + road_score + ridership_score

    details = {
        "roads": len(arterials),
        "highways": len(highways),
        "transit_stops": len(transit),
        "nearest_highway_km": round(nearest_highway, 2) if nearest_highway else None,
        "highway_score": round(highway_score, 1),
        "transit_score": round(transit_score, 1),
        "road_score": round(road_score, 1),
    }

    return round(min(100, score), 2), details


def score_poi(lat: float, lng: float, radius_km: float) -> Tuple[float, Dict]:
    """Score based on Points of Interest (competitors, anchors, complementary)."""
    features = get_features_in_radius("poi", lat, lng, radius_km)

    if not features:
        return 20.0, {"competitors": 0, "anchors": 0, "complementary": 0}

    competitors = [f for f in features if f["properties"].get("category") == "competitor"]
    anchors = [f for f in features if f["properties"].get("category") == "anchor"]
    complementary = [f for f in features if f["properties"].get("category") == "complementary"]

    # Competitive density analysis
    comp_score = competitive_density_score(len(competitors), optimal_min=2, optimal_max=6) * 0.35

    # Anchor proximity (malls, major stores)
    anchor_score = 0
    if anchors:
        nearest_anchor = min(anchors, key=lambda f: f.get("distance_km", 999))
        anchor_dist = nearest_anchor.get("distance_km", 999)
        anchor_score = exponential_decay(anchor_dist, 0.4) * 100 * 0.30

    # Complementary business density
    comp_biz_score = normalize_score(len(complementary), 0, 20) * 0.35

    score = comp_score + anchor_score + comp_biz_score

    details = {
        "competitors": len(competitors),
        "anchors": len(anchors),
        "complementary": len(complementary),
        "nearest_anchor_km": round(min((f.get("distance_km", 999) for f in anchors), default=0), 2),
        "competitive_score": round(comp_score, 1),
        "anchor_score": round(anchor_score, 1),
        "complementary_score": round(comp_biz_score, 1),
    }

    return round(min(100, score), 2), details


def score_landuse(lat: float, lng: float, radius_km: float) -> Tuple[float, Dict]:
    """Score based on land use and zoning."""
    features = get_features_in_radius("landuse", lat, lng, radius_km)

    if not features:
        return 30.0, {"zones": 0, "dominant_zone": "unknown"}

    # Find the closest zone (most relevant)
    closest = min(features, key=lambda f: f.get("distance_km", 999))
    zone_type = closest["properties"].get("zone_type", "unknown")

    # Zone type scoring (for retail use case)
    zone_scores = {
        "commercial": 95,
        "mixed_use": 85,
        "residential": 55,
        "institutional": 45,
        "industrial": 30,
        "agricultural": 15,
    }

    zone_score = zone_scores.get(zone_type, 40) * 0.40

    # Development status
    dev_status = closest["properties"].get("development_status", "undeveloped")
    dev_scores = {"developed": 80, "developing": 90, "undeveloped": 50}
    dev_score = dev_scores.get(dev_status, 50) * 0.25

    # Building coverage (moderate is best for new construction)
    bcr = closest["properties"].get("building_coverage_ratio", 0.5)
    bcr_score = (1.0 - abs(bcr - 0.4) / 0.6) * 100 * 0.20
    bcr_score = max(0, bcr_score)

    # Variety of zones nearby (diversity is good)
    zone_types = set(f["properties"].get("zone_type") for f in features)
    diversity_score = normalize_score(len(zone_types), 1, 5) * 0.15

    score = zone_score + dev_score + bcr_score + diversity_score

    details = {
        "zones": len(features),
        "dominant_zone": zone_type,
        "development_status": dev_status,
        "zone_types_nearby": list(zone_types),
        "building_coverage": bcr,
        "zone_score": round(zone_score, 1),
        "dev_score": round(dev_score, 1),
    }

    return round(min(100, score), 2), details


def score_environmental(lat: float, lng: float, radius_km: float) -> Tuple[float, Dict]:
    """Score based on environmental risks (inverted - lower risk = higher score)."""
    features = get_features_in_radius("environmental", lat, lng, radius_km)

    if not features:
        return 80.0, {"flood_risk": 0, "earthquake_risk": 0, "aqi": "unknown", "avg_aqi": 0}

    # Separate risk types
    flood = [f for f in features if f["properties"].get("risk_type") == "flood"]
    earthquake = [f for f in features if f["properties"].get("risk_type") == "earthquake"]
    aqi = [f for f in features if f["properties"].get("risk_type") == "air_quality"]

    # Flood risk (higher severity = lower score)
    flood_score = 100
    max_flood_severity = 0
    if flood:
        max_flood_severity = max(f["properties"].get("severity", 0) for f in flood)
        nearest_flood = min(flood, key=lambda f: f.get("distance_km", 999))
        flood_dist = nearest_flood.get("distance_km", 1)
        flood_impact = max_flood_severity * exponential_decay(flood_dist, 0.3)
        flood_score = max(0, (1 - flood_impact) * 100)

    # Earthquake risk
    quake_score = 100
    max_quake_severity = 0
    if earthquake:
        max_quake_severity = max(f["properties"].get("severity", 0) for f in earthquake)
        nearest_quake = min(earthquake, key=lambda f: f.get("distance_km", 999))
        quake_dist = nearest_quake.get("distance_km", 1)
        quake_impact = max_quake_severity * exponential_decay(quake_dist, 0.2)
        quake_score = max(0, (1 - quake_impact) * 100)

    # Air quality
    aqi_score = 80
    avg_aqi = 0
    if aqi:
        aqi_values = [f["properties"].get("aqi_value", 100) for f in aqi]
        avg_aqi = sum(aqi_values) / len(aqi_values)
        aqi_score = max(0, normalize_score(300 - avg_aqi, 0, 300))

    # Composite environmental score
    score = flood_score * 0.35 + quake_score * 0.35 + aqi_score * 0.30

    details = {
        "flood_risk": round(max_flood_severity, 2),
        "earthquake_risk": round(max_quake_severity, 2),
        "avg_aqi": round(avg_aqi, 0),
        "flood_score": round(flood_score, 1),
        "quake_score": round(quake_score, 1),
        "aqi_score": round(aqi_score, 1),
        "flood_features": len(flood),
        "quake_features": len(earthquake),
        "aqi_stations": len(aqi),
    }

    return round(min(100, score), 2), details


def compute_site_score(lat: float, lng: float,
                       weights: Optional[Dict[str, float]] = None,
                       preset: Optional[str] = None,
                       radius_km: float = 5.0) -> Dict[str, Any]:
    """Compute composite site readiness score for a location."""
    w = get_weights(weights, preset)

    # Compute sub-scores
    scorers = {
        "demographics": score_demographics,
        "transportation": score_transportation,
        "poi": score_poi,
        "landuse": score_landuse,
        "environmental": score_environmental,
    }

    sub_scores = []
    composite = 0.0
    threshold_violations = []
    nearby_summary = {}

    for layer_name, scorer in scorers.items():
        layer_weight = w.get(layer_name, 0.2)
        
        # Skip completely if layer is disabled (weight is 0)
        if layer_weight <= 0:
            continue
            
        layer_score, details = scorer(lat, lng, radius_km)
        weighted = layer_score * layer_weight

        sub_scores.append({
            "layer": layer_name,
            "score": layer_score,
            "weight": layer_weight,
            "weighted_score": round(weighted, 2),
            "details": details,
        })

        composite += weighted
        nearby_summary[layer_name] = details

    # Check threshold constraints
    demo_details = nearby_summary.get("demographics", {})
    if demo_details.get("population_nearby", 0) < SCORE_THRESHOLDS["min_population_5km"]:
        threshold_violations.append(
            f"Population within {radius_km}km ({demo_details.get('population_nearby', 0)}) "
            f"below minimum ({SCORE_THRESHOLDS['min_population_5km']})"
        )

    env_details = nearby_summary.get("environmental", {})
    flood_risk_val = env_details.get("flood_risk", 0)
    if isinstance(flood_risk_val, (int, float)) and flood_risk_val > SCORE_THRESHOLDS["max_flood_risk"]:
        threshold_violations.append(
            f"Flood risk ({env_details.get('flood_risk', 0)}) exceeds maximum ({SCORE_THRESHOLDS['max_flood_risk']})"
        )

    quake_risk_val = env_details.get("earthquake_risk", 0)
    if isinstance(quake_risk_val, (int, float)) and quake_risk_val > SCORE_THRESHOLDS["max_earthquake_risk"]:
        threshold_violations.append(
            f"Earthquake risk ({env_details.get('earthquake_risk', 0)}) exceeds maximum ({SCORE_THRESHOLDS['max_earthquake_risk']})"
        )

    # Apply penalty for threshold violations
    penalty = len(threshold_violations) * 5
    composite = max(0, composite - penalty)

    # ─── Investment Potential Analysis ────────────────────────
    investment = _compute_investment_potential(composite, sub_scores)

    result = {
        "lat": lat,
        "lng": lng,
        "composite_score": round(composite, 2),
        "grade": get_grade(composite),
        "sub_scores": sub_scores,
        "threshold_violations": threshold_violations,
        "nearby_summary": nearby_summary,
        "investment_potential": investment,
    }

    return result


def _compute_investment_potential(composite_score: float, sub_scores: list) -> dict:
    """Convert technical scores into business investment insights."""
    # Extract raw layer scores from sub_scores list
    layer_scores = {}
    for sub in sub_scores:
        layer_scores[sub.get("layer", "")] = sub.get("score", 0)

    demo_score = layer_scores.get("demographics", 0)
    transport_score = layer_scores.get("transportation", 0)
    landuse_score = layer_scores.get("landuse", 0)
    env_score = layer_scores.get("environmental", 0)

    # A) ROI Potential
    if composite_score >= 80:
        roi = "High"
    elif composite_score >= 60:
        roi = "Medium"
    else:
        roi = "Low"

    # B) Risk Level
    if env_score < 50:
        risk = "High"
    elif transport_score < 30:
        risk = "Medium"
    else:
        risk = "Low"

    # C) Growth Potential
    if demo_score > 70 and 50 <= landuse_score <= 80:
        growth = "High"
    elif demo_score > 50:
        growth = "Medium"
    else:
        growth = "Low"

    return {
        "roi_potential": roi,
        "risk_level": risk,
        "growth_potential": growth,
    }
