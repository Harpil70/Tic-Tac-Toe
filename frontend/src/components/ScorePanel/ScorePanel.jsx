/**
 * ScorePanel — Displays site readiness score breakdown with gauge, sub-scores, and isochrone data.
 */
import { useState, useEffect } from 'react';
import { fetchIsochrone } from '../../services/api';
import './ScorePanel.css';

const LAYER_COLORS = {
  demographics: '#4fc3f7',
  transportation: '#ff8a65',
  poi: '#ba68c8',
  landuse: '#81c784',
  environmental: '#e57373',
};

const LAYER_LABELS = {
  demographics: 'Demographics',
  transportation: 'Transportation',
  poi: 'Points of Interest',
  landuse: 'Land Use & Zoning',
  environmental: 'Environmental',
};

function getScoreColor(score) {
  if (score >= 80) return '#10b981';
  if (score >= 60) return '#34d399';
  if (score >= 40) return '#fbbf24';
  if (score >= 25) return '#fb923c';
  return '#ef4444';
}

function ScoreGauge({ score, grade }) {
  const size = 110;
  const stroke = 8;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = (score / 100) * circumference;
  const color = getScoreColor(score);

  return (
    <div className="score-gauge" style={{ width: size, height: size }}>
      <svg width={size} height={size}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(148,163,184,0.1)"
          strokeWidth={stroke}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={circumference - progress}
          style={{ transition: 'stroke-dashoffset 1s ease-out' }}
        />
      </svg>
      <div className="score-gauge-value">
        <div className="score-gauge-number" style={{ color }}>{score.toFixed(0)}</div>
        <div className="score-gauge-label">{grade}</div>
      </div>
    </div>
  );
}

export default function ScorePanel({
  scoreData,
  onClose,
  onAddCompare,
  onShowIsochrone,
  compareMode,
}) {
  const [isoData, setIsoData] = useState(null);
  const [isoLoading, setIsoLoading] = useState(false);

  if (!scoreData) return null;

  const { lat, lng, composite_score, grade, sub_scores, threshold_violations } = scoreData;

  const handleIsochrone = async () => {
    setIsoLoading(true);
    try {
      const data = await fetchIsochrone(lat, lng, 'driving', [10, 20, 30]);
      setIsoData(data);
      if (onShowIsochrone) onShowIsochrone(data);
    } catch (err) {
      console.error('Isochrone error:', err);
    }
    setIsoLoading(false);
  };

  return (
    <div className="score-panel">
      <div className="score-panel-header">
        <span className="score-panel-title">📊 Site Readiness Score</span>
        <button className="score-panel-close" onClick={onClose}>✕</button>
      </div>

      <div className="score-panel-body">
        {/* ─── Gauge ─── */}
        <div className="score-gauge-section">
          <ScoreGauge score={composite_score} grade={grade} />
          <div className="score-info">
            <div className="score-grade" style={{ color: getScoreColor(composite_score) }}>
              {composite_score.toFixed(1)} / 100
            </div>
            <div className="score-coords">
              {lat.toFixed(4)}°N, {lng.toFixed(4)}°E
            </div>

            {threshold_violations && threshold_violations.length > 0 && (
              <div className="score-violations">
                {threshold_violations.map((v, i) => (
                  <div key={i} className="violation-item">
                    <span>⚠</span>
                    <span>{v}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* ─── Sub-scores ─── */}
        <div className="subscore-list">
        {sub_scores.map(sub => {
            const color = LAYER_COLORS[sub.layer] || '#888';
            const details = sub.details || {};
            const isExcluded = sub.weight === 0;
            return (
              <div key={sub.layer} className="subscore-item" style={isExcluded ? { opacity: 0.4 } : {}}>
                <div className="subscore-header">
                  <span className="subscore-name" style={{ color: isExcluded ? '#64748b' : color }}>
                    {LAYER_LABELS[sub.layer] || sub.layer}
                    {isExcluded && <span style={{ fontSize: 9, marginLeft: 4, color: '#94a3b8' }}>(excluded)</span>}
                  </span>
                  <span className="subscore-value" style={{ color: isExcluded ? '#64748b' : getScoreColor(sub.score) }}>
                    {sub.score.toFixed(1)}
                  </span>
                </div>
                <div className="subscore-bar">
                  <div
                    className="subscore-bar-fill"
                    style={{
                      width: `${sub.score}%`,
                      background: isExcluded
                        ? '#475569'
                        : `linear-gradient(90deg, ${color}, ${getScoreColor(sub.score)})`,
                    }}
                  />
                </div>
                <div className="subscore-detail">
                  <span>Weight: {(sub.weight * 100).toFixed(0)}%</span>
                  <span>Weighted: {sub.weighted_score.toFixed(1)}</span>
                  {sub.layer === 'demographics' && (
                    <>
                      <span>Pop: {(details.population_nearby || 0).toLocaleString()}</span>
                      <span>Income: ₹{(details.avg_income || 0).toLocaleString()}</span>
                    </>
                  )}
                  {sub.layer === 'transportation' && (
                    <>
                      <span>Roads: {details.roads || 0}</span>
                      <span>Transit: {details.transit_stops || 0}</span>
                      {details.nearest_highway_km && (
                        <span>Hwy: {details.nearest_highway_km}km</span>
                      )}
                    </>
                  )}
                  {sub.layer === 'poi' && (
                    <>
                      <span>Competitors: {details.competitors || 0}</span>
                      <span>Anchors: {details.anchors || 0}</span>
                    </>
                  )}
                  {sub.layer === 'landuse' && (
                    <>
                      <span>Zone: {details.dominant_zone || '?'}</span>
                      <span>Status: {details.development_status || '?'}</span>
                    </>
                  )}
                  {sub.layer === 'environmental' && (
                    <>
                      <span>Flood: {details.flood_risk || 0}</span>
                      <span>Quake: {details.earthquake_risk || 0}</span>
                      <span>AQI: {details.avg_aqi || '?'}</span>
                    </>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* ─── Isochrone ─── */}
        <div className="isochrone-section">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span className="isochrone-title">🚗 Drive-Time Catchment</span>
            <button
              className="btn btn-sm btn-secondary"
              onClick={handleIsochrone}
              disabled={isoLoading}
            >
              {isoLoading ? '⏳' : '▶'} {isoData ? 'Refresh' : 'Analyze'}
            </button>
          </div>

          {isoData && (
            <div className="isochrone-rings">
              {isoData.isochrones.map(iso => (
                <div key={iso.minutes} className="isochrone-ring">
                  <span className="isochrone-time">{iso.minutes} min</span>
                  <span className="isochrone-pop">
                    👤 {(iso.catchment.population || 0).toLocaleString()}
                  </span>
                  <span className="isochrone-area">{iso.catchment.area_sqkm} km²</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ─── Actions ─── */}
      <div className="score-panel-actions">
        {compareMode && (
          <button
            className="btn btn-primary btn-sm"
            onClick={() => onAddCompare({ lat, lng })}
          >
            + Add to Compare
          </button>
        )}
        <button
          className="btn btn-secondary btn-sm"
          onClick={() => onAddCompare({ lat, lng })}
        >
          📌 Pin Site
        </button>
      </div>
    </div>
  );
}
