/**
 * ComparePanel — Side-by-side comparison of candidate sites.
 */
import './ComparePanel.css';

const LAYER_COLORS = {
  demographics: '#4fc3f7',
  transportation: '#ff8a65',
  poi: '#ba68c8',
  landuse: '#81c784',
  environmental: '#e57373',
};

const LAYER_SHORT = {
  demographics: 'Demo',
  transportation: 'Trans',
  poi: 'POI',
  landuse: 'Land',
  environmental: 'Env',
};

function getScoreColor(score) {
  if (score >= 80) return '#10b981';
  if (score >= 60) return '#34d399';
  if (score >= 40) return '#fbbf24';
  if (score >= 25) return '#fb923c';
  return '#ef4444';
}

function getRankColor(rank) {
  if (rank === 1) return 'var(--gradient-success)';
  if (rank === 2) return 'var(--gradient-primary)';
  if (rank === 3) return 'var(--gradient-warm)';
  return 'var(--gradient-danger)';
}

export default function ComparePanel({ sites, onClose, onRemoveSite }) {
  if (!sites || sites.length === 0) return null;

  // Sort by score descending
  const ranked = [...sites].sort((a, b) => b.composite_score - a.composite_score);
  ranked.forEach((s, i) => { s.rank = i + 1; });

  return (
    <div className="compare-panel">
      <div className="compare-header">
        <span className="compare-title">⚖️ Site Comparison ({sites.length} sites)</span>
        <button className="score-panel-close" onClick={onClose}>✕</button>
      </div>

      <div className="compare-body">
        {ranked.map((site, idx) => (
          <div key={idx} className="compare-card">
            <div
              className="compare-card-rank"
              style={{ background: getRankColor(site.rank) }}
            >
              #{site.rank}
            </div>

            <button
              className="compare-remove"
              onClick={() => onRemoveSite(idx)}
              title="Remove"
            >
              ✕
            </button>

            <div
              className="compare-card-score"
              style={{ color: getScoreColor(site.composite_score) }}
            >
              {site.composite_score.toFixed(0)}
            </div>

            <div
              className="compare-card-grade"
              style={{ color: getScoreColor(site.composite_score) }}
            >
              {site.grade}
            </div>

            <div className="compare-card-coords">
              {site.lat.toFixed(4)}°N, {site.lng.toFixed(4)}°E
            </div>

            <div className="compare-bars">
              {site.sub_scores.map(sub => (
                <div key={sub.layer} className="compare-bar-item">
                  <span className="compare-bar-label">
                    {LAYER_SHORT[sub.layer] || sub.layer}
                  </span>
                  <div className="compare-bar-track">
                    <div
                      className="compare-bar-fill"
                      style={{
                        width: `${sub.score}%`,
                        background: LAYER_COLORS[sub.layer],
                      }}
                    />
                  </div>
                  <span className="compare-bar-value">
                    {sub.score.toFixed(0)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
