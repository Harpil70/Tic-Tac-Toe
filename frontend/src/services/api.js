/**
 * API service for communicating with the FastAPI backend.
 */
import axios from 'axios';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// ─── Layer APIs ─────────────────────────────────────────────────
export const fetchLayers = () => api.get('/layers').then(r => r.data);
export const fetchLayerData = (name) => api.get(`/layers/${name}`).then(r => r.data);

export const uploadLayer = (file, customName) => {
  const formData = new FormData();
  formData.append('file', file);
  if (customName) formData.append('layer_name', customName);
  
  return api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000, // May take larger files
  }).then(r => r.data);
};

// ─── Scoring APIs ───────────────────────────────────────────────
export const scorePoint = (lat, lng, weights = null, preset = null, radiusKm = 5) =>
  api.post('/score', { lat, lng, weights, preset, radius_km: radiusKm }).then(r => r.data);

export const scorePolygon = (polygon, weights = null, preset = null) =>
  api.post('/score/polygon', { polygon, weights, preset }).then(r => r.data);

// ─── Clustering APIs ─────────────────────────────────────────────
export const runClustering = (params = {}) => {
  const bounds = params.bounds || null;
  const boundsPayload = (bounds && bounds.minLat && bounds.maxLat && bounds.minLng && bounds.maxLng)
    ? { min_lat: bounds.minLat, max_lat: bounds.maxLat, min_lng: bounds.minLng, max_lng: bounds.maxLng }
    : null;

  return api.post('/cluster', {
    h3_resolution: params.resolution || 7,
    min_samples: params.minSamples || 3,
    eps_km: params.epsKm || 10,
    weights: params.weights || null,
    preset: params.preset || null,
    bounds: boundsPayload,
  }).then(r => r.data);
};

export const fetchHeatmap = (params = {}) => {
  const bounds = (params.minLat && params.maxLat && params.minLng && params.maxLng)
    ? {
        min_lat: params.minLat,
        max_lat: params.maxLat,
        min_lng: params.minLng,
        max_lng: params.maxLng
      }
    : null;

  return api.post('/h3/heatmap', {
    h3_resolution: params.resolution || 7,
    bounds: bounds,
    weights: params.weights || null,
    preset: params.preset || null,
  }).then(r => r.data);
};

// ─── Isochrone APIs ──────────────────────────────────────────────
export const fetchIsochrone = (lat, lng, mode = 'driving', intervals = [10, 20, 30]) =>
  api.post('/isochrone', { lat, lng, mode, intervals }).then(r => r.data);

// ─── Comparison APIs ─────────────────────────────────────────────
export const compareSites = (sites, weights = null, preset = null) =>
  api.post('/compare', { sites, weights, preset }).then(r => r.data);

// ─── Export APIs ─────────────────────────────────────────────────
export const exportReport = async (siteResults, format = 'pdf', weights = null, preset = null, title = 'Site Readiness Report') => {
  if (format === 'pdf' || format === 'excel') {
    try {
      const response = await api.post('/export', {
        pre_computed_results: siteResults,
        format, weights, preset, title,
      }, {
        responseType: 'blob',
        timeout: 60000,
      });

      const mimeType = format === 'pdf' 
        ? 'application/pdf' 
        : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
      const fileExt = format === 'pdf' ? 'pdf' : 'xlsx';

      const blob = new Blob([response.data], { type: mimeType });
      const url = window.URL.createObjectURL(blob);

      // Create a hidden anchor with download attribute
      const link = document.createElement('a');
      link.style.display = 'none';
      link.href = url;
      link.download = `site_readiness_report.${fileExt}`;
      document.body.appendChild(link);

      // Use setTimeout to ensure the link is in the DOM before clicking
      await new Promise((resolve) => {
        setTimeout(() => {
          link.click();
          resolve();
        }, 100);
      });

      // Clean up after a delay
      setTimeout(() => {
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      }, 5000);

      return { success: true };
    } catch (err) {
      console.error(`${format.toUpperCase()} export failed:`, err);
      throw err;
    }
  }

  // JSON format
  const response = await api.post('/export', { pre_computed_results: siteResults, format, weights, preset, title });
  return response.data;
};
// ─── Config APIs ─────────────────────────────────────────────────
export const fetchPresets = () => api.get('/presets').then(r => r.data);
export const fetchConfig = () => api.get('/config').then(r => r.data);
export const healthCheck = () => api.get('/health').then(r => r.data);

// ─── Smart Search API ────────────────────────────────────────────
export const smartSearch = (query, currentWeights = null, radiusKm = 5) =>
  api.post('/smart-search', { query, current_weights: currentWeights, radius_km: radiusKm }).then(r => r.data);

export default api;
