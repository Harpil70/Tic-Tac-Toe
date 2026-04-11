/**
 * SmartSearchBar — AI-powered natural language search for geospatial analysis.
 */
import { useState, useRef, useEffect } from 'react';
import './SmartSearchBar.css';

const SUGGESTIONS = [
  { icon: '☕', text: 'Best place to open a cafe in Ahmedabad' },
  { icon: '⚡', text: 'EV charging near highway in Surat' },
  { icon: '🏪', text: 'Low competition area for grocery store in Rajkot' },
  { icon: '🏭', text: 'Best warehouse location in Vadodara' },
  { icon: '📡', text: 'Telecom tower in Gandhinagar' },
  { icon: '☀️', text: 'Solar farm in Bhavnagar' },
  { icon: '🏥', text: 'Best hospital location in Ahmedabad' },
  { icon: '🏙️', text: 'High population area in Surat' },
];

function getScoreColor(score) {
  if (score >= 80) return '#10b981';
  if (score >= 60) return '#34d399';
  if (score >= 40) return '#fbbf24';
  if (score >= 25) return '#fb923c';
  return '#ef4444';
}

export default function SmartSearchBar({ onSearch, onResultClick, loading }) {
  const [query, setQuery] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [results, setResults] = useState(null);
  const [searching, setSearching] = useState(false);
  const inputRef = useRef(null);
  const wrapperRef = useRef(null);

  // Close suggestions on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const filteredSuggestions = query.length > 0
    ? SUGGESTIONS.filter(s => s.text.toLowerCase().includes(query.toLowerCase()))
    : SUGGESTIONS;

  const handleSubmit = async (searchQuery) => {
    const q = searchQuery || query;
    if (!q.trim()) return;

    setShowSuggestions(false);
    setSearching(true);

    try {
      const data = await onSearch(q);
      setResults(data);
    } catch (err) {
      console.error('Smart search failed:', err);
    }
    setSearching(false);
  };

  const handleSuggestionClick = (text) => {
    setQuery(text);
    handleSubmit(text);
  };

  const handleResultCardClick = (rec) => {
    if (onResultClick) {
      onResultClick(rec);
    }
    setResults(null);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      handleSubmit();
    }
  };

  return (
    <>
      <div className="smart-search-wrapper" ref={wrapperRef}>
        <div className="smart-search-bar">
          <div className="smart-search-icon">🔍</div>
          <input
            ref={inputRef}
            type="text"
            className="smart-search-input"
            placeholder="Ask AI: e.g. Best cafe location in Surat..."
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setShowSuggestions(true);
            }}
            onFocus={() => setShowSuggestions(true)}
            onKeyDown={handleKeyDown}
          />
          <button
            className="smart-search-submit"
            onClick={() => handleSubmit()}
            disabled={searching || loading || !query.trim()}
            title="Search"
          >
            {searching ? '⏳' : '→'}
          </button>
        </div>

        {/* Suggestions Dropdown */}
        {showSuggestions && !searching && !results && filteredSuggestions.length > 0 && (
          <div className="search-suggestions">
            <div className="search-suggestions-title">✨ Try asking</div>
            {filteredSuggestions.slice(0, 6).map((s, i) => (
              <div
                key={i}
                className="search-suggestion-item"
                onClick={() => handleSuggestionClick(s.text)}
              >
                <span className="suggestion-icon">{s.icon}</span>
                <span className="suggestion-text">{s.text}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Results Panel (floating on the map) */}
      {results && results.recommendations && (
        <div className="search-results-panel">
          <div className="search-results-header">
            <h3><span>🧠</span> AI Recommendations</h3>
            <button className="search-results-close" onClick={() => setResults(null)}>✕</button>
          </div>

          <div className="search-results-summary">
            {results.summary}
            <div className="detected-tags">
              {results.city && (
                <span className="detected-tag city">📍 {results.city.name}</span>
              )}
              {results.business_type && (
                <span className="detected-tag">{results.business_type}</span>
              )}
              {results.preset && (
                <span className="detected-tag">preset: {results.preset}</span>
              )}
              {results.intents && results.intents.map((intent, i) => (
                <span key={i} className="detected-tag intent">{intent.replace('_', ' ')}</span>
              ))}
            </div>
          </div>

          {results.recommendations.map((rec, i) => (
            <div
              key={i}
              className="search-result-card"
              onClick={() => handleResultCardClick(rec)}
            >
              <div className="result-card-top">
                <div className="result-rank">{i + 1}</div>
                <div className="result-zone-name">{rec.zone}</div>
                <div
                  className="result-score-badge"
                  style={{
                    background: `${getScoreColor(rec.score)}20`,
                    color: getScoreColor(rec.score),
                    border: `1px solid ${getScoreColor(rec.score)}30`,
                  }}
                >
                  {rec.score}
                </div>
              </div>
              <div className="result-card-bottom">
                <span className="result-explanation">{rec.explanation}</span>
                <span className="result-grade">{rec.grade}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
