/**
 * MapView — Main interactive Leaflet map with all layers, heatmap, clusters, and isochrones.
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import {
  MapContainer,
  TileLayer,
  GeoJSON,
  Marker,
  Popup,
  Polygon,
  CircleMarker,
  Circle,
  useMapEvents,
  useMap,
} from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './MapView.css';

// Fix default marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

const LAYER_COLORS = {
  demographics: '#4fc3f7',
  transportation: '#ff8a65',
  poi: '#ba68c8',
  landuse: '#81c784',
  environmental: '#e57373',
};

const ZONE_COLORS = {
  commercial: '#fbbf24',
  residential: '#60a5fa',
  industrial: '#fb923c',
  mixed_use: '#a78bfa',
  agricultural: '#34d399',
  institutional: '#f472b6',
};

const RISK_COLORS = {
  flood: '#3b82f6',
  earthquake: '#ef4444',
  air_quality: '#a78bfa',
};

function getScoreColor(score) {
  if (score >= 80) return '#10b981';
  if (score >= 60) return '#34d399';
  if (score >= 40) return '#fbbf24';
  if (score >= 25) return '#fb923c';
  return '#ef4444';
}

function getCustomPin(color) {
  return L.divIcon({
    className: 'custom-colored-pin',
    html: `<div style="
      background-color: ${color};
      width: 24px;
      height: 24px;
      border-radius: 50% 50% 50% 0;
      transform: rotate(-45deg);
      border: 3px solid white;
      box-shadow: 2px 2px 6px rgba(0,0,0,0.4);
    "></div>`,
    iconSize: [26, 26],
    iconAnchor: [13, 26],
    popupAnchor: [0, -26]
  });
}

function getHeatColor(score) {
  // Red (0) -> Yellow (50) -> Green (100)
  if (score <= 30) return `rgba(239, 68, 68, 0.55)`;
  if (score <= 50) return `rgba(251, 191, 36, 0.55)`;
  if (score <= 70) return `rgba(52, 211, 153, 0.55)`;
  return `rgba(16, 185, 129, 0.6)`;
}

function MapClickHandler({ onClick }) {
  useMapEvents({
    click: (e) => {
      onClick(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

function CoordsTracker({ onMove }) {
  useMapEvents({
    mousemove: (e) => {
      onMove(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

function MapRefSetter({ mapRef }) {
  const map = useMap();
  if (mapRef) mapRef.current = map;
  return null;
}

function DrawPolygonControl({ active, onPolygonComplete }) {
  const map = useMap();
  const pointsRef = useRef([]);
  const polylineRef = useRef(null);

  useEffect(() => {
    if (!active) {
      pointsRef.current = [];
      if (polylineRef.current) {
        map.removeLayer(polylineRef.current);
        polylineRef.current = null;
      }
      return;
    }

    const onClick = (e) => {
      pointsRef.current.push([e.latlng.lat, e.latlng.lng]);

      if (polylineRef.current) {
        map.removeLayer(polylineRef.current);
      }
      polylineRef.current = L.polyline(pointsRef.current, {
        color: '#3b82f6',
        weight: 2,
        dashArray: '6, 4',
      }).addTo(map);
    };

    const onDblClick = (e) => {
      L.DomEvent.stopPropagation(e);
      if (pointsRef.current.length >= 3) {
        const polygon = pointsRef.current.map(p => [p[1], p[0]]); // [lng, lat] for API
        onPolygonComplete(polygon);
      }
      pointsRef.current = [];
      if (polylineRef.current) {
        map.removeLayer(polylineRef.current);
        polylineRef.current = null;
      }
    };

    map.on('click', onClick);
    map.on('dblclick', onDblClick);

    return () => {
      map.off('click', onClick);
      map.off('dblclick', onDblClick);
    };
  }, [active, map, onPolygonComplete]);

  return null;
}

export default function MapView({
  layerData,
  enabledLayers,
  heatmapData,
  clusterData,
  isochroneData,
  compareSites,
  pinMarker,
  scoreData,
  radiusKm,
  onMapClick,
  drawMode,
  onPolygonComplete,
  polygonData,
  mapRef,
}) {
  const [coords, setCoords] = useState({ lat: 22.3, lng: 72.0 });

  // ─── Style Functions ───────────────────────────────────────
  const demoStyle = (feature) => ({
    fillColor: LAYER_COLORS.demographics,
    fillOpacity: Math.min(0.6, (feature.properties.population_density || 0) / 30000),
    color: LAYER_COLORS.demographics,
    weight: 1,
    opacity: 0.5,
  });

  const transportStyle = (feature) => {
    const type = feature.properties.type;
    const cat = feature.properties.category;
    if (type === 'transit_stop') return {};
    return {
      color: cat === 'national_highway' ? '#f97316' : '#ff8a65',
      weight: cat === 'national_highway' ? 3 : 1.5,
      opacity: 0.7,
    };
  };

  const landuseStyle = (feature) => ({
    fillColor: ZONE_COLORS[feature.properties.zone_type] || '#888',
    fillOpacity: 0.35,
    color: ZONE_COLORS[feature.properties.zone_type] || '#888',
    weight: 1,
    opacity: 0.5,
  });

  const envStyle = (feature) => {
    const riskType = feature.properties.risk_type;
    if (feature.geometry.type === 'Point') return {};
    return {
      fillColor: RISK_COLORS[riskType] || '#e57373',
      fillOpacity: (feature.properties.severity || 0.3) * 0.4,
      color: RISK_COLORS[riskType] || '#e57373',
      weight: 1,
      opacity: 0.5,
      dashArray: riskType === 'flood' ? '4, 4' : null,
    };
  };

  // ─── Popup Functions ───────────────────────────────────────
  const onEachDemo = (feature, layer) => {
    const p = feature.properties;
    layer.bindPopup(`
      <div class="custom-popup">
        <h4>${p.name || 'Census Tract'}</h4>
        <p>👥 Population: <strong>${(p.population || 0).toLocaleString()}</strong></p>
        <p>📊 Density: ${p.population_density?.toLocaleString() || '?'}/km²</p>
        <p>💰 Income: ₹${(p.median_income || 0).toLocaleString()}</p>
        <p>📅 Median Age: ${p.median_age || '?'}</p>
        <p>📖 Literacy: ${((p.literacy_rate || 0) * 100).toFixed(0)}%</p>
      </div>
    `);
  };

  const onEachTransport = (feature, layer) => {
    const p = feature.properties;
    layer.bindPopup(`
      <div class="custom-popup">
        <h4>${p.name}</h4>
        <p>Type: ${p.category || p.type}</p>
        ${p.lanes ? `<p>Lanes: ${p.lanes}</p>` : ''}
        ${p.daily_ridership ? `<p>Ridership: ${p.daily_ridership?.toLocaleString()}/day</p>` : ''}
      </div>
    `);
  };

  const onEachPoi = (feature, layer) => {
    const p = feature.properties;
    const catColors = { competitor: '#ef4444', anchor: '#fbbf24', complementary: '#10b981' };
    layer.bindPopup(`
      <div class="custom-popup">
        <h4>${p.name}</h4>
        <p>Category: <span style="color:${catColors[p.category] || '#888'}">${p.category}</span></p>
        <p>City: ${p.city}</p>
        <p>Rating: ${'⭐'.repeat(Math.round(p.rating || 0))}</p>
      </div>
    `);
  };

  const onEachLanduse = (feature, layer) => {
    const p = feature.properties;
    layer.bindPopup(`
      <div class="custom-popup">
        <h4>${p.name}</h4>
        <p>Zone: ${p.zone_type}</p>
        <p>Area: ${p.area_sqkm} km²</p>
        <p>Development: ${p.development_status}</p>
        ${p.is_gidc ? '<p>🏭 GIDC Industrial Estate</p>' : ''}
      </div>
    `);
  };

  const onEachEnv = (feature, layer) => {
    const p = feature.properties;
    layer.bindPopup(`
      <div class="custom-popup">
        <h4>${p.name}</h4>
        <p>Risk: ${p.risk_type}</p>
        <p>Severity: ${(p.severity * 100).toFixed(0)}%</p>
        ${p.aqi_value ? `<p>AQI: ${p.aqi_value} (${p.aqi_category})</p>` : ''}
        <p>${p.description || ''}</p>
      </div>
    `);
  };

  // ─── Filter point/non-point features ──────────────────────
  const getPointFeatures = (data) =>
    data?.features?.filter(f => f.geometry.type === 'Point') || [];

  const getNonPointFeatures = (data) =>
    data?.features?.filter(f => f.geometry.type !== 'Point') || [];

  const isoColors = ['rgba(59,130,246,0.12)', 'rgba(59,130,246,0.08)', 'rgba(59,130,246,0.04)'];
  const isoBorders = ['rgba(59,130,246,0.5)', 'rgba(59,130,246,0.35)', 'rgba(59,130,246,0.2)'];

  return (
    <div className="map-wrapper">
      <MapContainer
        center={[22.3, 72.0]}
        zoom={7}
        zoomControl={true}
        doubleClickZoom={!drawMode}
        style={{ width: '100%', height: '100%' }}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>'
          maxZoom={19}
        />

        {!drawMode && <MapClickHandler onClick={onMapClick} />}
        <CoordsTracker onMove={(lat, lng) => setCoords({ lat, lng })} />
        <MapRefSetter mapRef={mapRef} />

        {drawMode && (
          <DrawPolygonControl active={drawMode} onPolygonComplete={onPolygonComplete} />
        )}

        {/* ─── Demographics Layer ─── */}
        {enabledLayers.demographics && layerData.demographics && (
          <GeoJSON
            key="demo"
            data={{ type: 'FeatureCollection', features: getNonPointFeatures(layerData.demographics) }}
            style={demoStyle}
            onEachFeature={onEachDemo}
          />
        )}

        {/* ─── Transportation Layer ─── */}
        {enabledLayers.transportation && layerData.transportation && (
          <>
            <GeoJSON
              key="transport-lines"
              data={{ type: 'FeatureCollection', features: getNonPointFeatures(layerData.transportation) }}
              style={transportStyle}
              onEachFeature={onEachTransport}
            />
            {getPointFeatures(layerData.transportation).map(f => (
              <CircleMarker
                key={`transit-${f.id}`}
                center={[f.geometry.coordinates[1], f.geometry.coordinates[0]]}
                radius={4}
                pathOptions={{
                  fillColor: '#ff8a65',
                  fillOpacity: 0.7,
                  color: '#fff',
                  weight: 1,
                }}
              >
                <Popup>
                  <div className="custom-popup">
                    <h4>{f.properties.name}</h4>
                    <p>{f.properties.category}</p>
                    {f.properties.daily_ridership && (
                      <p>Ridership: {f.properties.daily_ridership.toLocaleString()}/day</p>
                    )}
                  </div>
                </Popup>
              </CircleMarker>
            ))}
          </>
        )}

        {/* ─── POI Layer ─── */}
        {enabledLayers.poi && layerData.poi && (
          getPointFeatures(layerData.poi).map(f => {
            const catColors = { competitor: '#ef4444', anchor: '#fbbf24', complementary: '#10b981' };
            return (
              <CircleMarker
                key={`poi-${f.id}`}
                center={[f.geometry.coordinates[1], f.geometry.coordinates[0]]}
                radius={5}
                pathOptions={{
                  fillColor: catColors[f.properties.category] || '#ba68c8',
                  fillOpacity: 0.8,
                  color: '#fff',
                  weight: 1,
                }}
              >
                <Popup>
                  <div className="custom-popup">
                    <h4>{f.properties.name}</h4>
                    <p>Category: {f.properties.category}</p>
                    <p>City: {f.properties.city}</p>
                    <p>Rating: {'⭐'.repeat(Math.round(f.properties.rating || 0))}</p>
                  </div>
                </Popup>
              </CircleMarker>
            );
          })
        )}

        {/* ─── Land Use Layer ─── */}
        {enabledLayers.landuse && layerData.landuse && (
          <GeoJSON
            key="landuse"
            data={layerData.landuse}
            style={landuseStyle}
            onEachFeature={onEachLanduse}
          />
        )}

        {/* ─── Environmental Layer ─── */}
        {enabledLayers.environmental && layerData.environmental && (
          <>
            <GeoJSON
              key="env-polys"
              data={{ type: 'FeatureCollection', features: getNonPointFeatures(layerData.environmental) }}
              style={envStyle}
              onEachFeature={onEachEnv}
            />
            {getPointFeatures(layerData.environmental).map(f => {
              const sev = f.properties.severity || 0.5;
              return (
                <CircleMarker
                  key={`env-${f.id}`}
                  center={[f.geometry.coordinates[1], f.geometry.coordinates[0]]}
                  radius={6}
                  pathOptions={{
                    fillColor: sev > 0.6 ? '#ef4444' : sev > 0.3 ? '#fbbf24' : '#34d399',
                    fillOpacity: 0.7,
                    color: '#fff',
                    weight: 1,
                  }}
                >
                  <Popup>
                    <div className="custom-popup">
                      <h4>{f.properties.name}</h4>
                      <p>AQI: {f.properties.aqi_value} ({f.properties.aqi_category})</p>
                    </div>
                  </Popup>
                </CircleMarker>
              );
            })}
          </>
        )}

        {/* ─── Getis-Ord Gi* Hot/Cold Spots ─── */}
        {clusterData && clusterData.getis_ord_gi && (
          <>
              {clusterData.getis_ord_gi
                .filter(spot => spot.significance !== "not_significant")
                .map((spot, i) => {
                  const isHot = spot.significance.startsWith('hot');
                  const strength = spot.significance.split('_')[1]; // 90, 95, 99
                  const radius = strength === '99' ? 10 : strength === '95' ? 7 : 5;
                  
                  return (
                    <CircleMarker
                      key={`gi-${i}`}
                      center={[spot.lat, spot.lng]}
                      radius={radius}
                      pathOptions={{
                        fillColor: isHot ? '#f59e0b' : '#3b82f6', // distinct from DBSCAN colors
                        fillOpacity: 0.6,
                        color: isHot ? '#b45309' : '#1d4ed8',
                        weight: 1,
                      }}
                    >
                      <Popup>
                        <div className="custom-popup">
                          <h4 style={{ color: isHot ? '#f59e0b' : '#3b82f6' }}>
                            {isHot ? '🔥 Gi* Hot Spot' : '❄️ Gi* Cold Spot'}
                          </h4>
                          <div className="popup-score" style={{ color: '#fff', fontSize: '14px' }}>
                            Z-Score: {spot.z_score}
                          </div>
                          <p>Significance: {strength}% confidence</p>
                        </div>
                      </Popup>
                    </CircleMarker>
                  );
                })}
          </>
        )}

        {/* ─── Heatmap Layer (H3 Hexagons) ─── */}
        {heatmapData && heatmapData.geojson && (
          heatmapData.geojson.features.map((f, i) => {
            const coords = f.geometry.coordinates[0].map(c => [c[1], c[0]]);
            const score = f.properties.score;
            return (
              <Polygon
                key={`hex-${i}`}
                positions={coords}
                pathOptions={{
                  fillColor: getScoreColor(score),
                  fillOpacity: 0.45,
                  color: getScoreColor(score),
                  weight: 1,
                  opacity: 0.6,
                }}
              >
                <Popup>
                  <div className="custom-popup">
                    <div className="popup-score" style={{ color: getScoreColor(score) }}>
                      {score.toFixed(1)}
                    </div>
                    <p>Grade: {f.properties.grade}</p>
                  </div>
                </Popup>
              </Polygon>
            );
          })
        )}

        {/* ─── Polygon Drawn Area Hexagons ─── */}
        {polygonData && polygonData.hexagons && (
          polygonData.hexagons.map((hex, i) => {
            const coords = hex.boundary.map(c => [c[0], c[1]]); // lat, lng
            return (
              <Polygon
                key={`polyhex-${i}`}
                positions={coords}
                pathOptions={{
                  fillColor: getScoreColor(hex.score),
                  fillOpacity: 0.5,
                  color: getScoreColor(hex.score),
                  weight: 2,
                  opacity: 0.8,
                }}
              >
                <Popup>
                  <div className="custom-popup">
                    <div className="popup-score" style={{ color: getScoreColor(hex.score) }}>
                      {hex.score.toFixed(1)}
                    </div>
                    <p>Grade: {hex.grade}</p>
                    <p style={{ fontSize: '10px', color: '#94a3b8' }}>Custom Polygon Hexagon</p>
                  </div>
                </Popup>
              </Polygon>
            );
          })
        )}

        {/* ─── Cluster Markers ─── */}
        {clusterData && clusterData.hot_spots && (
          clusterData.hot_spots.map((spot, i) => (
            <CircleMarker
              key={`hot-${i}`}
              center={[spot.center.lat, spot.center.lng]}
              radius={12 + spot.hex_count * 2}
              pathOptions={{
                fillColor: '#10b981',
                fillOpacity: 0.4,
                color: '#10b981',
                weight: 2,
                opacity: 0.8,
              }}
            >
              <Popup>
                <div className="custom-popup">
                  <h4>🔥 Hot Spot</h4>
                  <p>Avg Score: {spot.avg_score.toFixed(1)}</p>
                  <p>Hexagons: {spot.hex_count}</p>
                </div>
              </Popup>
            </CircleMarker>
          ))
        )}

        {clusterData && clusterData.cold_spots && (
          clusterData.cold_spots.map((spot, i) => (
            <CircleMarker
              key={`cold-${i}`}
              center={[spot.center.lat, spot.center.lng]}
              radius={12 + spot.hex_count * 2}
              pathOptions={{
                fillColor: '#3b82f6',
                fillOpacity: 0.3,
                color: '#3b82f6',
                weight: 2,
                opacity: 0.6,
                dashArray: '4, 4',
              }}
            >
              <Popup>
                <div className="custom-popup">
                  <h4>❄️ Cold Spot (Underserved)</h4>
                  <p>Avg Score: {spot.avg_score.toFixed(1)}</p>
                  <p>Hexagons: {spot.hex_count}</p>
                </div>
              </Popup>
            </CircleMarker>
          ))
        )}

        {/* ─── Isochrone Rings ─── */}
        {isochroneData && isochroneData.isochrones && (
          isochroneData.isochrones.map((iso, i) => {
            const coords = iso.polygon.coordinates[0].map(c => [c[1], c[0]]);
            return (
              <Polygon
                key={`iso-${i}`}
                positions={coords}
                pathOptions={{
                  fillColor: isoColors[i] || 'rgba(59,130,246,0.1)',
                  fillOpacity: 1,
                  color: isoBorders[i] || 'rgba(59,130,246,0.3)',
                  weight: 2,
                }}
              >
                <Popup>
                  <div className="custom-popup">
                    <h4>{iso.minutes} min {iso.mode === 'driving' ? 'drive' : iso.mode === 'transit' ? 'transit' : 'walk'}</h4>
                    <p>Radius: ~{iso.radius_km} km</p>
                    <p>Population: {iso.catchment.population.toLocaleString()}</p>
                  </div>
                </Popup>
              </Polygon>
            );
          })
        )}

        {/* ─── Pin Marker ─── */}
        {pinMarker && (
          <Marker 
            position={[pinMarker.lat, pinMarker.lng]}
            icon={getCustomPin(scoreData ? getScoreColor(scoreData.composite_score) : '#3b82f6')}
          >
            <Popup>
              <div className="custom-popup">
                <h4>📍 Selected Site</h4>
                <p>{pinMarker.lat.toFixed(4)}°N, {pinMarker.lng.toFixed(4)}°E</p>
                <p>Analysis Radius: {radiusKm} km</p>
                {scoreData && (
                  <p style={{ marginTop: '6px' }}>
                    Score: <strong style={{ color: getScoreColor(scoreData.composite_score) }}>
                      {scoreData.composite_score.toFixed(1)} / 100
                    </strong>
                  </p>
                )}
              </div>
            </Popup>
          </Marker>
        )}

        {/* ─── Compare Site Markers ─── */}
        {compareSites && compareSites.map((site, i) => (
          <CircleMarker
            key={`comp-${i}`}
            center={[site.lat, site.lng]}
            radius={10}
            pathOptions={{
              fillColor: getScoreColor(site.composite_score),
              fillOpacity: 0.9,
              color: '#fff',
              weight: 2,
            }}
          >
            <Popup>
              <div className="custom-popup">
                <h4>Site #{i + 1}</h4>
                <div className="popup-score" style={{ color: getScoreColor(site.composite_score) }}>
                  {site.composite_score.toFixed(1)}
                </div>
              </div>
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>

      {/* ─── Coordinate Display ─── */}
      <div className="coords-display">
        {coords.lat.toFixed(4)}°N, {coords.lng.toFixed(4)}°E
      </div>

      {/* ─── Instructions ─── */}
      {drawMode && (
        <div className="map-instructions">
          ✏️ Click to draw polygon points • Double-click to complete
        </div>
      )}

      {/* ─── Polygon Stats Overlay ─── */}
      {polygonData && !drawMode && (
        <div className="polygon-stats-overlay">
          <h4>Polygon Analysis</h4>
          <div className="poly-stat">
            <span>Avg Score:</span>
            <span style={{ color: getScoreColor(polygonData.avg_score), fontWeight: 'bold' }}>
              {polygonData.avg_score.toFixed(1)}
            </span>
          </div>
          <div className="poly-stat">
            <span>Hexagons Evaluated:</span>
            <span>{polygonData.count}</span>
          </div>
        </div>
      )}

      {/* ─── Legend ─── */}
      {heatmapData && (
        <div className="map-legend">
          <div className="map-legend-title">Score Legend</div>
          <div className="legend-item">
            <div className="legend-color" style={{ background: '#10b981' }} />
            <span>80+ Excellent</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ background: '#34d399' }} />
            <span>60-79 Good</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ background: '#fbbf24' }} />
            <span>40-59 Average</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ background: '#fb923c' }} />
            <span>25-39 Below Avg</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ background: '#ef4444' }} />
            <span>0-24 Poor</span>
          </div>
        </div>
      )}
    </div>
  );
}
