/**
 * GeoSpatial Site Readiness Analyzer — Main Application
 * AI-Powered Location Intelligence for Gujarat, India
 */
import { useState, useEffect, useCallback } from 'react';
import Sidebar from './components/Sidebar/Sidebar';
import MapView from './components/MapView/MapView';
import ScorePanel from './components/ScorePanel/ScorePanel';
import ComparePanel from './components/ComparePanel/ComparePanel';
import {
  fetchLayers,
  fetchLayerData,
  scorePoint,
  fetchHeatmap,
  runClustering,
  exportReport,
  healthCheck,
} from './services/api';
import './App.css';

const DEFAULT_WEIGHTS = {
  demographics: 0.25,
  transportation: 0.20,
  poi: 0.20,
  landuse: 0.15,
  environmental: 0.20,
};

const PRESETS = {
  retail_store: 'Retail Store',
  ev_charging: 'EV Charging',
  warehouse: 'Warehouse',
  telecom_tower: 'Telecom Tower',
  solar_farm: 'Solar Farm',
};

export default function App() {
  // ─── State ─────────────────────────────────────────────────
  const [layers, setLayers] = useState([]);
  const [layerData, setLayerData] = useState({});
  const [enabledLayers, setEnabledLayers] = useState({
    demographics: false,
    transportation: false,
    poi: false,
    landuse: false,
    environmental: false,
  });
  const [weights, setWeights] = useState({ ...DEFAULT_WEIGHTS });
  const [preset, setPreset] = useState('retail_store');
  const [radiusKm, setRadiusKm] = useState(5);

  const [scoreData, setScoreData] = useState(null);
  const [pinMarker, setPinMarker] = useState(null);
  const [heatmapData, setHeatmapData] = useState(null);
  const [clusterData, setClusterData] = useState(null);
  const [isochroneData, setIsochroneData] = useState(null);

  const [compareMode, setCompareMode] = useState(false);
  const [compareSites, setCompareSites] = useState([]);

  const [drawMode, setDrawMode] = useState(false);
  const [loading, setLoading] = useState(false);
  const [apiConnected, setApiConnected] = useState(false);
  const [error, setError] = useState(null);

  // ─── Initialize ────────────────────────────────────────────
  useEffect(() => {
    const init = async () => {
      try {
        await healthCheck();
        setApiConnected(true);

        const layerInfo = await fetchLayers();
        setLayers(layerInfo.layers || []);

        // Pre-load all layer data
        const allData = {};
        for (const layer of (layerInfo.layers || [])) {
          try {
            const data = await fetchLayerData(layer.name);
            allData[layer.name] = data;
          } catch (err) {
            console.warn(`Failed to load layer ${layer.name}:`, err);
          }
        }
        setLayerData(allData);
      } catch (err) {
        console.error('Backend connection failed:', err);
        setError('Cannot connect to backend. Start the server with: uvicorn main:app --reload');
      }
    };
    init();
  }, []);

  // ─── Handlers ──────────────────────────────────────────────
  const handleToggleLayer = useCallback((name) => {
    setEnabledLayers(prev => ({ ...prev, [name]: !prev[name] }));
  }, []);

  const handleWeightChange = useCallback((layer, value) => {
    setWeights(prev => ({ ...prev, [layer]: value }));
  }, []);

  const handlePresetChange = (e) => {
    setPreset(e.target.value);
  };

  const handleMapClick = useCallback(async (lat, lng) => {
    if (drawMode) return;

    setPinMarker({ lat, lng });
    setLoading(true);
    setError(null);

    try {
      const result = await scorePoint(lat, lng, weights, preset, radiusKm);
      setScoreData(result);
      setIsochroneData(null);

      if (compareMode) {
        setCompareSites(prev => [...prev, result]);
      }
    } catch (err) {
      console.error('Score error:', err);
      setError('Failed to compute score. Is the backend running?');
    }
    setLoading(false);
  }, [weights, preset, radiusKm, drawMode, compareMode]);

  const handleRunHeatmap = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchHeatmap({ resolution: 7, preset });
      setHeatmapData(data);
    } catch (err) {
      console.error('Heatmap error:', err);
      setError('Failed to generate heatmap');
    }
    setLoading(false);
  };

  const handleRunClustering = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await runClustering({ preset });
      setClusterData(data);
    } catch (err) {
      console.error('Cluster error:', err);
      setError('Failed to run clustering');
    }
    setLoading(false);
  };

  const handleToggleCompare = () => {
    if (compareMode) {
      setCompareMode(false);
    } else {
      setCompareMode(true);
      setCompareSites([]);
    }
  };

  const handleAddCompare = (coord) => {
    if (!compareMode) {
      setCompareMode(true);
    }
    if (scoreData) {
      // Check if already added
      const exists = compareSites.some(
        s => Math.abs(s.lat - scoreData.lat) < 0.0001 && Math.abs(s.lng - scoreData.lng) < 0.0001
      );
      if (!exists) {
        setCompareSites(prev => [...prev, scoreData]);
      }
    }
  };

  const handleRemoveCompare = (idx) => {
    setCompareSites(prev => prev.filter((_, i) => i !== idx));
  };

  const handleExport = async () => {
    if (compareSites.length === 0) {
      setError('Pin at least one site to export');
      return;
    }
    setLoading(true);
    try {
      const sites = compareSites.map(s => ({ lat: s.lat, lng: s.lng }));
      await exportReport(sites, 'pdf', weights, preset);
    } catch (err) {
      console.error('Export error:', err);
      setError('Failed to export PDF');
    }
    setLoading(false);
  };

  const handleShowIsochrone = (data) => {
    setIsochroneData(data);
  };

  const handlePolygonComplete = async (polygon) => {
    setDrawMode(false);
    // TODO: Score polygon area
    console.log('Polygon drawn:', polygon);
  };

  // ─── Render ────────────────────────────────────────────────
  return (
    <div className="app">
      {/* ─── Header ─── */}
      <header className="header">
        <div className="header-brand">
          <div className="header-logo">🌍</div>
          <span className="header-title">GeoSpatial Site Readiness Analyzer</span>
          <span className="header-subtitle">Gujarat, India</span>
        </div>

        <div className="header-actions">
          <div className="preset-selector">
            <label>Use Case:</label>
            <select value={preset} onChange={handlePresetChange}>
              {Object.entries(PRESETS).map(([key, label]) => (
                <option key={key} value={key}>{label}</option>
              ))}
            </select>
          </div>

          <div className="header-status">
            <div className={`status-dot ${apiConnected ? '' : 'disconnected'}`}
                 style={{ background: apiConnected ? '#10b981' : '#ef4444' }} />
            <span>{apiConnected ? 'API Connected' : 'Disconnected'}</span>
          </div>
        </div>
      </header>

      {/* ─── Main Content ─── */}
      <div className="main-content">
        <Sidebar
          layers={layers}
          enabledLayers={enabledLayers}
          onToggleLayer={handleToggleLayer}
          weights={weights}
          onWeightChange={handleWeightChange}
          radiusKm={radiusKm}
          onRadiusChange={setRadiusKm}
          onRunHeatmap={handleRunHeatmap}
          onRunClustering={handleRunClustering}
          onToggleCompare={handleToggleCompare}
          onExport={handleExport}
          compareMode={compareMode}
          compareSites={compareSites}
          loading={loading}
        />

        <div className="map-container">
          <MapView
            layerData={layerData}
            enabledLayers={enabledLayers}
            heatmapData={heatmapData}
            clusterData={clusterData}
            isochroneData={isochroneData}
            compareSites={compareSites}
            pinMarker={pinMarker}
            onMapClick={handleMapClick}
            drawMode={drawMode}
            onPolygonComplete={handlePolygonComplete}
          />

          {/* Score Panel */}
          {scoreData && (
            <ScorePanel
              scoreData={scoreData}
              onClose={() => setScoreData(null)}
              onAddCompare={handleAddCompare}
              onShowIsochrone={handleShowIsochrone}
              compareMode={compareMode}
            />
          )}

          {/* Compare Panel */}
          {compareSites.length > 0 && (
            <ComparePanel
              sites={compareSites}
              onClose={() => { setCompareSites([]); setCompareMode(false); }}
              onRemoveSite={handleRemoveCompare}
            />
          )}

          {/* Loading Overlay */}
          {loading && (
            <div className="loading-overlay">
              <div className="spinner" style={{ width: 32, height: 32 }} />
              <span style={{ color: 'var(--text-secondary)', marginTop: 8 }}>Analyzing...</span>
            </div>
          )}

          {/* Error Toast */}
          {error && (
            <div
              style={{
                position: 'absolute',
                top: 12,
                left: '50%',
                transform: 'translateX(-50%)',
                background: 'rgba(239,68,68,0.15)',
                border: '1px solid rgba(239,68,68,0.3)',
                borderRadius: 8,
                padding: '8px 16px',
                color: '#fb7185',
                fontSize: 12,
                zIndex: 500,
                backdropFilter: 'blur(12px)',
                cursor: 'pointer',
                animation: 'fadeIn 0.3s ease-out',
              }}
              onClick={() => setError(null)}
            >
              ⚠ {error} <span style={{ opacity: 0.5, marginLeft: 8 }}>✕</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
