/**
 * Sidebar — Layer controls, weight config, and action buttons.
 */
import { useState } from 'react';
import './Sidebar.css';

const LAYER_META = {
  demographics: { name: 'Demographics', color: '#4fc3f7', icon: '👥' },
  transportation: { name: 'Transportation', color: '#ff8a65', icon: '🛣️' },
  poi: { name: 'Points of Interest', color: '#ba68c8', icon: '📍' },
  landuse: { name: 'Land Use & Zoning', color: '#81c784', icon: '🏗️' },
  environmental: { name: 'Environmental Risk', color: '#e57373', icon: '⚠️' },
};

export default function Sidebar({
  layers,
  enabledLayers,
  onToggleLayer,
  weights,
  onWeightChange,
  radiusKm,
  onRadiusChange,
  onRunHeatmap,
  onRunClustering,
  onToggleCompare,
  onExport,
  onUploadLayer,
  compareMode,
  compareSites,
  loading,
  drawMode,
  onToggleDrawMode,
}) {
  const [collapsed, setCollapsed] = useState({});
  const [dragActive, setDragActive] = useState(false);

  const toggleSection = (key) => {
    setCollapsed(prev => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-title">Control Panel</div>
      </div>

      <div className="sidebar-body">
        {/* ─── Data Layers & Weights (unified) ─── */}
        <div className="sidebar-section">
          <div
            className="sidebar-section-title"
            onClick={() => toggleSection('layers')}
            style={{ cursor: 'pointer' }}
          >
            {collapsed.layers ? '▶' : '▼'} Data Layers & Weights
          </div>
          {!collapsed.layers && layers.map(layer => {
            const meta = LAYER_META[layer.name] || {};
            const isEnabled = !!enabledLayers[layer.name];
            const weightVal = weights[layer.name] ?? 0;
            return (
              <div key={layer.name} className="layer-block">
                <div
                  className="layer-item"
                  onClick={() => onToggleLayer(layer.name)}
                >
                  <div
                    className="layer-dot"
                    style={{
                      background: meta.color,
                      opacity: isEnabled ? 1 : 0.3,
                    }}
                  />
                  <div className="layer-info">
                    <div className="layer-name">{meta.icon} {meta.name || layer.name}</div>
                    <div className="layer-count">{layer.feature_count} features</div>
                  </div>
                  <label className="toggle" onClick={e => e.stopPropagation()}>
                    <input
                      type="checkbox"
                      checked={isEnabled}
                      onChange={() => onToggleLayer(layer.name)}
                    />
                    <span className="toggle-slider" />
                  </label>
                </div>

                {/* Weight slider — only visible when layer is toggled ON */}
                {isEnabled && (
                  <div className="weight-inline">
                    <div className="weight-header">
                      <span className="weight-label" style={{ color: meta.color }}>
                        Weight
                      </span>
                      <span className="weight-value">{Math.round(weightVal * 100)}%</span>
                    </div>
                    <input
                      type="range"
                      className="weight-slider"
                      min="0"
                      max="100"
                      value={Math.round(weightVal * 100)}
                      onChange={e => onWeightChange(layer.name, parseInt(e.target.value) / 100)}
                      style={{
                        background: `linear-gradient(to right, ${meta.color} ${weightVal * 100}%, rgba(148,163,184,0.15) ${weightVal * 100}%)`,
                      }}
                    />
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* ─── Analysis Radius ─── */}
        <div className="sidebar-section">
          <div className="sidebar-section-title">Analysis Settings</div>
          <div className="radius-control">
            <label>Radius (km):</label>
            <input
              type="number"
              className="input radius-input"
              value={radiusKm}
              min={1}
              max={50}
              onChange={e => onRadiusChange(parseFloat(e.target.value) || 5)}
            />
          </div>
        </div>

        {/* ─── Upload Data ─── */}
        <div className="sidebar-section">
          <div
            className="sidebar-section-title"
            onClick={() => toggleSection('upload')}
            style={{ cursor: 'pointer' }}
          >
            {collapsed.upload ? '▶' : '▼'} Upload Data Layer
          </div>
          {!collapsed.upload && (
            <div
              className={`upload-dropzone ${dragActive ? 'drag-active' : ''}`}
              onDragEnter={(e) => { e.preventDefault(); setDragActive(true); }}
              onDragLeave={(e) => { e.preventDefault(); setDragActive(false); }}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault();
                setDragActive(false);
                if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                  const file = e.dataTransfer.files[0];
                  let name = prompt('Enter a layer name (or leave empty for auto):', file.name.split('.')[0]);
                  if (name === null) return; // Cancelled
                  onUploadLayer(file, name);
                }
              }}
            >
              <div className="upload-icon">📁</div>
              <p>Drag & drop or <label className="upload-link">click to browse<input type="file" style={{ display: 'none' }} accept=".geojson,.json,.zip,.shp,.tif,.tiff,.wkt,.txt" onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  const file = e.target.files[0];
                  let name = prompt('Enter a layer name (or leave empty for auto):', file.name.split('.')[0]);
                  if (name === null) return;
                  onUploadLayer(file, name);
                }
              }} /></label></p>
              <span className="upload-formats">Requires: .geojson, .tif, .wkt, .zip (.shp)</span>
            </div>
          )}
        </div>
      </div>

      {/* ─── Action Buttons ─── */}
      <div className="sidebar-actions">
        <button
          className="action-btn action-btn-heatmap"
          onClick={onRunHeatmap}
          disabled={loading}
        >
          <span className="action-btn-icon">🗺️</span>
          {loading ? 'Computing...' : 'Generate H3 Heatmap'}
        </button>

        <button
          className={`action-btn ${drawMode ? 'active' : ''}`}
          onClick={onToggleDrawMode}
          style={drawMode ? { background: 'rgba(59,130,246,0.25)', color: '#60a5fa' } : { borderColor: 'rgba(59,130,246,0.15)', color: '#60a5fa' }}
        >
          <span className="action-btn-icon">✏️</span>
          {drawMode ? 'Cancel Drawing' : 'Draw Polygon Area'}
        </button>

        <button
          className="action-btn action-btn-cluster"
          onClick={onRunClustering}
          disabled={loading}
        >
          <span className="action-btn-icon">🎯</span>
          {loading ? 'Analyzing...' : 'Detect Hot Spots'}
        </button>

        <button
          className={`action-btn action-btn-compare ${compareMode ? 'active' : ''}`}
          onClick={onToggleCompare}
          style={compareMode ? { background: 'rgba(251,191,36,0.25)' } : {}}
        >
          <span className="action-btn-icon">⚖️</span>
          {compareMode
            ? `Compare Mode (${compareSites.length} sites)`
            : 'Compare Sites'}
        </button>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            className="action-btn action-btn-export"
            onClick={() => onExport('pdf')}
            disabled={loading}
            style={{ flex: 1 }}
          >
            <span className="action-btn-icon">📄</span>
            Export PDF
          </button>
          
          <button
            className="action-btn action-btn-export"
            onClick={() => onExport('excel')}
            disabled={loading}
            style={{ flex: 1, background: 'rgba(16, 185, 129, 0.12)', color: '#34d399', border: '1px solid rgba(16, 185, 129, 0.15)' }}
          >
            <span className="action-btn-icon">📊</span>
            Export Excel
          </button>
        </div>
      </div>
    </div>
  );
}
