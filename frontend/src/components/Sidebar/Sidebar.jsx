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
  compareMode,
  compareSites,
  loading,
}) {
  const [collapsed, setCollapsed] = useState({});

  const toggleSection = (key) => {
    setCollapsed(prev => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-title">Control Panel</div>
      </div>

      <div className="sidebar-body">
        {/* ─── Layer Toggles ─── */}
        <div className="sidebar-section">
          <div
            className="sidebar-section-title"
            onClick={() => toggleSection('layers')}
            style={{ cursor: 'pointer' }}
          >
            {collapsed.layers ? '▶' : '▼'} Data Layers
          </div>
          {!collapsed.layers && layers.map(layer => {
            const meta = LAYER_META[layer.name] || {};
            return (
              <div
                key={layer.name}
                className="layer-item"
                onClick={() => onToggleLayer(layer.name)}
              >
                <div
                  className="layer-dot"
                  style={{
                    background: meta.color,
                    opacity: enabledLayers[layer.name] ? 1 : 0.3,
                  }}
                />
                <div className="layer-info">
                  <div className="layer-name">{meta.icon} {meta.name || layer.name}</div>
                  <div className="layer-count">{layer.feature_count} features</div>
                </div>
                <label className="toggle" onClick={e => e.stopPropagation()}>
                  <input
                    type="checkbox"
                    checked={!!enabledLayers[layer.name]}
                    onChange={() => onToggleLayer(layer.name)}
                  />
                  <span className="toggle-slider" />
                </label>
              </div>
            );
          })}
        </div>

        {/* ─── Weight Config ─── */}
        <div className="sidebar-section">
          <div
            className="sidebar-section-title"
            onClick={() => toggleSection('weights')}
            style={{ cursor: 'pointer' }}
          >
            {collapsed.weights ? '▶' : '▼'} Scoring Weights
          </div>
          {!collapsed.weights && Object.entries(weights).map(([key, value]) => {
            const meta = LAYER_META[key] || {};
            return (
              <div key={key} className="weight-item">
                <div className="weight-header">
                  <span className="weight-label" style={{ color: meta.color }}>
                    {meta.name || key}
                  </span>
                  <span className="weight-value">{Math.round(value * 100)}%</span>
                </div>
                <input
                  type="range"
                  className="weight-slider"
                  min="0"
                  max="100"
                  value={Math.round(value * 100)}
                  onChange={e => onWeightChange(key, parseInt(e.target.value) / 100)}
                  style={{
                    background: `linear-gradient(to right, ${meta.color} ${value * 100}%, rgba(148,163,184,0.15) ${value * 100}%)`,
                  }}
                />
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

        <button
          className="action-btn action-btn-export"
          onClick={onExport}
          disabled={compareSites.length === 0}
        >
          <span className="action-btn-icon">📄</span>
          Export Report (PDF)
        </button>
      </div>
    </div>
  );
}
