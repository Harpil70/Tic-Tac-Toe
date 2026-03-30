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
    results = []
    for site in req.sites:
        result = compute_site_score(
            lat=site.lat,
            lng=site.lng,
            weights=req.weights,
            preset=req.preset,
        )
        results.append(result)

    ranked = sorted(results, key=lambda r: r["composite_score"], reverse=True)
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

        # Weights used
        w = get_weights(weights, preset)
        weight_data = [["Layer", "Weight"]]
        for layer, weight in w.items():
            weight_data.append([layer.title(), f"{weight:.0%}"])

        weight_table = Table(weight_data, colWidths=[3*inch, 1.5*inch])
        weight_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1a237e")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
        ]))
        elements.append(Paragraph("Scoring Weights", styles['Heading2']))
        elements.append(weight_table)
        elements.append(Spacer(1, 20))

        # Sites summary table
        site_data = [["Rank", "Location", "Score", "Grade"]]
        for site in sites:
            site_data.append([
                str(site.get("rank", "-")),
                f"({site['lat']:.4f}, {site['lng']:.4f})",
                f"{site['composite_score']:.1f}",
                site["grade"],
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
            elements.append(Paragraph(
                f"Site #{site.get('rank', '?')}: ({site['lat']:.4f}, {site['lng']:.4f}) — "
                f"Score: {site['composite_score']:.1f} ({site['grade']})",
                styles['Heading3']
            ))

            breakdown_data = [["Layer", "Score", "Weight", "Weighted"]]
            for sub in site.get("sub_scores", []):
                breakdown_data.append([
                    sub["layer"].title(),
                    f"{sub['score']:.1f}",
                    f"{sub['weight']:.0%}",
                    f"{sub['weighted_score']:.1f}",
                ])

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

            # Threshold violations
            violations = site.get("threshold_violations", [])
            if violations:
                elements.append(Spacer(1, 5))
                for v in violations:
                    elements.append(Paragraph(f"⚠ {v}", styles['Normal']))

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
        }, indent=2)
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
