"""
GeoSpatial Site Readiness Analyzer - FastAPI Backend
AI-Powered Location Intelligence for Commercial Real Estate and Infrastructure
"""
import io
import json
from datetime import datetime
from typing import Optional, Dict

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

from config import WEIGHT_PRESETS, GUJARAT_BOUNDS, GUJARAT_CITIES
from models.schemas import (
    ScoreRequest, PolygonScoreRequest, CompareRequest,
    ClusterRequest, IsochroneRequest, ExportRequest, HeatmapRequest
)
from services.data_ingestion import load_all_layers, get_layer, get_layer_summary, get_all_layers
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
        resolution=req.h3_resolution,
        weights=req.weights,
        preset=req.preset,
        max_hexagons=300,
    )
    clusters = detect_clusters(heatmap, req.min_samples, req.eps_km)
    return clusters


@app.get("/api/h3/heatmap")
async def get_heatmap(
    resolution: int = Query(7, ge=4, le=9),
    min_lat: Optional[float] = None,
    max_lat: Optional[float] = None,
    min_lng: Optional[float] = None,
    max_lng: Optional[float] = None,
    preset: Optional[str] = None,
):
    """Get H3 hexagonal heatmap of scores."""
    bounds = None
    if all(v is not None for v in [min_lat, max_lat, min_lng, max_lng]):
        bounds = {
            "min_lat": min_lat,
            "max_lat": max_lat,
            "min_lng": min_lng,
            "max_lng": max_lng,
        }

    heatmap = compute_heatmap(bounds, resolution, preset=preset, max_hexagons=400)
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
    else:
        # Generate PDF
        pdf_buffer = _generate_pdf_report(req.title, ranked, req.weights, req.preset)
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=site_report.pdf"},
        )


def _generate_pdf_report(title, sites, weights, preset):
    """Generate a PDF report using reportlab."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import inch, cm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
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


# ─── Health Check ────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    layers = get_layer_summary()
    total_features = sum(l["feature_count"] for l in layers)
    return {
        "status": "healthy",
        "layers_loaded": len(layers),
        "total_features": total_features,
        "timestamp": datetime.utcnow().isoformat(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
