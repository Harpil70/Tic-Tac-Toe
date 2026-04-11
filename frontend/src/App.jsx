/**
 * GeoSpatial Site Readiness Analyzer — Main Application
 * AI-Powered Location Intelligence for Gujarat, India
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import LoginPage from './components/LoginPage/LoginPage';
import Sidebar from './components/Sidebar/Sidebar';
import MapView from './components/MapView/MapView';
import ScorePanel from './components/ScorePanel/ScorePanel';
import ComparePanel from './components/ComparePanel/ComparePanel';
import { auth, signOut } from './firebase';
import {
  fetchLayers,
  fetchLayerData,
  scorePoint,
  fetchHeatmap,
  runClustering,
  exportReport,
  uploadLayer,
  scorePolygon,
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
  // ─── Auth State ────────────────────────────────────────────
  const [user, setUser] = useState(() => {
    try {
      const saved = localStorage.getItem('geo_user');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  const handleLogin = useCallback((userData) => {
    localStorage.setItem('geo_user', JSON.stringify(userData));
    setUser(userData);
  }, []);

  const handleLogout = useCallback(async () => {
    try {
      await signOut(auth);
    } catch (err) {
      console.warn('Firebase signOut error:', err);
    }
    setUser(null);
    localStorage.removeItem('geo_user');
  }, []);

  // ─── App State ─────────────────────────────────────────────
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
  const [polygonData, setPolygonData] = useState(null);

  const [compareMode, setCompareMode] = useState(false);
  const [compareSites, setCompareSites] = useState([]);
  const compareSitesRef = useRef([]);

  useEffect(() => {
    compareSitesRef.current = compareSites;
  }, [compareSites]);

  const [drawMode, setDrawMode] = useState(false);
  const [loading, setLoading] = useState(false);
  const [apiConnected, setApiConnected] = useState(false);
  const [error, setError] = useState(null);

  // Map reference for reading current viewport bounds
  const mapRef = useRef(null);

  const getMapBounds = () => {
    if (!mapRef.current) return null;
    const b = mapRef.current.getBounds();
    return {
      minLat: b.getSouth(),
      maxLat: b.getNorth(),
      minLng: b.getWest(),
      maxLng: b.getEast(),
    };
  };

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

  // Build effective weights: zero out any disabled (toggled-off) layers
  const getEffectiveWeights = useCallback(() => {
    const effective = {};
    for (const [key, val] of Object.entries(weights)) {
      effective[key] = enabledLayers[key] ? val : 0;
    }
    return effective;
  }, [weights, enabledLayers]);

  const handlePresetChange = (e) => {
    setPreset(e.target.value);
  };

  const handleMapClick = useCallback(async (lat, lng) => {
    if (drawMode) return;

    setPinMarker({ lat, lng });
    setLoading(true);
    setError(null);

    try {
      const result = await scorePoint(lat, lng, getEffectiveWeights(), preset, radiusKm);
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
  }, [getEffectiveWeights, preset, radiusKm, drawMode, compareMode]);

  const handleRunHeatmap = async () => {
    setLoading(true);
    setError(null);
    try {
      const bounds = getMapBounds();
      const data = await fetchHeatmap({ resolution: 7, preset, weights: getEffectiveWeights(), ...bounds });
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
      const bounds = getMapBounds();
      const data = await runClustering({ preset, weights: getEffectiveWeights(), bounds });
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

  const handleExport = async (format = 'pdf') => {
    // Gather full score data — use compare sites if available, otherwise current scored site
    let siteResults = [...compareSites];
    if (siteResults.length === 0 && scoreData) {
      siteResults = [scoreData];
    }
    if (siteResults.length === 0) {
      setError('Click on the map to score a site first, then export');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      // Send the full pre-computed results so the file matches the website exactly
      await exportReport(siteResults, format, weights, preset);
    } catch (err) {
      console.error('Export error:', err);
      setError(`Failed to export ${format.toUpperCase()}. Check the backend console for errors.`);
    }
    setLoading(false);
  };

  const handleShowIsochrone = (data) => {
    setIsochroneData(data);
  };

  const handlePolygonComplete = async (polygon) => {
    setDrawMode(false);
    setLoading(true);
    setError(null);
    try {
      const result = await scorePolygon(polygon, getEffectiveWeights(), preset);
      setPolygonData(result);
    } catch (err) {
      console.error('Polygon score error:', err);
      setError('Failed to score polygon area');
    }
    setLoading(false);
  };

  const handleUploadLayer = async (file, customName) => {
    setLoading(true);
    setError(null);
    try {
      await uploadLayer(file, customName);
      
      // Refresh layers
      const layerInfo = await fetchLayers();
      setLayers(layerInfo.layers || []);

      // Pre-load layer data again
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

      // Successfully processed, you might want to show a success toast here
    } catch (err) {
      console.error('Upload error:', err);
      setError('Failed to upload data. Please check the format and try again.');
    }
    setLoading(false);
  };

  // ─── Dynamic Rescore Effect ────────────────────────────────
  const weightsStr = JSON.stringify(weights);
  const enabledStr = JSON.stringify(enabledLayers);

  useEffect(() => {
    // Only run if we actually have a selected site and we're not drawing
    if (!pinMarker || drawMode) return;

    let isCancelled = false;

    const runDynamicUpdates = async () => {
      try {
        // 1. Update the primary selected site silently
        const result = await scorePoint(pinMarker.lat, pinMarker.lng, getEffectiveWeights(), preset, radiusKm);
        if (isCancelled) return;
        setScoreData(result);

        // 2. Update any comparison sites dynamically
        const currentCompare = compareSitesRef.current;
        if (currentCompare.length > 0) {
          const newCompare = await Promise.all(
            currentCompare.map(site => scorePoint(site.lat, site.lng, getEffectiveWeights(), preset, radiusKm))
          );
          if (!isCancelled) setCompareSites(newCompare);
        }
      } catch (err) {
        console.error('Dynamic score update failed:', err);
      }
    };

    runDynamicUpdates();

    return () => {
      isCancelled = true;
    };
  }, [weightsStr, enabledStr, preset, radiusKm, pinMarker, drawMode, getEffectiveWeights]);

  // ─── Render ────────────────────────────────────────────────

  // Show login page if not authenticated
  if (!user) {
    return <LoginPage onLogin={handleLogin} />;
  }

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

          {/* User Profile */}
          <div className="header-user">
            {user.picture ? (
              <img src={user.picture} alt="" className="user-avatar" referrerPolicy="no-referrer" />
            ) : (
              <div className="user-avatar user-avatar-placeholder">
                {user.name?.charAt(0)?.toUpperCase() || '?'}
              </div>
            )}
            <span className="user-name">{user.name}</span>
            <button className="logout-btn" onClick={handleLogout} title="Sign out">
              ↗ Logout
            </button>
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
          onUploadLayer={handleUploadLayer}
          compareMode={compareMode}
          compareSites={compareSites}
          loading={loading}
          drawMode={drawMode}
          onToggleDrawMode={() => setDrawMode(!drawMode)}
        />

        <div className="map-container">
          <MapView
            layerData={layerData}
            enabledLayers={enabledLayers}
            heatmapData={heatmapData}
            clusterData={clusterData}
            isochroneData={isochroneData}
            polygonData={polygonData}
            compareSites={compareSites}
            pinMarker={pinMarker}
            scoreData={scoreData}
            radiusKm={radiusKm}
            onMapClick={handleMapClick}
            drawMode={drawMode}
            onPolygonComplete={handlePolygonComplete}
            mapRef={mapRef}
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
