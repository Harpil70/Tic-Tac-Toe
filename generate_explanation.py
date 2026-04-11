"""
Generate a comprehensive PDF explaining the GeoSpatial Site Readiness Analyzer
project — workflow, architecture, algorithms, and concepts.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch, cm, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, ListFlowable, ListItem, HRFlowable
)
from reportlab.platypus.flowables import KeepTogether
import os

# ── Colors ───────────────────────────────────────────────────────
NAVY = colors.HexColor("#0f172a")
DARK_BLUE = colors.HexColor("#1e3a5f")
BLUE = colors.HexColor("#3b82f6")
LIGHT_BLUE = colors.HexColor("#dbeafe")
CYAN = colors.HexColor("#06b6d4")
GREEN = colors.HexColor("#10b981")
AMBER = colors.HexColor("#f59e0b")
RED = colors.HexColor("#ef4444")
PURPLE = colors.HexColor("#8b5cf6")
GRAY = colors.HexColor("#64748b")
LIGHT_GRAY = colors.HexColor("#f1f5f9")
WHITE = colors.white
BG_SECTION = colors.HexColor("#f8fafc")

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "GeoSpatial_Site_Analyzer_Explanation.pdf")

def build_pdf():
    doc = SimpleDocTemplate(
        OUTPUT_PATH,
        pagesize=A4,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm,
        leftMargin=2*cm,
        rightMargin=2*cm,
    )

    styles = getSampleStyleSheet()

    # ── Custom Styles ────────────────────────────────────────────
    title_style = ParagraphStyle(
        "DocTitle", parent=styles["Title"],
        fontSize=26, leading=32, spaceAfter=6,
        textColor=NAVY, fontName="Helvetica-Bold",
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle", parent=styles["Normal"],
        fontSize=13, leading=18, spaceAfter=20,
        textColor=GRAY, fontName="Helvetica",
        alignment=TA_CENTER,
    )

    h1 = ParagraphStyle(
        "H1", parent=styles["Heading1"],
        fontSize=20, leading=26, spaceBefore=24, spaceAfter=10,
        textColor=NAVY, fontName="Helvetica-Bold",
        borderWidth=0, borderPadding=0,
    )

    h2 = ParagraphStyle(
        "H2", parent=styles["Heading2"],
        fontSize=15, leading=20, spaceBefore=16, spaceAfter=8,
        textColor=DARK_BLUE, fontName="Helvetica-Bold",
    )

    h3 = ParagraphStyle(
        "H3", parent=styles["Heading3"],
        fontSize=12, leading=16, spaceBefore=10, spaceAfter=6,
        textColor=BLUE, fontName="Helvetica-Bold",
    )

    body = ParagraphStyle(
        "BodyText2", parent=styles["Normal"],
        fontSize=10.5, leading=15, spaceAfter=8,
        textColor=colors.HexColor("#1e293b"),
        fontName="Helvetica", alignment=TA_JUSTIFY,
    )

    code_style = ParagraphStyle(
        "Code", parent=styles["Code"],
        fontSize=9, leading=12, spaceAfter=6,
        textColor=colors.HexColor("#1e293b"),
        backColor=colors.HexColor("#f1f5f9"),
        fontName="Courier",
        leftIndent=12, rightIndent=12,
        borderWidth=0.5, borderColor=colors.HexColor("#e2e8f0"),
        borderPadding=6,
    )

    bullet_style = ParagraphStyle(
        "BulletText", parent=body,
        leftIndent=20, bulletIndent=8,
        spaceAfter=4,
    )

    note_style = ParagraphStyle(
        "NoteStyle", parent=body,
        fontSize=10, leading=14,
        textColor=DARK_BLUE,
        backColor=LIGHT_BLUE,
        borderWidth=1, borderColor=BLUE,
        borderPadding=8, leftIndent=8, rightIndent=8,
        spaceAfter=10, spaceBefore=6,
    )

    elements = []

    def hr():
        elements.append(Spacer(1, 4))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1")))
        elements.append(Spacer(1, 4))

    def add_table(data, col_widths=None, header_color=NAVY):
        style = TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), header_color),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 9.5),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
            ("TOPPADDING", (0, 1), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ])
        t = Table(data, colWidths=col_widths, repeatRows=1)
        t.setStyle(style)
        elements.append(t)
        elements.append(Spacer(1, 10))

    # ════════════════════════════════════════════════════════════════
    #  COVER / TITLE
    # ════════════════════════════════════════════════════════════════
    elements.append(Spacer(1, 2*cm))
    elements.append(Paragraph("🌍 GeoSpatial Site Readiness Analyzer", title_style))
    elements.append(Paragraph(
        "AI-Powered Location Intelligence for Commercial Real Estate &amp; Infrastructure",
        subtitle_style
    ))
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph("Gujarat, India — Project Documentation", ParagraphStyle(
        "CenterGray", parent=body, alignment=TA_CENTER, textColor=GRAY, fontSize=11
    )))
    elements.append(Spacer(1, 1*cm))

    # Quick summary box
    elements.append(Paragraph(
        "<b>What is this project?</b><br/>"
        "A full-stack web application that evaluates any location in Gujarat for commercial "
        "viability by analyzing 5 geospatial data layers — demographics, transportation, "
        "points of interest, land use, and environmental risk — and computing a composite "
        "site readiness score (0–100) with interactive map visualizations.",
        note_style
    ))
    elements.append(Spacer(1, 0.5*cm))

    # Tech stack table
    add_table(
        [
            ["Component", "Technology", "Purpose"],
            ["Backend", "Python, FastAPI, Uvicorn", "REST API, scoring engine, data processing"],
            ["Frontend", "React 19, Vite 6, Leaflet.js", "Interactive map UI, dark-themed dashboard"],
            ["Spatial Analysis", "H3 (Uber), DBSCAN, Haversine", "Hexagonal binning, clustering, distance"],
            ["Data Format", "GeoJSON", "Standardized geospatial feature encoding"],
            ["PDF Export", "ReportLab", "Professional site readiness reports"],
            ["Routing", "OSRM (OpenStreetMap)", "Drive-time isochrone computation"],
        ],
        col_widths=[2.8*cm, 4.5*cm, 8.5*cm],
        header_color=DARK_BLUE,
    )

    elements.append(PageBreak())

    # ════════════════════════════════════════════════════════════════
    #  TABLE OF CONTENTS
    # ════════════════════════════════════════════════════════════════
    elements.append(Paragraph("Table of Contents", h1))
    toc_items = [
        "1. Problem Statement & Motivation",
        "2. System Architecture",
        "3. Data Layer — Synthetic GeoJSON Generation",
        "4. Scoring Engine — Multi-Criteria Decision Analysis",
        "5. Spatial Algorithms — H3, DBSCAN, Haversine",
        "6. Routing & Isochrone Analysis (OSRM)",
        "7. Frontend — React + Leaflet Interactive Map",
        "8. API Design — FastAPI REST Endpoints",
        "9. PDF Report Generation",
        "10. End-to-End Workflow",
        "11. Key Concepts Glossary",
    ]
    for item in toc_items:
        elements.append(Paragraph(item, ParagraphStyle(
            "TOC", parent=body, leftIndent=16, spaceAfter=4, fontSize=11
        )))
    elements.append(PageBreak())

    # ════════════════════════════════════════════════════════════════
    #  1. PROBLEM STATEMENT
    # ════════════════════════════════════════════════════════════════
    elements.append(Paragraph("1. Problem Statement & Motivation", h1))
    hr()
    elements.append(Paragraph(
        "Selecting optimal locations for new retail stores, warehouses, EV charging stations, "
        "telecom towers, or renewable energy installations requires analyzing dozens of "
        "geospatial factors: population density, road network accessibility, competitor proximity, "
        "land use regulations, environmental risks, and utility infrastructure availability.",
        body
    ))
    elements.append(Paragraph(
        "Currently, this analysis is performed <b>manually</b> by teams of analysts using "
        "disconnected GIS tools, spreadsheets, and gut instinct, leading to <b>months-long "
        "evaluation cycles</b> and suboptimal site selections.",
        body
    ))
    elements.append(Paragraph(
        "Our solution automates this entire process into an interactive, AI-powered web "
        "application that can score any location in seconds, visualize results on an "
        "interactive map, and generate professional PDF reports for stakeholders.",
        body
    ))

    elements.append(Paragraph("Key Capabilities:", h3))
    capabilities = [
        "<b>Multi-Layer Analysis</b>: Ingest 5 distinct geospatial data layers simultaneously",
        "<b>Composite Scoring</b>: Weighted, explainable 0-100 score with grade (A+ to F)",
        "<b>Spatial Clustering</b>: Automatic hot-spot and cold-spot detection using DBSCAN",
        "<b>H3 Heatmap</b>: Uber's hexagonal spatial indexing for consistent area comparison",
        "<b>Isochrone Analysis</b>: Drive-time catchment areas with population estimation",
        "<b>Site Comparison</b>: Side-by-side ranking of multiple candidate sites",
        "<b>PDF Export</b>: Professional report generation with ReportLab",
    ]
    for cap in capabilities:
        elements.append(Paragraph(f"• {cap}", bullet_style))

    elements.append(PageBreak())

    # ════════════════════════════════════════════════════════════════
    #  2. SYSTEM ARCHITECTURE
    # ════════════════════════════════════════════════════════════════
    elements.append(Paragraph("2. System Architecture", h1))
    hr()
    elements.append(Paragraph(
        "The application follows a <b>client-server architecture</b> with a clear separation "
        "between the React frontend and the FastAPI backend, communicating via REST API calls "
        "proxied through the Vite development server.",
        body
    ))

    elements.append(Paragraph("Architecture Components:", h2))
    add_table(
        [
            ["Layer", "Technology", "Responsibility"],
            ["Presentation", "React 19 + Leaflet.js", "Interactive map, sidebar controls, score panels"],
            ["API Gateway", "Vite Dev Proxy", "Routes /api/* requests to backend (port 8000)"],
            ["Application", "FastAPI (Python)", "Business logic, scoring, clustering, export"],
            ["Data Access", "GeoPandas + In-Memory", "Spatial queries on GeoJSON datasets"],
            ["Spatial Index", "H3 Hexagonal Grid", "Uniform area partitioning for heatmaps"],
            ["External Service", "OSRM API", "Real road-network routing for isochrones"],
        ],
        col_widths=[2.5*cm, 3.8*cm, 9.5*cm],
    )

    elements.append(Paragraph("Data Flow:", h2))
    flow_steps = [
        "<b>User clicks on map</b> → Leaflet captures (lat, lng) coordinates",
        "<b>Frontend sends POST /api/score</b> → {lat, lng, weights, preset, radius_km}",
        "<b>Vite proxy forwards</b> to http://localhost:8000/api/score",
        "<b>Scoring Engine runs 5 sub-scorers</b> → each queries nearby GeoJSON features",
        "<b>Composite score computed</b> → weighted sum with threshold violation checks",
        "<b>JSON response returned</b> → {composite_score, grade, sub_scores[], violations[]}",
        "<b>ScorePanel renders</b> → SVG gauge, bar charts, layer-specific details",
    ]
    for i, step in enumerate(flow_steps):
        elements.append(Paragraph(f"  {i+1}. {step}", bullet_style))

    elements.append(Spacer(1, 8))
    elements.append(Paragraph("File Structure:", h2))
    structure = [
        ["Directory", "Key Files", "Purpose"],
        ["backend/", "main.py", "FastAPI app with 12 REST endpoints"],
        ["backend/", "config.py", "Gujarat cities, weights, scoring thresholds"],
        ["backend/data/", "generate_data.py", "Synthetic GeoJSON generator for Gujarat"],
        ["backend/services/", "scoring.py", "5 sub-scorers + composite score engine"],
        ["backend/services/", "clustering.py", "H3 heatmap + DBSCAN clustering"],
        ["backend/services/", "routing.py", "OSRM isochrone generation"],
        ["backend/services/", "data_ingestion.py", "GeoJSON loading + radius queries"],
        ["backend/utils/", "spatial.py", "Haversine distance, decay functions"],
        ["frontend/src/", "App.jsx", "Main state orchestrator"],
        ["frontend/src/components/", "MapView.jsx", "Leaflet map with 5 layer renderers"],
        ["frontend/src/components/", "ScorePanel.jsx", "SVG gauge + sub-score breakdown"],
        ["frontend/src/components/", "Sidebar.jsx", "Layer toggles, weight sliders"],
        ["frontend/src/components/", "ComparePanel.jsx", "Side-by-side site comparison"],
        ["frontend/src/services/", "api.js", "Axios HTTP client for all endpoints"],
    ]
    add_table(structure, col_widths=[2.8*cm, 3.5*cm, 9.5*cm])

    elements.append(PageBreak())

    # ════════════════════════════════════════════════════════════════
    #  3. DATA LAYER
    # ════════════════════════════════════════════════════════════════
    elements.append(Paragraph("3. Data Layer — Synthetic GeoJSON Generation", h1))
    hr()
    elements.append(Paragraph(
        "The system uses <b>synthetic but realistic</b> GeoJSON data generated for Gujarat, India. "
        "The data generator creates features around 12 major Gujarat cities (Ahmedabad, Surat, "
        "Vadodara, Rajkot, Gandhinagar, Bhavnagar, Jamnagar, Junagadh, Anand, Nadiad, Mehsana, "
        "and Bharuch) with properties that mirror real-world distributions.",
        body
    ))

    elements.append(Paragraph("The 5 Geospatial Data Layers:", h2))

    # Demographics
    elements.append(Paragraph("3.1 Demographics Layer", h3))
    elements.append(Paragraph(
        "Contains census-tract-like polygons with population data. Each feature is a circular "
        "polygon (approximated) representing a neighborhood with properties including: "
        "<b>population</b> (5,000–500,000), <b>population_density</b> (per km²), "
        "<b>median_income</b> (₹8,000–₹80,000/month), <b>median_age</b>, and <b>literacy_rate</b>.",
        body
    ))
    elements.append(Paragraph(
        "Concept — <b>GeoJSON Polygon</b>: A closed shape defined by an array of [longitude, latitude] "
        "coordinate pairs. The first and last coordinate must be identical to close the ring.",
        note_style
    ))

    # Transportation
    elements.append(Paragraph("3.2 Transportation Layer", h3))
    elements.append(Paragraph(
        "Includes two geometry types: <b>LineString</b> features for roads (national highways, "
        "state highways, arterials) with properties like <i>lanes</i> and <i>surface_quality</i>, "
        "and <b>Point</b> features for transit stops (bus stations, railway stations, metro) "
        "with <i>daily_ridership</i> data.",
        body
    ))

    # POI
    elements.append(Paragraph("3.3 Points of Interest (POI) Layer", h3))
    elements.append(Paragraph(
        "Point features representing businesses categorized as: <b>competitor</b> (rival stores), "
        "<b>anchor</b> (malls, large stores that attract foot traffic), and <b>complementary</b> "
        "(nearby businesses that benefit each other). Each has a <i>rating</i> and <i>city</i> attribute.",
        body
    ))

    # Land Use
    elements.append(Paragraph("3.4 Land Use & Zoning Layer", h3))
    elements.append(Paragraph(
        "Polygon features representing zoned areas: <b>commercial</b>, <b>residential</b>, "
        "<b>industrial</b>, <b>mixed_use</b>, <b>agricultural</b>, <b>institutional</b>. "
        "Properties include <i>development_status</i> (developed/developing/undeveloped), "
        "<i>building_coverage_ratio</i>, and Gujarat-specific <i>is_gidc</i> flag for "
        "Gujarat Industrial Development Corporation estates.",
        body
    ))

    # Environmental
    elements.append(Paragraph("3.5 Environmental Risk Layer", h3))
    elements.append(Paragraph(
        "Mixed geometry: <b>Polygon</b> features for flood zones (coastal Gujarat, river basins) "
        "and earthquake risk zones (Kutch region), plus <b>Point</b> features for air quality "
        "monitoring stations with <i>aqi_value</i> (Air Quality Index) and <i>severity</i> levels.",
        body
    ))

    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        "Concept — <b>GeoJSON Standard (RFC 7946)</b>: An open standard format for encoding "
        "geographic data structures using JSON. It supports geometry types: Point, LineString, "
        "Polygon, MultiPoint, MultiLineString, MultiPolygon, and GeometryCollection. Each "
        "Feature has a <i>geometry</i> and arbitrary <i>properties</i>.",
        note_style
    ))

    elements.append(PageBreak())

    # ════════════════════════════════════════════════════════════════
    #  4. SCORING ENGINE
    # ════════════════════════════════════════════════════════════════
    elements.append(Paragraph("4. Scoring Engine — Multi-Criteria Decision Analysis", h1))
    hr()
    elements.append(Paragraph(
        "The core of the application is the <b>Scoring Engine</b> — a configurable system that "
        "evaluates any location by computing 5 independent sub-scores and combining them into a "
        "single composite score using a Weighted Linear Combination (WLC) approach.",
        body
    ))

    elements.append(Paragraph("4.1 Scoring Workflow", h2))
    scoring_flow = [
        "Receive target coordinates (lat, lng) and analysis radius (default 5 km)",
        "For each of the 5 layers, run a spatial radius query to find nearby features",
        "Compute a raw sub-score (0–100) for each layer using domain-specific logic",
        "Apply distance decay: closer features have more influence than farther ones",
        "Multiply each sub-score by its configurable weight (sums to 1.0)",
        "Sum weighted scores to get the composite score",
        "Check threshold constraints (min population, max flood risk, etc.)",
        "Apply penalty for each threshold violation (−5 points each)",
        "Assign a letter grade (A+ through F) based on final score",
    ]
    for i, step in enumerate(scoring_flow):
        elements.append(Paragraph(f"  {i+1}. {step}", bullet_style))

    elements.append(Paragraph("4.2 Default Weight Configuration", h2))
    add_table(
        [
            ["Layer", "Weight", "Rationale"],
            ["Demographics", "25%", "Population density and income are primary demand indicators"],
            ["Transportation", "20%", "Highway/transit access affects customer reach"],
            ["Points of Interest", "20%", "Competitive landscape and anchor store proximity"],
            ["Land Use & Zoning", "15%", "Regulatory compliance and development readiness"],
            ["Environmental Risk", "20%", "Flood/earthquake/air quality affect long-term viability"],
        ],
        col_widths=[3.2*cm, 1.5*cm, 11.1*cm],
        header_color=DARK_BLUE,
    )

    elements.append(Paragraph("4.3 Use-Case Presets", h2))
    elements.append(Paragraph(
        "Different business types prioritize different factors. The system supports "
        "<b>weight presets</b> that automatically adjust scoring priorities:",
        body
    ))
    add_table(
        [
            ["Use Case", "Demo", "Trans", "POI", "Land", "Env", "Key Priority"],
            ["Retail Store", "30%", "20%", "25%", "10%", "15%", "Population & competitors"],
            ["EV Charging", "15%", "35%", "15%", "15%", "20%", "Highway access"],
            ["Warehouse", "10%", "30%", "10%", "30%", "20%", "Land & roads"],
            ["Telecom Tower", "25%", "15%", "10%", "20%", "30%", "Coverage & environment"],
            ["Solar Farm", "5%", "15%", "5%", "30%", "45%", "Land & low risk"],
        ],
        col_widths=[2.5*cm, 1.3*cm, 1.3*cm, 1.3*cm, 1.3*cm, 1.3*cm, 6.8*cm],
        header_color=colors.HexColor("#7c3aed"),
    )

    elements.append(Paragraph("4.4 Sub-Score Computation Details", h2))

    # Demographics scorer
    elements.append(Paragraph("Demographics Sub-Score", h3))
    elements.append(Paragraph(
        "Queries census tracts within the radius and computes three components:<br/>"
        "• <b>Population Score (40%)</b>: normalize(total_population, 0, 500000)<br/>"
        "• <b>Density Score (30%)</b>: normalize(avg_density, 0, 30000/km²)<br/>"
        "• <b>Income Score (30%)</b>: normalize(avg_income, ₹8000, ₹80000)<br/>"
        "Each feature's contribution is weighted by an <b>exponential distance decay</b> function.",
        body
    ))

    # Transportation scorer
    elements.append(Paragraph("Transportation Sub-Score", h3))
    elements.append(Paragraph(
        "Components:<br/>"
        "• <b>Highway Score (35%)</b>: Exponential decay from nearest national/state highway<br/>"
        "• <b>Transit Score (30%)</b>: Number of bus/rail/metro stops within radius<br/>"
        "• <b>Road Density (20%)</b>: Count of road features within radius<br/>"
        "• <b>Ridership Score (15%)</b>: Average daily ridership of nearby transit stops",
        body
    ))

    # POI scorer
    elements.append(Paragraph("Points of Interest Sub-Score", h3))
    elements.append(Paragraph(
        "Components:<br/>"
        "• <b>Competitive Density (35%)</b>: Uses a bell-curve formula — some competition is "
        "good (indicates demand), but too much is saturating<br/>"
        "• <b>Anchor Proximity (30%)</b>: Exponential decay from nearest anchor (mall, major store)<br/>"
        "• <b>Complementary Density (35%)</b>: Count of complementary businesses (restaurants, banks)",
        body
    ))

    # Land Use scorer
    elements.append(Paragraph("Land Use & Zoning Sub-Score", h3))
    elements.append(Paragraph(
        "Components:<br/>"
        "• <b>Zone Type Score (40%)</b>: commercial=95, mixed_use=85, residential=55, industrial=30<br/>"
        "• <b>Development Status (25%)</b>: developing=90, developed=80, undeveloped=50<br/>"
        "• <b>Building Coverage (20%)</b>: Optimal around 0.4 (room for new construction)<br/>"
        "• <b>Zone Diversity (15%)</b>: More zone types nearby = more versatile area",
        body
    ))

    # Environmental scorer
    elements.append(Paragraph("Environmental Risk Sub-Score (Inverted)", h3))
    elements.append(Paragraph(
        "This score is <b>inverted</b> — lower risk means higher score:<br/>"
        "• <b>Flood Risk (35%)</b>: Based on severity of nearest flood zone × distance decay<br/>"
        "• <b>Earthquake Risk (35%)</b>: Based on severity of nearest seismic zone × decay<br/>"
        "• <b>Air Quality (30%)</b>: normalize(300 − avg_AQI, 0, 300) — lower AQI is better",
        body
    ))

    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        "Concept — <b>Weighted Linear Combination (WLC)</b>: A Multi-Criteria Decision Analysis "
        "(MCDA) method where the overall score is computed as:<br/>"
        "<font face='Courier' size=10>  S = Σ (w_i × s_i)</font><br/>"
        "where w_i is the weight and s_i is the sub-score for layer i. Weights must sum to 1.0.",
        note_style
    ))

    elements.append(PageBreak())

    # ════════════════════════════════════════════════════════════════
    #  5. SPATIAL ALGORITHMS
    # ════════════════════════════════════════════════════════════════
    elements.append(Paragraph("5. Spatial Algorithms — H3, DBSCAN, Haversine", h1))
    hr()

    elements.append(Paragraph("5.1 Haversine Distance Formula", h2))
    elements.append(Paragraph(
        "Computes the <b>great-circle distance</b> between two points on Earth's surface "
        "given their latitude and longitude. This is more accurate than Euclidean distance "
        "because it accounts for Earth's curvature.",
        body
    ))
    elements.append(Paragraph(
        "<font face='Courier' size=9>"
        "  a = sin²(Δlat/2) + cos(lat₁) × cos(lat₂) × sin²(Δlng/2)<br/>"
        "  c = 2 × atan2(√a, √(1−a))<br/>"
        "  distance = R × c    (R = 6371 km, Earth's radius)</font>",
        code_style
    ))
    elements.append(Paragraph(
        "Used in: Spatial radius queries, distance decay, DBSCAN neighbor search.",
        body
    ))

    elements.append(Paragraph("5.2 Exponential Distance Decay", h2))
    elements.append(Paragraph(
        "Models the idea that closer features have more influence on a location's score. "
        "The decay function is:<br/>"
        "<font face='Courier' size=9>  decay(d) = e^(−λd)</font><br/>"
        "where d is distance (km) and λ is the decay rate (typically 0.2–0.4). At λ=0.3, "
        "a feature 5 km away has ~22% of the influence of a feature at 0 km.",
        body
    ))

    elements.append(Paragraph("5.3 H3 Hexagonal Spatial Index (Uber)", h2))
    elements.append(Paragraph(
        "<b>H3</b> is a hierarchical geospatial indexing system developed by Uber. It "
        "partitions the Earth's surface into hexagonal cells at multiple resolutions. "
        "Hexagons are preferred over squares because:",
        body
    ))
    hex_advantages = [
        "Every neighbor is equidistant (6 neighbors, all same distance)",
        "No orientation bias (squares have diagonal vs. cardinal neighbor asymmetry)",
        "Better approximation of circular search areas",
        "Hierarchical: each parent hex contains ~7 child hexes",
    ]
    for adv in hex_advantages:
        elements.append(Paragraph(f"  • {adv}", bullet_style))

    elements.append(Spacer(1, 4))
    add_table(
        [
            ["Resolution", "Hex Area", "Edge Length", "Use in This Project"],
            ["4", "~1,770 km²", "~22.6 km", "State-level overview"],
            ["5", "~253 km²", "~8.5 km", "Regional analysis"],
            ["7 (default)", "~5.16 km²", "~1.22 km", "City-level heatmaps"],
            ["9", "~0.105 km²", "~174 m", "Street-level analysis"],
        ],
        col_widths=[2.2*cm, 2.5*cm, 2.5*cm, 8.6*cm],
        header_color=colors.HexColor("#0891b2"),
    )

    elements.append(Paragraph(
        "Key H3 functions used (v4 API):<br/>"
        "• <font face='Courier'>latlng_to_cell(lat, lng, resolution)</font> → hex ID<br/>"
        "• <font face='Courier'>cell_to_latlng(hex_id)</font> → center coordinates<br/>"
        "• <font face='Courier'>cell_to_boundary(hex_id)</font> → polygon vertices",
        body
    ))

    elements.append(Paragraph("5.4 DBSCAN Clustering Algorithm", h2))
    elements.append(Paragraph(
        "<b>DBSCAN (Density-Based Spatial Clustering of Applications with Noise)</b> "
        "groups nearby high-scoring hexagons into \"hot spots\" and low-scoring hexagons "
        "into \"cold spots\" (underserved areas). Unlike K-Means, DBSCAN:",
        body
    ))
    dbscan_points = [
        "Does NOT require specifying the number of clusters in advance",
        "Can find clusters of arbitrary shape",
        "Identifies noise points (outliers that don't belong to any cluster)",
        "Uses two parameters: <b>eps</b> (max neighbor distance) and <b>min_samples</b> (min cluster size)",
    ]
    for pt in dbscan_points:
        elements.append(Paragraph(f"  • {pt}", bullet_style))

    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        "Algorithm steps:<br/>"
        "1. For each unvisited hexagon, find all hexagons within <i>eps_km</i> distance<br/>"
        "2. If ≥ <i>min_samples</i> neighbors found, start a new cluster<br/>"
        "3. Expand: add each neighbor's neighbors if they also meet the min_samples threshold<br/>"
        "4. Continue until no more points can be added to the cluster<br/>"
        "5. Unvisited points remaining are noise",
        body
    ))

    elements.append(Paragraph("5.5 Competitive Density Score (Bell Curve)", h2))
    elements.append(Paragraph(
        "For retail site selection, some competition is actually desirable (it validates demand), "
        "but too many competitors saturate the market. The scoring uses a bell-curve function:<br/>"
        "<font face='Courier' size=9>  if count &lt; optimal_min: score = count / optimal_min<br/>"
        "  if optimal_min ≤ count ≤ optimal_max: score = 1.0 (ideal)<br/>"
        "  if count &gt; optimal_max: score = max(0, 1 − (count−optimal_max)/(optimal_max×2))</font>",
        body
    ))

    elements.append(PageBreak())

    # ════════════════════════════════════════════════════════════════
    #  6. ROUTING & ISOCHRONE
    # ════════════════════════════════════════════════════════════════
    elements.append(Paragraph("6. Routing & Isochrone Analysis", h1))
    hr()
    elements.append(Paragraph(
        "An <b>isochrone</b> is a polygon on a map that shows all areas reachable within a "
        "given travel time from a point. Unlike a simple radius circle, isochrones follow the "
        "actual road network — areas with highways are reachable faster than areas with only "
        "narrow roads.",
        body
    ))

    elements.append(Paragraph("How Isochrones Are Computed:", h2))
    iso_steps = [
        "User clicks 'Analyze' in the drive-time catchment section",
        "Frontend sends POST /api/isochrone with lat, lng, mode (driving), intervals [10, 20, 30 min]",
        "Backend sends requests to the OSRM (Open Source Routing Machine) public API",
        "OSRM returns route geometries for sample directions from the origin",
        "Backend approximates the isochrone polygon from route endpoints",
        "For each ring, population within the catchment area is estimated from demographics data",
        "Result: nested polygons (10-min, 20-min, 30-min rings) with population counts",
    ]
    for i, step in enumerate(iso_steps):
        elements.append(Paragraph(f"  {i+1}. {step}", bullet_style))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "Concept — <b>OSRM (Open Source Routing Machine)</b>: A high-performance routing engine "
        "that uses OpenStreetMap data to compute shortest/fastest paths on real road networks. "
        "It supports car, bicycle, and foot routing profiles. The public demo server is used "
        "for development; production would require a self-hosted instance.",
        note_style
    ))

    elements.append(Paragraph("Catchment Population Estimation:", h2))
    elements.append(Paragraph(
        "For each isochrone ring, the system queries the demographics layer for census tracts "
        "whose centroids fall within the polygon, then sums their population. This tells "
        "stakeholders: <i>'Within a 10-minute drive, 378,000 potential customers reside.'</i>",
        body
    ))

    elements.append(PageBreak())

    # ════════════════════════════════════════════════════════════════
    #  7. FRONTEND
    # ════════════════════════════════════════════════════════════════
    elements.append(Paragraph("7. Frontend — React + Leaflet Interactive Map", h1))
    hr()

    elements.append(Paragraph("7.1 Design System", h2))
    elements.append(Paragraph(
        "The UI uses a <b>premium dark theme</b> with glassmorphism effects (semi-transparent "
        "backgrounds with backdrop blur). Key design tokens:",
        body
    ))
    add_table(
        [
            ["Token", "Value", "Usage"],
            ["--bg-primary", "#0a0e1a", "Main background"],
            ["--bg-glass", "rgba(17,24,39, 0.65)", "Glassmorphism panels"],
            ["--accent-blue", "#3b82f6", "Primary interactive elements"],
            ["--accent-emerald", "#34d399", "Success / good scores"],
            ["--accent-rose", "#fb7185", "Danger / poor scores"],
            ["--font-main", "Inter", "UI text (Google Fonts)"],
            ["--font-mono", "JetBrains Mono", "Coordinates, scores"],
        ],
        col_widths=[3*cm, 4*cm, 8.8*cm],
        header_color=colors.HexColor("#4f46e5"),
    )

    elements.append(Paragraph("7.2 Component Architecture", h2))
    components = [
        ["Component", "Responsibility", "Key Features"],
        ["App.jsx", "State orchestrator", "Manages all state: layers, scores, compare, heatmap, clusters"],
        ["Sidebar", "Controls panel", "Layer toggles, weight sliders, radius input, action buttons"],
        ["MapView", "Interactive map", "Leaflet with 5 layers, heatmap hexagons, cluster markers, isochrones"],
        ["ScorePanel", "Score display", "Animated SVG gauge, 5 sub-score bars, violation warnings"],
        ["ComparePanel", "Site comparison", "Ranked cards with mini bar charts"],
    ]
    add_table(components, col_widths=[2.5*cm, 3.5*cm, 9.8*cm])

    elements.append(Paragraph("7.3 Leaflet Map Layers", h2))
    elements.append(Paragraph(
        "The Leaflet map renders multiple overlapping layers:<br/>"
        "• <b>Base tiles</b>: CartoDB Dark Matter (dark theme compatible)<br/>"
        "• <b>Demographics</b>: Blue polygons with opacity based on population density<br/>"
        "• <b>Transportation</b>: Orange lines for roads, points for transit stops<br/>"
        "• <b>POI</b>: Color-coded circles (red=competitor, yellow=anchor, green=complementary)<br/>"
        "• <b>Land Use</b>: Zone polygons colored by type (yellow=commercial, blue=residential)<br/>"
        "• <b>Environmental</b>: Risk zone polygons with dashed borders for flood areas<br/>"
        "• <b>Heatmap</b>: H3 hexagon polygons colored by score (green→yellow→red)<br/>"
        "• <b>Clusters</b>: Large circles for hot spots (green) and cold spots (blue)",
        body
    ))

    elements.append(Paragraph("7.4 SVG Score Gauge", h2))
    elements.append(Paragraph(
        "The score panel features an animated circular gauge built with SVG:<br/>"
        "• Two concentric circles: background track and progress arc<br/>"
        "• Progress is controlled via <font face='Courier'>stroke-dashoffset</font> CSS property<br/>"
        "• Color transitions: Red (0-24) → Orange (25-39) → Yellow (40-59) → "
        "Light Green (60-79) → Green (80-100)<br/>"
        "• Animated with CSS transition for smooth arc drawing on load",
        body
    ))

    elements.append(PageBreak())

    # ════════════════════════════════════════════════════════════════
    #  8. API DESIGN
    # ════════════════════════════════════════════════════════════════
    elements.append(Paragraph("8. API Design — FastAPI REST Endpoints", h1))
    hr()

    add_table(
        [
            ["Method", "Endpoint", "Description"],
            ["GET", "/api/health", "Server health check with layer counts"],
            ["GET", "/api/layers", "List all available layers with metadata"],
            ["GET", "/api/layers/{name}", "Fetch GeoJSON data for a specific layer"],
            ["POST", "/api/score", "Compute site readiness score for a point"],
            ["POST", "/api/score/polygon", "Score all hexagons within a drawn polygon"],
            ["GET", "/api/h3/heatmap", "Generate H3 hexagonal heatmap of scores"],
            ["POST", "/api/cluster", "Run DBSCAN clustering for hot/cold spots"],
            ["POST", "/api/isochrone", "Compute drive-time isochrone rings"],
            ["POST", "/api/compare", "Compare multiple candidate sites"],
            ["POST", "/api/export", "Generate PDF or JSON report"],
            ["GET", "/api/presets", "Get available use-case weight presets"],
            ["GET", "/api/config", "Get application configuration"],
        ],
        col_widths=[1.5*cm, 4*cm, 10.3*cm],
    )

    elements.append(Paragraph("Score Request/Response Example:", h2))
    elements.append(Paragraph(
        "<font face='Courier' size=9>"
        "// Request: POST /api/score<br/>"
        "{ \"lat\": 23.0225, \"lng\": 72.5714,<br/>"
        "  \"weights\": {\"demographics\":0.25, \"transportation\":0.20, ...},<br/>"
        "  \"preset\": \"retail_store\", \"radius_km\": 5 }<br/><br/>"
        "// Response:<br/>"
        "{ \"composite_score\": 51.7, \"grade\": \"C+\",<br/>"
        "  \"sub_scores\": [<br/>"
        "    {\"layer\":\"demographics\", \"score\":56.6, \"weight\":0.25, \"weighted_score\":14.1,<br/>"
        "     \"details\":{\"population_nearby\":290407, \"avg_income\":75926}},<br/>"
        "    {\"layer\":\"transportation\", \"score\":14.4, ...}, ... ],<br/>"
        "  \"threshold_violations\": [] }</font>",
        code_style
    ))

    elements.append(PageBreak())

    # ════════════════════════════════════════════════════════════════
    #  9. PDF REPORT
    # ════════════════════════════════════════════════════════════════
    elements.append(Paragraph("9. PDF Report Generation", h1))
    hr()
    elements.append(Paragraph(
        "The system generates professional PDF reports using Python's <b>ReportLab</b> library. "
        "When a user clicks 'Export Report (PDF),' the backend scores all pinned sites, ranks "
        "them, and builds a multi-page PDF with:",
        body
    ))
    pdf_sections = [
        "<b>Title page</b> with generation timestamp",
        "<b>Weights table</b> showing the scoring configuration used",
        "<b>Rankings table</b> with all sites sorted by composite score",
        "<b>Detailed breakdown</b> for each site: layer scores, weights, weighted contributions",
        "<b>Threshold violations</b> highlighted with warning symbols",
    ]
    for sec in pdf_sections:
        elements.append(Paragraph(f"  • {sec}", bullet_style))

    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        "The PDF is streamed directly to the browser as a download via FastAPI's "
        "<font face='Courier'>StreamingResponse</font> with <font face='Courier'>"
        "media_type='application/pdf'</font>.",
        body
    ))

    elements.append(PageBreak())

    # ════════════════════════════════════════════════════════════════
    #  10. END-TO-END WORKFLOW
    # ════════════════════════════════════════════════════════════════
    elements.append(Paragraph("10. End-to-End Workflow", h1))
    hr()

    elements.append(Paragraph("Scenario: Evaluating a Retail Store Location Near Ahmedabad", h2))

    e2e_steps = [
        ("<b>Launch</b>", "Start backend (uvicorn) and frontend (npm run dev). "
         "Backend loads 1,253 synthetic GeoJSON features into memory."),

        ("<b>Explore Data</b>", "Toggle layer toggles to visualize demographics (blue zones), "
         "transportation (orange roads), POIs (colored dots), land use, and environmental risks across Gujarat."),

        ("<b>Score a Site</b>", "Click near Ahmedabad on the map. The system queries all features "
         "within 5 km, applies distance decay, computes 5 sub-scores, and returns a composite "
         "score (e.g., 51.7 / 100, Grade C+)."),

        ("<b>Analyze Breakdown</b>", "The Score Panel shows demographics=56.6 (good population density), "
         "transportation=14.4 (far from highway), POI=41.3 (moderate competition), "
         "land_use=58.9 (mixed-use zone), environmental=87.8 (low risk)."),

        ("<b>Catchment Analysis</b>", "Click 'Analyze' in Drive-Time Catchment. The system computes "
         "10/20/30-minute drive-time isochrones via OSRM, showing 378K people within 10 min."),

        ("<b>Generate Heatmap</b>", "Click 'Generate H3 Heatmap' to see color-coded hexagons across "
         "Gujarat. Green hexagons indicate high-potential areas; red indicates poor candidates."),

        ("<b>Find Hot Spots</b>", "Click 'Detect Hot Spots' to run DBSCAN clustering. The system "
         "identifies clusters of high-scoring hexagons (investment opportunities) and low-scoring "
         "clusters (underserved areas)."),

        ("<b>Compare Sites</b>", "Enable compare mode, click 3-4 candidate locations. "
         "The Compare Panel shows ranked cards with side-by-side bar charts."),

        ("<b>Export Report</b>", "Click 'Export Report (PDF)' to download a professional report "
         "with all site data, rankings, and score breakdowns."),
    ]
    for step_title, step_desc in e2e_steps:
        elements.append(Paragraph(f"{step_title}: {step_desc}", body))
        elements.append(Spacer(1, 4))

    elements.append(PageBreak())

    # ════════════════════════════════════════════════════════════════
    #  11. GLOSSARY
    # ════════════════════════════════════════════════════════════════
    elements.append(Paragraph("11. Key Concepts Glossary", h1))
    hr()

    glossary = [
        ["Term", "Definition"],
        ["GeoJSON", "Open standard format (RFC 7946) for encoding geographic features using JSON"],
        ["Haversine Formula", "Calculates great-circle distance between two lat/lng points on a sphere"],
        ["Distance Decay", "Mathematical function where influence decreases exponentially with distance"],
        ["H3", "Uber's hierarchical hexagonal spatial indexing system for the globe"],
        ["DBSCAN", "Density-based clustering algorithm that finds arbitrarily-shaped clusters"],
        ["Isochrone", "A polygon showing all points reachable within a given travel time"],
        ["OSRM", "Open Source Routing Machine — routing engine using OpenStreetMap road data"],
        ["WLC", "Weighted Linear Combination — MCDA method: S = Σ(w_i × s_i)"],
        ["Leaflet", "Open-source JavaScript library for interactive maps"],
        ["FastAPI", "Modern high-performance Python web framework for building APIs"],
        ["Glassmorphism", "UI design trend using frosted-glass effect (blur + transparency)"],
        ["GeoJSON Feature", "A geographic object with geometry (shape) and properties (attributes)"],
        ["Spatial Query", "Database query that filters features based on geographic criteria (e.g., within radius)"],
        ["Composite Score", "A single number (0-100) combining multiple weighted sub-scores"],
        ["Threshold Constraint", "Minimum/maximum values that trigger penalties if violated"],
        ["Heat Map", "Visualization where areas are colored by intensity of a metric (score)"],
        ["Hot Spot", "A cluster of adjacent areas with consistently high scores"],
        ["Cold Spot", "A cluster of adjacent areas with consistently low scores (underserved)"],
        ["Catchment Area", "The geographic region from which a business draws its customers"],
        ["CORS", "Cross-Origin Resource Sharing — browser security policy for cross-domain requests"],
        ["Vite", "Next-generation frontend build tool with instant hot module replacement (HMR)"],
        ["ReportLab", "Python library for programmatic PDF document generation"],
    ]
    add_table(glossary, col_widths=[3.5*cm, 12.3*cm])

    elements.append(Spacer(1, 1*cm))
    elements.append(Paragraph(
        "— End of Documentation —",
        ParagraphStyle("EndMarker", parent=body, alignment=TA_CENTER, textColor=GRAY, fontSize=11)
    ))

    # ── Build ────────────────────────────────────────────────────
    doc.build(elements)
    print(f"\n✅ PDF generated successfully: {OUTPUT_PATH}")
    print(f"   File size: {os.path.getsize(OUTPUT_PATH) / 1024:.1f} KB")

if __name__ == "__main__":
    build_pdf()
