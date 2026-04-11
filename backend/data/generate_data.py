"""
Generate synthetic geospatial data for Gujarat, India.
Creates 5 data layers: demographics, transportation, POI, land use, environmental.
"""
import json
import math
import os
import random

random.seed(42)

# Gujarat cities with approximate coordinates and populations
CITIES = {
    "Ahmedabad": {"lat": 23.0225, "lng": 72.5714, "pop": 8000000, "radius": 0.25},
    "Surat": {"lat": 21.1702, "lng": 72.8311, "pop": 7500000, "radius": 0.20},
    "Vadodara": {"lat": 22.3072, "lng": 73.1812, "pop": 2100000, "radius": 0.15},
    "Rajkot": {"lat": 22.3039, "lng": 70.8022, "pop": 1800000, "radius": 0.15},
    "Gandhinagar": {"lat": 23.2156, "lng": 72.6369, "pop": 400000, "radius": 0.10},
    "Bhavnagar": {"lat": 21.7645, "lng": 72.1519, "pop": 700000, "radius": 0.10},
    "Jamnagar": {"lat": 22.4707, "lng": 70.0577, "pop": 600000, "radius": 0.10},
    "Junagadh": {"lat": 21.5222, "lng": 70.4579, "pop": 400000, "radius": 0.08},
    "Anand": {"lat": 22.5645, "lng": 72.9289, "pop": 300000, "radius": 0.07},
    "Navsari": {"lat": 20.9467, "lng": 72.9520, "pop": 250000, "radius": 0.06},
    "Morbi": {"lat": 22.8173, "lng": 70.8370, "pop": 300000, "radius": 0.07},
    "Mehsana": {"lat": 23.5880, "lng": 72.3693, "pop": 250000, "radius": 0.06},
    "Bharuch": {"lat": 21.7051, "lng": 72.9959, "pop": 230000, "radius": 0.06},
    "Vapi": {"lat": 20.3893, "lng": 72.9106, "pop": 200000, "radius": 0.05},
    "Gandhidham": {"lat": 23.0753, "lng": 70.1337, "pop": 250000, "radius": 0.06},
}

TOWNS = {
    "Nadiad": {"lat": 22.6916, "lng": 72.8634, "pop": 150000},
    "Surendranagar": {"lat": 22.7289, "lng": 71.6480, "pop": 180000},
    "Palanpur": {"lat": 24.1725, "lng": 72.4260, "pop": 140000},
    "Porbandar": {"lat": 21.6417, "lng": 69.6293, "pop": 180000},
    "Godhra": {"lat": 22.7788, "lng": 73.6143, "pop": 150000},
    "Dahod": {"lat": 22.8350, "lng": 74.2525, "pop": 130000},
    "Amreli": {"lat": 21.6032, "lng": 71.2225, "pop": 120000},
    "Veraval": {"lat": 20.9066, "lng": 70.3628, "pop": 160000},
    "Dwarka": {"lat": 22.2442, "lng": 68.9685, "pop": 40000},
    "Bhuj": {"lat": 23.2420, "lng": 69.6669, "pop": 180000},
}


def random_point_near(lat, lng, radius_deg):
    """Generate a random point within radius_deg of center."""
    angle = random.uniform(0, 2 * math.pi)
    r = radius_deg * math.sqrt(random.random())
    return lat + r * math.sin(angle), lng + r * math.cos(angle)


def make_polygon(lat, lng, size=0.02, irregular=True):
    """Create a GeoJSON polygon around a center point."""
    points = []
    n_sides = random.randint(5, 8) if irregular else 4
    for i in range(n_sides):
        angle = 2 * math.pi * i / n_sides
        r = size * (1 + random.uniform(-0.3, 0.3)) if irregular else size
        px = lng + r * math.cos(angle)
        py = lat + r * math.sin(angle)
        points.append([round(px, 6), round(py, 6)])
    points.append(points[0])  # close ring
    return {"type": "Polygon", "coordinates": [points]}


def generate_demographics():
    """Generate demographic census tract data for Gujarat."""
    features = []
    fid = 0

    for city_name, info in CITIES.items():
        n_tracts = max(5, int(info["pop"] / 100000))
        for i in range(n_tracts):
            lat, lng = random_point_near(info["lat"], info["lng"], info["radius"])
            pop = int(random.gauss(info["pop"] / n_tracts, info["pop"] / (n_tracts * 3)))
            pop = max(1000, pop)
            density = pop / (random.uniform(1.5, 8.0))  # per km²

            feature = {
                "type": "Feature",
                "id": fid,
                "properties": {
                    "id": fid,
                    "name": f"{city_name}_Tract_{i+1}",
                    "city": city_name,
                    "population": pop,
                    "population_density": round(density, 1),
                    "median_income": round(random.gauss(35000, 15000), 0),
                    "median_age": round(random.gauss(30, 5), 1),
                    "households": int(pop / random.uniform(3.5, 5.5)),
                    "literacy_rate": round(random.uniform(0.65, 0.95), 2),
                },
                "geometry": make_polygon(lat, lng, info["radius"] / n_tracts * 1.5),
            }
            feature["properties"]["median_income"] = max(12000, feature["properties"]["median_income"])
            feature["properties"]["median_age"] = max(18, min(55, feature["properties"]["median_age"]))
            features.append(feature)
            fid += 1

    # Add some rural tracts
    for _ in range(30):
        lat = random.uniform(20.5, 24.5)
        lng = random.uniform(69.0, 74.0)
        pop = random.randint(500, 5000)
        features.append({
            "type": "Feature",
            "id": fid,
            "properties": {
                "id": fid,
                "name": f"Rural_Tract_{fid}",
                "city": "Rural",
                "population": pop,
                "population_density": round(pop / random.uniform(10, 50), 1),
                "median_income": round(random.uniform(8000, 20000), 0),
                "median_age": round(random.gauss(28, 6), 1),
                "households": int(pop / random.uniform(4, 6)),
                "literacy_rate": round(random.uniform(0.45, 0.75), 2),
            },
            "geometry": make_polygon(lat, lng, random.uniform(0.03, 0.08)),
        })
        fid += 1

    return {"type": "FeatureCollection", "features": features}


def generate_transportation():
    """Generate transportation network data."""
    features = []
    fid = 0

    # National Highways
    highways = [
        {"name": "NH-48 (Ahmedabad-Mumbai)", "points": [(23.02, 72.57), (22.30, 73.18), (21.17, 72.83), (20.39, 72.91)]},
        {"name": "NH-8 (Ahmedabad-Delhi)", "points": [(23.02, 72.57), (23.59, 72.37), (24.17, 72.43)]},
        {"name": "NH-47 (Ahmedabad-Rajkot)", "points": [(23.02, 72.57), (22.73, 71.65), (22.30, 70.80)]},
        {"name": "NH-64 (Rajkot-Jamnagar)", "points": [(22.30, 70.80), (22.47, 70.06)]},
        {"name": "NH-8D (Ahmedabad-Gandhinagar)", "points": [(23.02, 72.57), (23.22, 72.64)]},
        {"name": "NH-53 (Vadodara-Surat)", "points": [(22.31, 73.18), (21.71, 73.00), (21.17, 72.83)]},
    ]

    for hw in highways:
        coords = [[round(p[1], 6), round(p[0], 6)] for p in hw["points"]]
        features.append({
            "type": "Feature",
            "id": fid,
            "properties": {
                "id": fid,
                "name": hw["name"],
                "type": "highway",
                "category": "national_highway",
                "lanes": random.choice([4, 6, 8]),
                "speed_limit_kmh": random.choice([80, 100, 120]),
            },
            "geometry": {"type": "LineString", "coordinates": coords},
        })
        fid += 1

    # State highways and arterial roads
    for city_name, info in CITIES.items():
        n_roads = random.randint(3, 8)
        for i in range(n_roads):
            # Start near city center, end at city edge
            lat1, lng1 = random_point_near(info["lat"], info["lng"], info["radius"] * 0.3)
            lat2, lng2 = random_point_near(info["lat"], info["lng"], info["radius"] * 0.8)

            # Generate intermediate waypoints for realistic road curves
            n_segments = random.randint(4, 7)
            road_coords = []
            for s in range(n_segments + 1):
                t = s / n_segments
                # Interpolate between start and end with small random offset
                mid_lat = lat1 + (lat2 - lat1) * t + random.uniform(-0.005, 0.005)
                mid_lng = lng1 + (lng2 - lng1) * t + random.uniform(-0.005, 0.005)
                road_coords.append([round(mid_lng, 6), round(mid_lat, 6)])

            features.append({
                "type": "Feature",
                "id": fid,
                "properties": {
                    "id": fid,
                    "name": f"{city_name}_Road_{i+1}",
                    "type": "arterial",
                    "category": "state_highway" if random.random() > 0.5 else "arterial_road",
                    "lanes": random.choice([2, 4]),
                    "speed_limit_kmh": random.choice([40, 60, 80]),
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": road_coords,
                },
            })
            fid += 1

    # Transit stops (BRTS, Metro, Railway)
    transit_types = ["BRTS_Stop", "Metro_Station", "Railway_Station", "Bus_Stand"]
    for city_name, info in CITIES.items():
        n_stops = random.randint(5, 20)
        for i in range(n_stops):
            lat, lng = random_point_near(info["lat"], info["lng"], info["radius"])
            t_type = random.choice(transit_types)
            features.append({
                "type": "Feature",
                "id": fid,
                "properties": {
                    "id": fid,
                    "name": f"{city_name}_{t_type}_{i+1}",
                    "type": "transit_stop",
                    "category": t_type,
                    "daily_ridership": random.randint(500, 50000),
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [round(lng, 6), round(lat, 6)],
                },
            })
            fid += 1

    return {"type": "FeatureCollection", "features": features}


def generate_poi():
    """Generate Points of Interest: competitors, anchors, complementary businesses."""
    features = []
    fid = 0

    categories = {
        "competitor": {
            "names": ["Reliance Retail", "D-Mart", "Big Bazaar", "Star Bazaar", "Vishal Mega Mart",
                      "Spencer's", "More Supermarket", "Easyday", "Spar Hypermarket"],
            "weight": 0.35,
        },
        "anchor": {
            "names": ["Ahmedabad One Mall", "AlphaOne Mall", "Palladium Mall", "Crystal Mall",
                      "Iscon Mega Mall", "Rajhans Multiplex", "CG Square", "Inorbit Mall",
                      "VR Surat", "Infinity Mall"],
            "weight": 0.25,
        },
        "complementary": {
            "names": ["SBI Branch", "HDFC Bank ATM", "ICICI Branch", "Zydus Hospital",
                      "Apollo Pharmacy", "Indian Oil Pump", "HP Petrol Pump",
                      "Jio Store", "Airtel Store", "Vodafone Store",
                      "Domino's Pizza", "McDonald's", "Subway", "Pizza Hut",
                      "OYO Rooms", "FabHotel", "CCD Cafe"],
            "weight": 0.40,
        },
    }

    for city_name, info in CITIES.items():
        for cat_key, cat_info in categories.items():
            n_poi = int(random.uniform(5, 25) * cat_info["weight"] * (info["pop"] / 1000000))
            n_poi = max(2, n_poi)
            for i in range(n_poi):
                lat, lng = random_point_near(info["lat"], info["lng"], info["radius"])
                features.append({
                    "type": "Feature",
                    "id": fid,
                    "properties": {
                        "id": fid,
                        "name": random.choice(cat_info["names"]),
                        "category": cat_key,
                        "city": city_name,
                        "rating": round(random.uniform(2.5, 5.0), 1),
                        "annual_revenue_lakhs": round(random.uniform(10, 500), 1),
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [round(lng, 6), round(lat, 6)],
                    },
                })
                fid += 1

    # Add POIs in smaller towns
    for town_name, info in TOWNS.items():
        for cat_key, cat_info in categories.items():
            n_poi = random.randint(1, 4)
            for i in range(n_poi):
                lat, lng = random_point_near(info["lat"], info["lng"], 0.05)
                features.append({
                    "type": "Feature",
                    "id": fid,
                    "properties": {
                        "id": fid,
                        "name": random.choice(cat_info["names"]),
                        "category": cat_key,
                        "city": town_name,
                        "rating": round(random.uniform(2.0, 4.5), 1),
                        "annual_revenue_lakhs": round(random.uniform(5, 100), 1),
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [round(lng, 6), round(lat, 6)],
                    },
                })
                fid += 1

    return {"type": "FeatureCollection", "features": features}


def generate_landuse():
    """Generate land use and zoning data."""
    features = []
    fid = 0

    zone_types = ["commercial", "residential", "industrial", "mixed_use", "agricultural", "institutional"]

    for city_name, info in CITIES.items():
        n_zones = random.randint(6, 15)
        for i in range(n_zones):
            lat, lng = random_point_near(info["lat"], info["lng"], info["radius"])
            dist_from_center = math.sqrt((lat - info["lat"])**2 + (lng - info["lng"])**2)

            # Closer to center = more likely commercial/mixed; farther = residential/industrial
            if dist_from_center < info["radius"] * 0.3:
                zone = random.choice(["commercial", "commercial", "mixed_use"])
            elif dist_from_center < info["radius"] * 0.6:
                zone = random.choice(["residential", "mixed_use", "commercial", "institutional"])
            else:
                zone = random.choice(["residential", "industrial", "agricultural", "industrial"])

            features.append({
                "type": "Feature",
                "id": fid,
                "properties": {
                    "id": fid,
                    "name": f"{city_name}_Zone_{i+1}",
                    "city": city_name,
                    "zone_type": zone,
                    "area_sqkm": round(random.uniform(0.5, 10.0), 2),
                    "building_coverage_ratio": round(random.uniform(0.2, 0.8), 2),
                    "floor_area_ratio": round(random.uniform(1.0, 4.0), 1),
                    "is_gidc": zone == "industrial" and random.random() > 0.5,
                    "development_status": random.choice(["developed", "developing", "undeveloped"]),
                },
                "geometry": make_polygon(lat, lng, random.uniform(0.01, 0.04)),
            })
            fid += 1

    # GIDC Industrial Estates
    gidc_zones = [
        {"name": "Vatva GIDC", "lat": 22.9650, "lng": 72.5950},
        {"name": "Naroda GIDC", "lat": 23.0800, "lng": 72.6500},
        {"name": "Sanand GIDC", "lat": 22.9900, "lng": 72.3800},
        {"name": "Halol GIDC", "lat": 22.5100, "lng": 73.4700},
        {"name": "Vapi GIDC", "lat": 20.3800, "lng": 72.9000},
        {"name": "Ankleshwar GIDC", "lat": 21.6300, "lng": 73.0000},
        {"name": "Mundra SEZ", "lat": 22.8400, "lng": 69.7200},
        {"name": "Dahej SEZ", "lat": 21.7100, "lng": 72.5800},
    ]

    for gidc in gidc_zones:
        features.append({
            "type": "Feature",
            "id": fid,
            "properties": {
                "id": fid,
                "name": gidc["name"],
                "city": "Industrial Estate",
                "zone_type": "industrial",
                "area_sqkm": round(random.uniform(5, 30), 2),
                "building_coverage_ratio": round(random.uniform(0.3, 0.6), 2),
                "floor_area_ratio": round(random.uniform(1.0, 2.5), 1),
                "is_gidc": True,
                "development_status": random.choice(["developed", "developing"]),
            },
            "geometry": make_polygon(gidc["lat"], gidc["lng"], random.uniform(0.03, 0.06)),
        })
        fid += 1

    return {"type": "FeatureCollection", "features": features}


def generate_environmental():
    """Generate environmental and risk data."""
    features = []
    fid = 0

    # Flood zones along rivers and coast
    flood_zones = [
        {"name": "Sabarmati Flood Zone", "lat": 23.05, "lng": 72.58, "size": 0.08},
        {"name": "Tapi Flood Zone", "lat": 21.18, "lng": 72.85, "size": 0.10},
        {"name": "Narmada Flood Zone", "lat": 21.70, "lng": 73.00, "size": 0.12},
        {"name": "Mahi River Flood Zone", "lat": 22.35, "lng": 73.20, "size": 0.07},
        {"name": "Gulf of Khambhat Coastal", "lat": 21.50, "lng": 72.30, "size": 0.15},
        {"name": "Gulf of Kutch Coastal", "lat": 22.80, "lng": 69.80, "size": 0.12},
        {"name": "Saurashtra Coast", "lat": 21.00, "lng": 70.50, "size": 0.10},
    ]

    for fz in flood_zones:
        features.append({
            "type": "Feature",
            "id": fid,
            "properties": {
                "id": fid,
                "name": fz["name"],
                "risk_type": "flood",
                "severity": round(random.uniform(0.4, 0.9), 2),
                "return_period_years": random.choice([10, 25, 50, 100]),
                "description": f"Flood-prone area near {fz['name'].replace(' Flood Zone', '').replace(' Coastal', '')}",
            },
            "geometry": make_polygon(fz["lat"], fz["lng"], fz["size"]),
        })
        fid += 1

    # Earthquake risk zones (Kutch region is high risk)
    quake_zones = [
        {"name": "Kutch Seismic Zone V", "lat": 23.30, "lng": 69.80, "size": 0.30, "severity": 0.9},
        {"name": "Kutch Seismic Zone IV", "lat": 23.00, "lng": 70.50, "size": 0.25, "severity": 0.7},
        {"name": "Saurashtra Seismic Zone III", "lat": 22.00, "lng": 71.00, "size": 0.20, "severity": 0.5},
        {"name": "North Gujarat Seismic Zone III", "lat": 23.80, "lng": 72.50, "size": 0.20, "severity": 0.5},
        {"name": "Central Gujarat Seismic Zone III", "lat": 22.50, "lng": 73.00, "size": 0.15, "severity": 0.4},
    ]

    for qz in quake_zones:
        features.append({
            "type": "Feature",
            "id": fid,
            "properties": {
                "id": fid,
                "name": qz["name"],
                "risk_type": "earthquake",
                "severity": qz["severity"],
                "seismic_zone": "V" if qz["severity"] > 0.8 else "IV" if qz["severity"] > 0.6 else "III",
                "description": f"Seismic risk area - {qz['name']}",
            },
            "geometry": make_polygon(qz["lat"], qz["lng"], qz["size"]),
        })
        fid += 1

    # Air Quality Index stations
    for city_name, info in CITIES.items():
        n_stations = random.randint(2, 6)
        for i in range(n_stations):
            lat, lng = random_point_near(info["lat"], info["lng"], info["radius"] * 0.8)
            aqi = random.gauss(120, 40)  # Gujarat typically 80-200
            aqi = max(30, min(300, aqi))
            features.append({
                "type": "Feature",
                "id": fid,
                "properties": {
                    "id": fid,
                    "name": f"{city_name}_AQI_Station_{i+1}",
                    "risk_type": "air_quality",
                    "severity": round(min(1.0, aqi / 300), 2),
                    "aqi_value": round(aqi, 0),
                    "aqi_category": (
                        "Good" if aqi < 50 else
                        "Satisfactory" if aqi < 100 else
                        "Moderate" if aqi < 200 else
                        "Poor" if aqi < 300 else "Very Poor"
                    ),
                    "description": f"Air quality monitoring at {city_name}",
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [round(lng, 6), round(lat, 6)],
                },
            })
            fid += 1

    return {"type": "FeatureCollection", "features": features}


def main():
    """Generate all data layers and save to files."""
    data_dir = os.path.dirname(os.path.abspath(__file__))

    layers = {
        "demographics.geojson": generate_demographics,
        "transportation.geojson": generate_transportation,
        "poi.geojson": generate_poi,
        "landuse.geojson": generate_landuse,
        "environmental.geojson": generate_environmental,
    }

    for filename, generator in layers.items():
        filepath = os.path.join(data_dir, filename)
        data = generator()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Generated {filename}: {len(data['features'])} features")

    print("\nAll data layers generated successfully!")


if __name__ == "__main__":
    main()
