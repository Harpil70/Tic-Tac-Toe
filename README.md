# 🌍 GeoSpatial Site Readiness Analyzer

A comprehensive location-intelligence platform built to evaluate, score, and compare geographic zones based on multifaceted data layers. Designed to help retail, commercial, and industrial businesses find the optimal locations for their next operations.

![Project Preview](https://img.shields.io/badge/Status-Hackathon_Ready-brightgreen)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)
![React](https://img.shields.io/badge/Frontend-React-61DAFB)

## ✨ Core Features

*   **Intelligent Scoring Engine:** Combines Demographics, Transportation, Points of Interest (POI), Land Use, and Environmental risk into a unified composite score out of 100.
*   **Business Investment Insights:** Automatically translates complex spatial calculations into easily understandable metrics (ROI Potential, Risk Level, and Growth Potential) using real-time thresholds.
*   **Interactive Cartography:** Powered by Leaflet. Click to drop pins, draw custom polygon measurement areas, toggle rich data layers, and generate dynamic H3-based heatmaps.
*   **Catchment Area Analysis (Isochrones):** Instantly visualize driving, transit, and walking radiuses using live routing algorithms, mapping the true reachable population for a site.
*   **Site Comparison & Export:** Compare multiple potential sites side-by-side. Export detailed analytical briefings as PDFs or Excel sheets directly from the dashboard.
*   **Custom Data Ingestion:** Upload your own geospatial formats (Shapefile, GeoJSON, KML).

## 🛠️ Technology Stack

**Frontend**
*   React 18 + Vite
*   Leaflet & React-Leaflet (Map rendering)
*   Vanilla CSS (Custom dark-mode glassmorphism design system)

**Backend**
*   FastAPI (High-performance Python API)
*   GeoPandas & Shapely (Spatial mathematics and geometry)
*   H3 (Uber's Hexagonal Hierarchical Spatial Index for heatmaps)

## 🚀 Getting Started

### Prerequisites
*   Node.js (v18+)
*   Python (3.9+)

### 1. Backend Setup

Open a terminal in the `backend` directory:

```bash
cd backend
python -m venv venv
# On Windows use: venv\Scripts\activate
# On Mac/Linux use: source venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload
```
*The API will be available at `http://localhost:8000`*

### 2. Frontend Setup

Open a terminal in the `frontend` directory:

```bash
cd frontend
npm install
npm run dev
```
*The web dashboard will be available at `http://localhost:5173`*

## 🎨 UI/UX Philosophy
The dashboard is purposely designed with a premium, low-clutter "Glassmorphism" aesthetic to ensure dense geospatial data is highly readable. We implemented tailored typography, dark-mode-first contrast ratios, and color-coded heuristics (Red/Yellow/Green) to ensure decision-makers can digest intelligence globally at a glance.
