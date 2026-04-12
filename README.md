<div align="center">

# 🌍 GeoSpatial Site Readiness Analyzer

**A comprehensive location-intelligence platform built to evaluate, score, and compare
geographic zones based on multifaceted data layers.**

*Designed to help retail, commercial, and industrial businesses
find the optimal locations for their next operations.*

---

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React_18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org/)
[![Vite](https://img.shields.io/badge/Bundler-Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev/)
[![Firebase](https://img.shields.io/badge/Auth-Firebase-FFCA28?style=for-the-badge&logo=firebase&logoColor=black)](https://firebase.google.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docs.docker.com/compose/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)



---

## 📋 Table of Contents

- [Overview](#-overview)
- [Core Features](#-core-features)
- [Technology Stack](#-technology-stack)
- [Getting Started](#-getting-started)
- [Project Structure](#-project-structure)
- [API Reference](#-api-reference)
- [Authors]

---
<img width="1919" height="972" alt="Screenshot 2026-04-12 110258" src="https://github.com/user-attachments/assets/e1678f71-0571-4ee9-96b5-9d6bf74c0be3" />

## 🔭 Overview

Making high-stakes location decisions — where to open a store, place a warehouse, or
invest in commercial property — traditionally requires expensive consultants and weeks
of manual research.

**GeoSpatial Site Readiness Analyzer** democratizes this process by unifying
demographic, transportation, environmental, and land-use data into a single interactive
dashboard that delivers actionable scores in seconds.

### Who Is This For?

| Persona | Use Case |
| :--- | :--- |
| 🏪 **Retail Strategists** | Identify high-footfall zones with favorable demographics |
| 🏗️ **Real Estate Developers** | Evaluate land parcels against environmental and zoning risk |
| 🏭 **Industrial Planners** | Optimize supply chain proximity via transport network analysis |
| 📊 **Urban Analysts** | Study population catchments and accessibility metrics |
| 🏛️ **Municipal Governments** | Assess infrastructure readiness for development proposals |

---

## ✨ Core Features

### 🧠 Intelligent Scoring Engine

Combines **five weighted data dimensions** into a unified composite score out of 100:

Composite Score = w₁(Demographics) + w₂(Transportation) + w₃(POI Density)
+ w₄(Land Use Compatibility) + w₅(Environmental Risk⁻¹)


Each dimension is independently normalizable and weight-adjustable per business vertical.

---

### 📈 Business Investment Insights

Automatically translates complex spatial calculations into easily digestible metrics:

| Metric | Description | Scoring |
| :--- | :--- | :--- |
| **ROI Potential** | Projected return viability based on demographics × accessibility | 🟢 High · 🟡 Moderate · 🔴 Low |
| **Risk Level** | Composite of environmental hazards, zoning conflicts, and market saturation | 🟢 Low · 🟡 Medium · 🔴 High |
| **Growth Potential** | Population trend trajectory + infrastructure development pipeline | 🟢 Strong · 🟡 Stable · 🔴 Declining |

---

### 🗺️ Interactive Cartography

Powered by **Leaflet** with a rich interaction model:

- 📌 **Click-to-Pin** — Drop analysis pins anywhere on the map
- 🔷 **Polygon Drawing** — Draw custom measurement areas freehand
- 🧩 **Layer Toggling** — Switch between demographic, POI, transport, and risk overlays
- 🔥 **H3 Heatmaps** — Dynamic hexagonal heatmaps via Uber's H3 spatial index

---

### 🚗 Catchment Area Analysis (Isochrones)

Instantly visualize **true reachable zones** using live routing algorithms:

| Mode | Description |
| :--- | :--- |
| 🚗 **Driving** | Road-network travel time polygons (5 / 10 / 15 min) |
| 🚌 **Transit** | Public transportation accessibility radii |
| 🚶 **Walking** | Pedestrian-reachable population coverage |

> **💡 Why Isochrones?**
> Isochrones reveal the *actual* service area of a site — far more accurate than
> simple radius buffers that ignore roads, barriers, and terrain.

---

### 🔬 Spatial Clustering

Leverages clustering algorithms to automatically identify **hotspot zones** and group
geographically similar areas, surfacing patterns invisible to manual analysis.

---

### ⚖️ Site Comparison & Export

- Compare **multiple potential sites** side-by-side with normalized metrics
- Export detailed analytical briefings as:
  - 📄 **PDF** — Formatted reports with maps, charts, and scoring breakdowns
  - 📊 **Excel** — Raw data tables for further analysis in BI tools
  
<img width="1068" height="630" alt="re2" src="https://github.com/user-attachments/assets/3d67f53f-689c-4cd5-a9e5-45f9e38485e9" />



---

### 🔐 Authentication

Firebase-powered authentication ensures secure access with user session management
built directly into the frontend.

---

## 🛠️ Technology Stack

### Frontend

| Technology | Purpose |
| :--- | :--- |
| **React 18** | Component-based UI framework |
| **Vite** | Lightning-fast HMR & build tooling |
| **Leaflet & React-Leaflet** | Interactive map rendering engine |
| **Firebase** | Authentication & user management |
| **Vanilla CSS** | Custom dark-mode glassmorphism design system |

### Backend

| Technology | Purpose |
| :--- | :--- |
| **FastAPI** | High-performance asynchronous Python API |
| **GeoPandas** | Spatial dataframe operations |
| **Shapely** | Computational geometry engine |
| **H3 (Uber)** | Hexagonal hierarchical spatial indexing for heatmaps |

---

## 🚀 Getting Started

### Prerequisites

| Requirement | Minimum Version |
| :--- | :--- |
| [Node.js](https://nodejs.org/) | v18.0+ |
| [Python](https://www.python.org/) | 3.9+ |
| [pip](https://pip.pypa.io/) | Latest |
| [Git](https://git-scm.com/) | Latest |
| [Docker](https://www.docker.com/) | Latest |

---

# 📁 Project Structure

geo-spatial-analyzer/
│
├── backend/
│   ├── app/
│   │   ├── api/                         # 🚀 Routes / Controllers
│   │   │   └── routes/
│   │   │       ├── upload.py
│   │   │       ├── analysis.py
│   │   │       └── health.py
│   │   │
│   │   ├── services/                    # 🧠 Business Logic
│   │   │   ├── clustering.py
│   │   │   ├── scoring.py
│   │   │   ├── routing.py
│   │   │   └── ingestion.py
│   │   │
│   │   ├── models/                      # 📦 Schemas
│   │   │   └── schemas.py
│   │   │
│   │   ├── core/                        # ⚙️ Config & DB
│   │   │   ├── config.py
│   │   │   └── database.py
│   │   │
│   │   ├── utils/                       # 🔧 Helpers
│   │   │   └── spatial.py
│   │   │
│   │   └── main.py                      # 🚪 Entry point
│   │
│   ├── data/                            # 📊 Data ONLY
│   │   ├── raw/
│   │   └── processed/
│   │
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── pages/                       # 📄 Screens (IMPORTANT)
│   │   │   ├── Home.jsx
│   │   │   ├── Upload.jsx
│   │   │   └── Dashboard.jsx
│   │   │
│   │   ├── components/                  # 🧩 UI Components
│   │   ├── hooks/                       # 🔁 Custom Hooks
│   │   ├── services/                    # 🌐 API Calls
│   │   │
│   │   ├── App.jsx
│   │   └── main.jsx
│   │
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── .env
├── docker-compose.yml
└── README.md

## 📡 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/score` | Calculate composite site score for given coordinates |
| POST | `/api/isochrone` | Generate catchment area polygons |
| POST | `/api/compare` | Compare multiple sites side-by-side |
| POST | `/api/upload` | Ingest custom geospatial data |
| POST | `/api/cluster` | Run spatial clustering analysis |
| GET | `/api/heatmap/{layer}` | Retrieve H3 heatmap tile data |
| POST | `/api/export/pdf` | Generate a PDF briefing |
| POST | `/api/export/excel` | Generate an Excel data export |
| GET | `/health` | API health check |

## 👨‍💻 Authors

| Name | 
|------|
| Harpil Patel |
| Kavya Chandegara |
| Harsh Patel |
| Ankit Yadav |
| Dev Shyara | 

---
