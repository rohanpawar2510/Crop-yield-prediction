/**
 * api.js — API call functions with mock data fallbacks
 * All fetch calls target backend endpoints. If the backend is unavailable,
 * realistic mock responses are returned so the dashboard remains demonstrable.
 */

// API_BASE is intentionally empty so requests use relative URLs,
// assuming the frontend is served from the same origin as the backend.
// Override this constant (or set via a config file) when deploying to
// a different origin, e.g. API_BASE = 'https://api.mysite.com'.
const API_BASE = '';

// ─── Mock responses ──────────────────────────────────────────────────────────

const MOCK_PREDICTION = {
  crop: 'Rice',
  yield: 4.2,
  unit: 'tons/hectare',
  confidence: 91,
  suitable_crops: ['Rice', 'Wheat', 'Maize', 'Soybean'],
  yield_comparison: [4.2, 3.8, 5.1, 2.9],
};

const MOCK_WEATHER = {
  location: 'Sample Location',
  temperature: 28,
  humidity: 65,
  rainfall: 120,
  wind_speed: 12,
  description: 'Partly Cloudy',
  icon: '⛅',
};

const MOCK_DISEASE = {
  detected: true,
  disease: 'Leaf Blight',
  confidence: 87,
  severity: 'Moderate',
  affected_area: '35%',
  treatment: 'Apply copper-based fungicide. Remove and destroy infected leaves. Ensure proper spacing between plants for air circulation.',
};

const MOCK_RECOMMENDATIONS = {
  fertilizer: {
    primary: 'NPK 20-10-10',
    amount: '150 kg/hectare',
    schedule: 'Apply at sowing and 30 days after germination',
    alternatives: ['Urea + DAP', 'Organic compost (5 ton/ha)'],
    distribution: { Nitrogen: 40, Phosphorus: 25, Potassium: 20, Organic: 15 },
  },
  crop_rotation: 'Follow Rice with Legumes (Lentil/Chickpea) next season to restore soil nitrogen.',
  irrigation: 'Maintain soil moisture at 60–70%. Irrigate every 5–7 days during dry spells.',
  pest_management: 'Monitor for stem borers. Use integrated pest management — neem-based sprays preferred.',
  general: 'Soil pH is slightly acidic. Consider liming (250 kg/ha of agricultural lime) to raise pH towards 6.5.',
};

// ─── Helper ───────────────────────────────────────────────────────────────────

/**
 * Wraps fetch with a timeout and returns parsed JSON.
 * @param {string} url
 * @param {RequestInit} options
 * @param {number} timeoutMs
 * @returns {Promise<any>}
 */
async function fetchWithTimeout(url, options = {}, timeoutMs = 10000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, { ...options, signal: controller.signal });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return await response.json();
  } finally {
    clearTimeout(timer);
  }
}

// ─── Public API functions ─────────────────────────────────────────────────────

/**
 * POST /api/predict
 * @param {{ location: string, nitrogen: number, phosphorus: number, potassium: number, ph: number }} data
 * @returns {Promise<typeof MOCK_PREDICTION>}
 */
export async function predictYield(data) {
  try {
    return await fetchWithTimeout(`${API_BASE}/api/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  } catch {
    console.warn('Yield prediction API unavailable — using mock data.');
    await simulateDelay(800);
    return { ...MOCK_PREDICTION };
  }
}

/**
 * GET /api/weather?location={location}
 * @param {string} location
 * @returns {Promise<typeof MOCK_WEATHER>}
 */
export async function fetchWeather(location) {
  try {
    const url = `${API_BASE}/api/weather?location=${encodeURIComponent(location)}`;
    return await fetchWithTimeout(url);
  } catch {
    console.warn('Weather API unavailable — using mock data.');
    await simulateDelay(600);
    return { ...MOCK_WEATHER, location };
  }
}

/**
 * POST /api/detect-disease
 * @param {File} imageFile
 * @returns {Promise<typeof MOCK_DISEASE>}
 */
export async function detectDisease(imageFile) {
  try {
    const formData = new FormData();
    formData.append('image', imageFile);
    const response = await fetch(`${API_BASE}/api/detect-disease`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  } catch {
    console.warn('Disease detection API unavailable — using mock data.');
    await simulateDelay(1200);
    return { ...MOCK_DISEASE };
  }
}

/**
 * POST /api/recommend
 * @param {object} data — combined soil, weather and prediction data
 * @returns {Promise<typeof MOCK_RECOMMENDATIONS>}
 */
export async function getRecommendations(data) {
  try {
    return await fetchWithTimeout(`${API_BASE}/api/recommend`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  } catch {
    console.warn('Recommendations API unavailable — using mock data.');
    await simulateDelay(1000);
    return { ...MOCK_RECOMMENDATIONS };
  }
}

// ─── Internal helpers ─────────────────────────────────────────────────────────

function simulateDelay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
