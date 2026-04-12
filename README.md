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

</div>

---

## 📋 Table of Contents

- [Overview](#overview)
- [Core Features](#core-features)
- [Technology Stack](#technology-stack)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [Authors](#authors)

---

<div align="center">
  <img width="1919" alt="Screenshot 2026-04-12 110258" src="https://github.com/user-attachments/assets/e1678f71-0571-4ee9-96b5-9d6bf74c0be3" />
</div>

---

## 🔭 Overview

	@@ -47,13 +52,13 @@ dashboard that delivers actionable scores in seconds.

### Who Is This For?

| Persona                        | Use Case                                                        |
| :----------------------------- | :-------------------------------------------------------------- |
| 🏪 **Retail Strategists**      | Identify high-footfall zones with favorable demographics        |
| 🏗️ **Real Estate Developers** | Evaluate land parcels against environmental and zoning risk     |
| 🏭 **Industrial Planners**     | Optimize supply chain proximity via transport network analysis  |
| 📊 **Urban Analysts**          | Study population catchments and accessibility metrics           |
| 🏛️ **Municipal Governments**  | Assess infrastructure readiness for development proposals       |

---

	@@ -75,11 +80,11 @@ Each dimension is independently normalizable and weight-adjustable per business

Automatically translates complex spatial calculations into easily digestible metrics:

| Metric               | Description                                                                      | Scoring                          |
| :------------------- | :------------------------------------------------------------------------------- | :------------------------------- |
| **ROI Potential**    | Projected return viability based on demographics × accessibility                 | 🟢 High · 🟡 Moderate · 🔴 Low  |
| **Risk Level**       | Composite of environmental hazards, zoning conflicts, and market saturation      | 🟢 Low · 🟡 Medium · 🔴 High    |
| **Growth Potential** | Population trend trajectory + infrastructure development pipeline                | 🟢 Strong · 🟡 Stable · 🔴 Declining |

---

	@@ -98,11 +103,11 @@ Powered by **Leaflet** with a rich interaction model:

Instantly visualize **true reachable zones** using live routing algorithms:

| Mode            | Description                                        |
| :-------------- | :------------------------------------------------- |
| 🚗 **Driving**  | Road-network travel time polygons (5 / 10 / 15 min) |
| 🚌 **Transit**  | Public transportation accessibility radii           |
| 🚶 **Walking**  | Pedestrian-reachable population coverage            |

> **💡 Why Isochrones?**
> Isochrones reveal the *actual* service area of a site — far more accurate than
	@@ -123,10 +128,10 @@ geographically similar areas, surfacing patterns invisible to manual analysis.
- Export detailed analytical briefings as:
  - 📄 **PDF** — Formatted reports with maps, charts, and scoring breakdowns
  - 📊 **Excel** — Raw data tables for further analysis in BI tools

<div align="center">
  <img width="1068" alt="re2" src="https://github.com/user-attachments/assets/3d67f53f-689c-4cd5-a9e5-45f9e38485e9" />
</div>

---

	@@ -141,21 +146,21 @@ built directly into the frontend.

### Frontend

| Technology                  | Purpose                                      |
| :-------------------------- | :------------------------------------------- |
| **React 18**                | Component-based UI framework                 |
| **Vite**                    | Lightning-fast HMR & build tooling           |
| **Leaflet & React-Leaflet** | Interactive map rendering engine             |
| **Firebase**                | Authentication & user management             |
| **Vanilla CSS**             | Custom dark-mode glassmorphism design system |

### Backend

| Technology    | Purpose                                              |
| :------------ | :--------------------------------------------------- |
| **FastAPI**   | High-performance asynchronous Python API             |
| **GeoPandas** | Spatial dataframe operations                         |
| **Shapely**   | Computational geometry engine                        |
| **H3 (Uber)** | Hexagonal hierarchical spatial indexing for heatmaps |

---
	@@ -164,96 +169,121 @@ built directly into the frontend.

### Prerequisites

| Requirement                            | Minimum Version |
| :------------------------------------- | :-------------- |
| [Node.js](https://nodejs.org/)         | v18.0+          |
| [Python](https://www.python.org/)      | 3.9+            |
| [pip](https://pip.pypa.io/)            | Latest          |
| [Git](https://git-scm.com/)           | Latest          |
| [Docker](https://www.docker.com/)      | Latest          |

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/Harpil70/tic-Tac-Toe.git
cd geo-spatial-analyzer
```

### 2️⃣ Backend Setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 3️⃣ Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```text
geo-spatial-analyzer/
│
├── backend/
│   ├── app/
│   │   ├── api/                        # 🚀 Routes / Controllers
│   │   │   └── routes/
│   │   │       ├── upload.py           #     File upload endpoints
│   │   │       ├── analysis.py         #     Scoring & comparison endpoints
│   │   │       └── health.py           #     Health check endpoint
│   │   │
│   │   ├── services/                   # 🧠 Business Logic
│   │   │   ├── clustering.py           #     Spatial clustering algorithms
│   │   │   ├── scoring.py              #     Composite site scoring engine
│   │   │   ├── routing.py              #     Isochrone & catchment generation
│   │   │   └── ingestion.py            #     GeoJSON / Shapefile / KML parsing
│   │   │
│   │   ├── models/                     # 📦 Schemas
│   │   │   └── schemas.py              #     Pydantic request/response models
│   │   │
│   │   ├── core/                       # ⚙️ Config & Settings
│   │   │   ├── config.py               #     App configuration & env variables
│   │   │   └── database.py             #     Database connection management
│   │   │
│   │   ├── utils/                      # 🔧 Helpers
│   │   │   └── spatial.py              #     GeoPandas / Shapely / H3 utilities
│   │   │
│   │   └── main.py                     # 🏁 FastAPI entry point
│   │
│   ├── data/                           # 📊 Data Assets
│   │   ├── raw/                        #     Original unprocessed datasets
│   │   └── processed/                  #     Cleaned & indexed datasets
│   │
│   └── requirements.txt                # Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── pages/                      # 📄 Page-Level Screens
│   │   │   ├── Home.jsx                #     Landing / map view
│   │   │   ├── Upload.jsx              #     Data upload interface
│   │   │   └── Dashboard.jsx           #     Analytics dashboard
│   │   │
│   │   ├── components/                 # 🧩 Reusable UI Components
│   │   ├── hooks/                      # 🪝 Custom React Hooks
│   │   ├── services/                   # 🔌 API Client & Data Fetching
│   │   ├── App.jsx                     # Root application component
│   │   └── main.jsx                    # React DOM entry point
│   │
│   └── package.json                    # Node.js dependencies & scripts
│
├── .env                                # Environment variables
├── docker-compose.yml                  # Multi-service container orchestration
└── README.md                           # ← You are here
```

## 📡 API Reference

| Method | Endpoint               | Description                                   |
|--------|------------------------|-----------------------------------------------|
| POST   | `/api/score`           | Calculate composite site score                |
| POST   | `/api/isochrone`       | Generate catchment area polygons              |
| POST   | `/api/compare`         | Compare multiple sites side-by-side           |
| POST   | `/api/upload`          | Ingest custom geospatial data                 |
| POST   | `/api/cluster`         | Run spatial clustering analysis               |
| GET    | `/api/heatmap/{layer}` | Retrieve H3 heatmap tile data                 |
| POST   | `/api/export/pdf`      | Generate a PDF briefing                       |
| POST   | `/api/export/excel`    | Generate an Excel data export                 |
| GET    | `/health`              | API health check                              |

## 👨‍💻 Authors

- **Harpil Patel**  
- **Kavya Chandegara**   
- **Harsh Patel**  
- **Ankit Yadav**   
- **Dev Shyara**
