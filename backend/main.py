"""
GeoSpatial Site Readiness Analyzer - FastAPI Backend
AI-Powered Location Intelligence for Commercial Real Estate and Infrastructure
"""
import io
import json
from datetime import datetime
from typing import Optional, Dict

from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

from config import WEIGHT_PRESETS, GUJARAT_BOUNDS, GUJARAT_CITIES
from models.schemas import (
    ScoreRequest, PolygonScoreRequest, CompareRequest,
    ClusterRequest, IsochroneRequest, ExportRequest, HeatmapRequest,
    HeatmapPostRequest, SmartSearchRequest
)
from services.data_ingestion import load_all_layers, get_layer, get_layer_summary, get_all_layers, register_layer
from services.upload import process_upload, save_uploaded_layer
from services.scoring import compute_site_score, get_weights
from services.clustering import compute_heatmap, detect_clusters
from services.routing import compute_isochrone, get_route_info

# Initialize FastAPI app
app = FastAPI(
    title="GeoSpatial Site Readiness Analyzer",
    description="AI-Powered Location Intelligence for Gujarat, India",
    version="1.0.0",
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    """Load geospatial data on startup."""
    print("Loading geospatial data layers...")
    load_all_layers()
    print("All layers loaded. Server ready.")


# ─── Layer Endpoints ────────────────────────────────────────────────────────

@app.get("/api/layers")
async def list_layers():
    """List all available data layers with metadata."""
    return {"layers": get_layer_summary()}


@app.get("/api/layers/{layer_name}")
async def get_layer_data(layer_name: str):
    """Fetch GeoJSON data for a specific layer."""
    layer = get_layer(layer_name)
    if not layer:
        raise HTTPException(404, f"Layer '{layer_name}' not found")
    return layer


@app.post("/api/upload")
async def upload_layer(file: UploadFile = File(...), layer_name: Optional[str] = Form(None)):
    """Upload a new data layer (GeoJSON, zipped Shapefile, GeoTIFF, WKT)."""
    try:
        content = await file.read()
        filename = file.filename

        # Process and convert to GeoJSON
        geojson, final_name = process_upload(content, filename, layer_name)
        
        # Save to disk
        save_uploaded_layer(geojson, final_name)
        
        # Register in memory
        register_layer(final_name, geojson)
        
        return {
            "message": f"Successfully uploaded and processed layer '{final_name}'",
            "layer_name": final_name,
            "feature_count": len(geojson.get("features", [])),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─── Scoring Endpoints ──────────────────────────────────────────────────────

@app.post("/api/score")
async def score_site(req: ScoreRequest):
    """Compute site readiness score for a single point."""
    result = compute_site_score(
        lat=req.lat,
        lng=req.lng,
        weights=req.weights,
        preset=req.preset,
        radius_km=req.radius_km,
    )
    return result


@app.post("/api/score/polygon")
async def score_polygon(req: PolygonScoreRequest):
    """Score all hexagons within a drawn polygon."""
    from services.clustering import get_h3_hexagons, hex_to_coords

    # Compute bounding box from polygon
    lngs = [p[0] for p in req.polygon]
    lats = [p[1] for p in req.polygon]
    bounds = {
        "min_lat": min(lats),
        "max_lat": max(lats),
        "min_lng": min(lngs),
        "max_lng": max(lngs),
    }

    hexagons = get_h3_hexagons(bounds, req.h3_resolution)

    # Score each hexagon center that falls within the polygon
    from utils.spatial import point_in_polygon_approx
    results = []
    for hex_id in hexagons[:200]:  # Limit for performance
        lat, lng, boundary = hex_to_coords(hex_id, req.h3_resolution)
        if point_in_polygon_approx(lat, lng, req.polygon):
            result = compute_site_score(lat, lng, req.weights, req.preset)
            results.append({
                "hex_id": hex_id,
                "lat": lat,
                "lng": lng,
                "score": result["composite_score"],
                "grade": result["grade"],
                "boundary": boundary,
            })

    return {
        "hexagons": results,
        "count": len(results),
        "avg_score": round(sum(r["score"] for r in results) / max(1, len(results)), 2),
    }


# ─── Clustering Endpoints ───────────────────────────────────────────────────

@app.post("/api/cluster")
async def cluster_sites(req: ClusterRequest):
    """Run spatial clustering to find hot/cold spots."""
    heatmap = compute_heatmap(
        bounds=req.bounds,
        resolution=req.h3_resolution,
        weights=req.weights,
        preset=req.preset,
        max_hexagons=300,
    )
    clusters = detect_clusters(heatmap, req.min_samples, req.eps_km)
    return clusters


@app.post("/api/h3/heatmap")
async def get_heatmap(req: HeatmapPostRequest):
    """Get H3 hexagonal heatmap of scores using current weights."""
    bounds = None
    if req.bounds:
        bounds = req.bounds

    heatmap = compute_heatmap(
        bounds,
        req.h3_resolution,
        weights=req.weights,
        preset=req.preset,
        max_hexagons=400,
    )
    return heatmap


# ─── Routing Endpoints ──────────────────────────────────────────────────────

@app.post("/api/isochrone")
async def get_isochrone(req: IsochroneRequest):
    """Compute drive-time or walk-time isochrones."""
    result = compute_isochrone(
        lat=req.lat,
        lng=req.lng,
        mode=req.mode,
        intervals=req.intervals,
    )
    return result


# ─── Comparison Endpoints ───────────────────────────────────────────────────

@app.post("/api/compare")
async def compare_sites(req: CompareRequest):
    """Compare multiple candidate sites side by side."""
    if len(req.sites) > 10:
        raise HTTPException(400, "Maximum 10 sites for comparison")

    results = []
    for site in req.sites:
        result = compute_site_score(
            lat=site.lat,
            lng=site.lng,
            weights=req.weights,
            preset=req.preset,
        )
        results.append(result)

    # Rank them
    ranked = sorted(results, key=lambda r: r["composite_score"], reverse=True)
    for i, r in enumerate(ranked):
        r["rank"] = i + 1

    return {"sites": ranked, "count": len(ranked)}


# ─── Export Endpoints ────────────────────────────────────────────────────────

@app.post("/api/export")
async def export_report(req: ExportRequest):
    """Generate PDF or JSON report for selected sites."""
    if req.pre_computed_results:
        # Use pre-computed results directly — matches what the user sees on screen
        results = req.pre_computed_results
    elif req.sites:
        # Legacy: re-score from coordinates
        results = []
        for site in req.sites:
            result = compute_site_score(
                lat=site.lat,
                lng=site.lng,
                weights=req.weights,
                preset=req.preset,
            )
            results.append(result)
    else:
        raise HTTPException(400, "Provide either pre_computed_results or sites")

    ranked = sorted(results, key=lambda r: r.get("composite_score", 0), reverse=True)
    for i, r in enumerate(ranked):
        r["rank"] = i + 1

    if req.format == "json":
        report = {
            "title": req.title,
            "generated_at": datetime.utcnow().isoformat(),
            "sites": ranked,
            "weights": get_weights(req.weights, req.preset),
        }
        return JSONResponse(report)
    elif req.format == "excel":
        import pandas as pd
        import io
        
        flat_data = []
        for site in ranked:
            row = {
                "Rank": site.get("rank"),
                "Score": round(site.get("composite_score", 0), 1),
                "Grade": site.get("grade"),
                "Latitude": round(site.get("lat", 0), 6),
                "Longitude": round(site.get("lng", 0), 6),
            }
            for sub in site.get("sub_scores", []):
                layer = sub.get("layer", "Unknown").capitalize()
                row[f"{layer} Weight"] = f"{int(sub.get('weight', 0)*100)}%"
                row[f"{layer} Raw Score"] = sub.get("score")
                row[f"{layer} Weighted Score"] = sub.get("weighted_score")
            
            flat_data.append(row)
            
        df = pd.DataFrame(flat_data)
        excel_buffer = io.BytesIO()
        
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Site Reporting')
            workbook = writer.book
            worksheet = writer.sheets['Site Reporting']
            
            from openpyxl.drawing.image import Image as OpenpyxlImage
            
            # Overall Comparison Bar Chart
            if len(ranked) >= 2:
                comp_chart_buf = _generate_comparison_chart(ranked)
                if comp_chart_buf:
                    img = OpenpyxlImage(comp_chart_buf)
                    img.width = 500
                    img.height = 350
                    worksheet.add_image(img, 'I2')
                    
            # Individual Score Pie Charts for up to top 3 sites
            for idx, site in enumerate(ranked[:3]):
                pie_buf = _generate_breakdown_pie_chart(site.get("sub_scores", []))
                if pie_buf:
                    img = OpenpyxlImage(pie_buf)
                    img.width = 300
                    img.height = 300
                    cell = f'Q{2 + (idx * 16)}'
                    worksheet.add_image(img, cell)
                    
        excel_buffer.seek(0)
        
        return StreamingResponse(
            excel_buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=site_report.xlsx"},
        )
    else:
        # Generate PDF
        pdf_buffer = _generate_pdf_report(req.title, ranked, req.weights, req.preset)
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=site_report.pdf"},
        )


import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def _generate_comparison_chart(sites):
    if len(sites) < 2:
        return None
    plt.figure(figsize=(6, 4))
    # Reverse to keep Rank 1 at the top if horizontal, or just normal if vertical
    site_names = [f"Site {s.get('rank', i+1)}" for i, s in enumerate(sites)]
    scores = [s.get('composite_score', 0) for s in sites]
    colors = ['#1a237e' if i == 0 else '#5c6bc0' for i in range(len(sites))]
    
    plt.bar(site_names, scores, color=colors)
    plt.title('Site Score Comparison')
    plt.ylabel('Composite Score')
    plt.ylim(0, max(100, max(scores) * 1.1) if scores else 100)
    plt.tight_layout()
    
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=100)
    plt.close()
    img_buffer.seek(0)
    return img_buffer

def _generate_breakdown_pie_chart(sub_scores):
    labels = []
    sizes = []
    for sub in sub_scores:
        w = sub.get("weighted_score", 0)
        if w > 0:
            labels.append(sub.get("layer", "Unknown").capitalize())
            sizes.append(w)
            
    if not sizes:
        return None
        
    plt.figure(figsize=(4, 4))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=['#4fc3f7', '#ff8a65', '#ba68c8', '#81c784', '#e57373'])
    plt.title('Score Impact Allocation')
    plt.tight_layout()
    
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=80)
    plt.close()
    img_buffer.seek(0)
    return img_buffer

def _generate_pdf_report(title, sites, weights, preset):
    """Generate a PDF report using reportlab."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import inch, cm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*cm, bottomMargin=1*cm)
        styles = getSampleStyleSheet()
        elements = []

        # Title
        title_style = ParagraphStyle(
            'CustomTitle', parent=styles['Title'],
            fontSize=20, spaceAfter=20,
            textColor=colors.HexColor("#1a237e"),
        )
        elements.append(Paragraph(title, title_style))
        elements.append(Paragraph(
            f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            styles['Normal']
        ))
        elements.append(Spacer(1, 20))

        # Sites summary table
        site_data = [["Rank", "Location", "Score", "Grade"]]
        for site in sites:
            lat = site.get('lat', 0)
            lng = site.get('lng', 0)
            score = site.get('composite_score', 0)
            grade = site.get('grade', '-')
            site_data.append([
                str(site.get("rank", "-")),
                f"({lat:.4f}, {lng:.4f})",
                f"{score:.1f}",
                grade,
            ])

        site_table = Table(site_data, colWidths=[0.8*inch, 2.5*inch, 1*inch, 0.8*inch])
        site_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1a237e")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
        ]))
        elements.append(Paragraph("Site Rankings", styles['Heading2']))
        elements.append(site_table)
        elements.append(Spacer(1, 20))

        if len(sites) >= 2:
            comp_chart_buf = _generate_comparison_chart(sites)
            if comp_chart_buf:
                elements.append(RLImage(comp_chart_buf, width=5*inch, height=3.3*inch))
                elements.append(Spacer(1, 20))

        # Detailed breakdown for each site
        for site in sites:
            lat = site.get('lat', 0)
            lng = site.get('lng', 0)
            score = site.get('composite_score', 0)
            grade = site.get('grade', '-')

            elements.append(Paragraph(
                f"Site #{site.get('rank', '?')}: ({lat:.4f}, {lng:.4f}) — "
                f"Score: {score:.1f} ({grade})",
                styles['Heading3']
            ))

            # Score breakdown table with per-site weights
            sub_scores = site.get("sub_scores", [])
            breakdown_data = [["Layer", "Score", "Weight", "Weighted"]]
            for sub in sub_scores:
                layer_name = sub.get("layer", "unknown").title()
                layer_score = sub.get("score", 0)
                layer_weight = sub.get("weight", 0)
                weighted = sub.get("weighted_score", 0)
                breakdown_data.append([
                    layer_name,
                    f"{layer_score:.1f}",
                    f"{layer_weight:.0%}",
                    f"{weighted:.1f}",
                ])

            if len(breakdown_data) > 1:
                bd_table = Table(breakdown_data, colWidths=[2*inch, 1*inch, 1*inch, 1*inch])
                bd_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#455a64")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#eceff1")]),
                ]))
                elements.append(bd_table)
                
                # Add Pie Chart right below the breakdown
                pie_buf = _generate_breakdown_pie_chart(sub_scores)
                if pie_buf:
                    elements.append(Spacer(1, 10))
                    elements.append(RLImage(pie_buf, width=3*inch, height=3*inch))

            # Key details from each layer
            details_text = []
            for sub in sub_scores:
                details = sub.get("details", {})
                layer = sub.get("layer", "")
                if layer == "demographics":
                    pop = details.get("population_nearby", details.get("total_population", "N/A"))
                    income = details.get("avg_income", details.get("median_income", "N/A"))
                    details_text.append(f"Population: {pop:,}" if isinstance(pop, (int, float)) else f"Population: {pop}")
                    details_text.append(f"Avg Income: ₹{income:,.0f}" if isinstance(income, (int, float)) else f"Avg Income: {income}")
                elif layer == "transportation":
                    roads = details.get("roads_nearby", details.get("roads", "N/A"))
                    transit = details.get("transit_stops", details.get("transit", "N/A"))
                    details_text.append(f"Roads Nearby: {roads}, Transit Stops: {transit}")
                elif layer == "poi":
                    comp = details.get("competitors", "N/A")
                    anchor = details.get("anchors", "N/A")
                    details_text.append(f"Competitors: {comp}, Anchors: {anchor}")
                elif layer == "environmental":
                    aqi = details.get("avg_aqi", details.get("aqi", "N/A"))
                    flood = details.get("flood_risk", "N/A")
                    quake = details.get("earthquake_risk", details.get("quake", "N/A"))
                    details_text.append(f"AQI: {aqi}, Flood Risk: {flood}, Earthquake: {quake}")

            if details_text:
                elements.append(Spacer(1, 5))
                detail_style = ParagraphStyle(
                    'DetailStyle', parent=styles['Normal'],
                    fontSize=8, textColor=colors.HexColor("#546e7a"),
                    spaceAfter=2,
                )
                for dt in details_text:
                    elements.append(Paragraph(f"    {dt}", detail_style))

            # Threshold violations
            violations = site.get("threshold_violations", [])
            if violations:
                elements.append(Spacer(1, 5))
                warn_style = ParagraphStyle(
                    'WarnStyle', parent=styles['Normal'],
                    fontSize=9, textColor=colors.HexColor("#e65100"),
                )
                for v in violations:
                    elements.append(Paragraph(f"⚠ {v}", warn_style))

            elements.append(Spacer(1, 15))

        doc.build(elements)
        buffer.seek(0)
        return buffer

    except ImportError:
        # Fallback: return JSON if reportlab not installed
        fallback = json.dumps({
            "error": "reportlab not installed, returning JSON",
            "title": title,
            "sites": sites,
        }, indent=2, default=str)
        return io.BytesIO(fallback.encode())


# ─── Config Endpoints ────────────────────────────────────────────────────────

@app.get("/api/presets")
async def get_presets():
    """Get available use-case weight presets."""
    return {"presets": WEIGHT_PRESETS}


@app.get("/api/config")
async def get_config():
    """Get application configuration."""
    return {
        "bounds": GUJARAT_BOUNDS,
        "cities": GUJARAT_CITIES,
        "default_center": {"lat": 22.3, "lng": 72.0},
        "default_zoom": 7,
    }


# ─── Smart AI Search ─────────────────────────────────────────────────────────

import random as _rand

# Keyword dictionaries for intent detection
_BUSINESS_KEYWORDS = {
    "retail_store": ["retail", "store", "shop", "mall", "supermarket", "grocery", "kirana", "mart", "boutique"],
    "ev_charging": ["ev", "charging", "electric vehicle", "electric car", "charge point", "charger"],
    "warehouse": ["warehouse", "godown", "storage", "distribution", "logistics", "supply chain"],
    "telecom_tower": ["telecom", "tower", "cell tower", "mobile", "network", "5g", "4g", "signal"],
    "solar_farm": ["solar", "renewable", "energy", "solar farm", "solar panel", "photovoltaic"],
    "cafe": ["cafe", "coffee", "tea", "bakery", "restaurant", "food", "dining", "hotel"],
    "hospital": ["hospital", "clinic", "healthcare", "medical", "pharmacy", "health"],
    "school": ["school", "college", "education", "academy", "university", "institute"],
    "office": ["office", "coworking", "co-working", "it park", "tech park", "commercial"],
}

_INTENT_KEYWORDS = {
    "best": ["best", "top", "ideal", "optimal", "recommended", "good", "great", "perfect", "prime"],
    "low_competition": ["low competition", "less competition", "underserved", "untapped", "gap", "no competition", "unserved"],
    "high_population": ["high population", "dense", "crowded", "populated", "busy", "heavy footfall"],
    "near_highway": ["highway", "near highway", "roadside", "national highway", "nh", "expressway"],
    "high_roi": ["roi", "return", "profit", "revenue", "income", "earning"],
    "safe": ["safe", "low risk", "no flood", "secure", "stable"],
}

def _parse_query(query: str):
    """Parse natural language query into structured intent."""
    q = query.lower().strip()

    # Detect city
    detected_city = None
    for city_name, coords in GUJARAT_CITIES.items():
        if city_name.lower() in q:
            detected_city = {"name": city_name, "lat": coords[0], "lng": coords[1]}
            break

    # Detect business type
    detected_business = None
    detected_preset = None
    for preset_key, keywords in _BUSINESS_KEYWORDS.items():
        for kw in keywords:
            if kw in q:
                detected_business = kw
                # Map to existing preset if available
                if preset_key in WEIGHT_PRESETS:
                    detected_preset = preset_key
                elif preset_key in ("cafe", "restaurant", "food", "hotel"):
                    detected_preset = "retail_store"  # closest match
                elif preset_key in ("hospital", "clinic", "school", "office"):
                    detected_preset = "retail_store"  # general commercial
                break
        if detected_business:
            break

    # Detect intents
    detected_intents = []
    for intent, keywords in _INTENT_KEYWORDS.items():
        for kw in keywords:
            if kw in q:
                detected_intents.append(intent)
                break

    return detected_city, detected_business, detected_preset, detected_intents


def _generate_sample_points(center_lat, center_lng, count=5, spread=0.04):
    """Generate sample analysis points around a city center."""
    points = []
    # Use deterministic offsets around the center for consistent results
    offsets = [
        (0.0, 0.0),        # Center
        (spread, spread),   # NE
        (-spread, spread),  # NW
        (spread, -spread),  # SE
        (-spread, -spread), # SW
        (spread*0.5, 0.0),  # E
        (0.0, spread*0.5),  # N
        (-spread*0.5, 0.0), # W
        (0.0, -spread*0.5), # S
    ]
    for i in range(min(count, len(offsets))):
        lat = center_lat + offsets[i][0]
        lng = center_lng + offsets[i][1]
        points.append((lat, lng))
    return points


def _build_explanation(business, intents, sub_scores):
    """Build a short human-readable explanation from score data."""
    parts = []
    if sub_scores:
        best = max(sub_scores, key=lambda s: s.get("weighted_score", 0))
        parts.append(f"Strong {best.get('layer', 'unknown')} score")
    if "low_competition" in intents:
        parts.append("Low competitive density")
    if "high_population" in intents:
        parts.append("High population density")
    if "near_highway" in intents:
        parts.append("Near major roads")
    if "safe" in intents:
        parts.append("Low environmental risk")
    if not parts:
        parts.append("Well-balanced location")
    return ", ".join(parts[:3])


_ZONE_LABELS = ["Central", "North-East", "North-West", "South-East", "South-West", "East", "North", "West", "South"]

@app.post("/api/smart-search")
async def smart_search(req: SmartSearchRequest):
    """AI-powered smart search: parse natural language → geospatial recommendations."""
    query = req.query
    city, business, preset_key, intents = _parse_query(query)

    # Default city to Ahmedabad if none detected
    if not city:
        city = {"name": "Ahmedabad", "lat": 23.0225, "lng": 72.5714}

    # Build weights based on preset or use current weights
    weights = None
    if preset_key:
        weights = WEIGHT_PRESETS.get(preset_key)
    elif req.current_weights:
        weights = req.current_weights

    # Adjust weights based on intent
    if weights and "low_competition" in intents:
        w = dict(weights)
        w["poi"] = w.get("poi", 0.2) * 1.5  # boost POI weight
        weights = w
    if weights and "near_highway" in intents:
        w = dict(weights)
        w["transportation"] = w.get("transportation", 0.2) * 1.5
        weights = w
    if weights and "safe" in intents:
        w = dict(weights)
        w["environmental"] = w.get("environmental", 0.2) * 1.5
        weights = w

    # Generate sample points around the city
    sample_points = _generate_sample_points(city["lat"], city["lng"], count=7, spread=0.04)

    # Score each point
    results = []
    for i, (lat, lng) in enumerate(sample_points):
        try:
            result = compute_site_score(lat, lng, weights, preset_key, req.radius_km)
            zone_label = _ZONE_LABELS[i] if i < len(_ZONE_LABELS) else f"Zone {i+1}"
            results.append({
                "zone": f"{city['name']} {zone_label}",
                "lat": lat,
                "lng": lng,
                "score": round(result.get("composite_score", 0), 1),
                "grade": result.get("grade", "?"),
                "explanation": _build_explanation(business, intents, result.get("sub_scores", [])),
                "sub_scores": result.get("sub_scores", []),
            })
        except Exception:
            pass

    # Sort by score descending and take top 5
    results.sort(key=lambda r: r["score"], reverse=True)
    top_results = results[:5]

    return {
        "query": query,
        "city": city,
        "business_type": business,
        "preset": preset_key,
        "intents": intents,
        "recommendations": top_results,
        "summary": f"Found {len(top_results)} recommended zones in {city['name']}" +
                   (f" for {business}" if business else ""),
    }


# ─── Health Check ────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    from database import is_postgis_available
    layers = get_layer_summary()
    total_features = sum(l["feature_count"] for l in layers)
    return {
        "status": "healthy",
        "layers_loaded": len(layers),
        "total_features": total_features,
        "spatial_backend": "PostGIS" if is_postgis_available() else "in-memory",
        "timestamp": datetime.utcnow().isoformat(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
