/**
 * app.js — Main application logic
 * Handles form submission, API orchestration, loading states, error handling
 * and populating all result sections of the dashboard.
 */

import { predictYield, fetchWeather, detectDisease, getRecommendations } from './api.js';
import { renderBarChart, renderRadarChart, renderPieChart } from './charts.js';

// ─── DOM references ───────────────────────────────────────────────────────────

const form          = document.getElementById('predictionForm');
const submitBtn     = document.getElementById('submitBtn');
const loadingOverlay = document.getElementById('loadingOverlay');
const resultsSection = document.getElementById('resultsSection');
const errorBanner   = document.getElementById('errorBanner');
const errorMessage  = document.getElementById('errorMessage');
const imagePreview  = document.getElementById('imagePreview');
const plantImageInput = document.getElementById('plantImage');

// ─── Init ─────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  setupImagePreview();
  setupTooltips();
  setupRangeInputs();
});

// ─── Image preview ────────────────────────────────────────────────────────────

function setupImagePreview() {
  if (!plantImageInput || !imagePreview) return;
  plantImageInput.addEventListener('change', () => {
    const file = plantImageInput.files[0];
    if (file && file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = e => {
        imagePreview.src = e.target.result;
        imagePreview.hidden = false;
      };
      reader.readAsDataURL(file);
    } else {
      imagePreview.hidden = true;
      imagePreview.src = '';
    }
  });
}

// ─── pH range visual feedback ─────────────────────────────────────────────────

function setupRangeInputs() {
  const phInput  = document.getElementById('ph');
  const phDisplay = document.getElementById('phDisplay');
  if (!phInput || !phDisplay) return;
  phInput.addEventListener('input', () => {
    const val = parseFloat(phInput.value);
    phDisplay.textContent = val.toFixed(1);
    // Colour coding
    if (val < 5.5)       phDisplay.className = 'ph-display acidic';
    else if (val > 7.5)  phDisplay.className = 'ph-display alkaline';
    else                 phDisplay.className = 'ph-display optimal';
  });
}

// ─── Tooltip setup ────────────────────────────────────────────────────────────

function setupTooltips() {
  document.querySelectorAll('[data-tooltip]').forEach(el => {
    const tip = document.createElement('span');
    tip.className = 'tooltip-text';
    tip.textContent = el.dataset.tooltip;
    el.classList.add('tooltip-wrap');
    el.appendChild(tip);
  });
}

// ─── Form submission ──────────────────────────────────────────────────────────

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  if (!validateForm()) return;

  hideError();
  showLoading();

  const formData = gatherFormData();

  try {
    // Run all API calls in parallel for speed
    const [prediction, weather, recommendations] = await Promise.all([
      predictYield(formData),
      fetchWeather(formData.location),
      getRecommendations(formData),
    ]);

    // Disease detection is optional (requires image)
    const imageFile = plantImageInput.files[0] || null;
    const disease = imageFile ? await detectDisease(imageFile) : null;

    displayResults({ prediction, weather, disease, recommendations, formData });
    renderCharts({ prediction, formData, recommendations });

    resultsSection.hidden = false;
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  } catch (err) {
    showError('Something went wrong. Please try again. ' + err.message);
  } finally {
    hideLoading();
  }
});

// ─── Form helpers ─────────────────────────────────────────────────────────────

function gatherFormData() {
  return {
    location:   document.getElementById('location').value.trim(),
    nitrogen:   parseFloat(document.getElementById('nitrogen').value),
    phosphorus: parseFloat(document.getElementById('phosphorus').value),
    potassium:  parseFloat(document.getElementById('potassium').value),
    ph:         parseFloat(document.getElementById('ph').value),
  };
}

function validateForm() {
  const fields = ['location', 'nitrogen', 'phosphorus', 'potassium', 'ph'];
  for (const id of fields) {
    const el = document.getElementById(id);
    const fieldLabel = document.querySelector(`label[for="${id}"]`)?.textContent?.trim() || id;
    if (!el || !el.value.trim()) {
      el?.focus();
      showError(`Please fill in the "${fieldLabel}" field.`);
      return false;
    }
  }
  const ph = parseFloat(document.getElementById('ph').value);
  if (ph < 0 || ph > 14) {
    showError('pH must be between 0 and 14.');
    return false;
  }
  return true;
}

// ─── Display helpers ──────────────────────────────────────────────────────────

function displayResults({ prediction, weather, disease, recommendations, formData }) {
  // Yield prediction
  document.getElementById('yieldValue').textContent   = prediction.yield ?? '—';
  document.getElementById('yieldUnit').textContent    = prediction.unit  ?? 'tons/hectare';
  document.getElementById('yieldCrop').textContent    = prediction.crop  ?? '—';
  document.getElementById('yieldConfidence').textContent = prediction.confidence
    ? `${prediction.confidence}% confidence`
    : '';

  // Weather
  document.getElementById('weatherLocation').textContent = weather.location || formData.location;
  document.getElementById('weatherIcon').textContent        = weather.icon ?? '🌤️';
  document.getElementById('weatherTemp').textContent        = `${weather.temperature}°C`;
  document.getElementById('weatherHumidity').textContent    = `${weather.humidity}%`;
  document.getElementById('weatherRainfall').textContent    = `${weather.rainfall} mm`;
  document.getElementById('weatherWind').textContent        = `${weather.wind_speed} km/h`;
  document.getElementById('weatherDesc').textContent        = weather.description ?? '';

  // Disease detection
  const diseaseSection = document.getElementById('diseaseSection');
  if (disease) {
    document.getElementById('diseaseName').textContent       = disease.disease ?? '—';
    document.getElementById('diseaseSeverity').textContent   = disease.severity ?? '—';
    document.getElementById('diseaseAffected').textContent   = disease.affected_area ?? '—';
    document.getElementById('diseaseTreatment').textContent  = disease.treatment ?? '—';
    setConfidenceBar('diseaseConfidenceBar', 'diseaseConfidenceVal', disease.confidence);
    diseaseSection.hidden = false;
  } else {
    diseaseSection.hidden = true;
  }

  // Recommendations
  const rec = recommendations.fertilizer || {};
  document.getElementById('recFertilizer').textContent   = `${rec.primary ?? ''} — ${rec.amount ?? ''}`;
  document.getElementById('recSchedule').textContent     = rec.schedule ?? '';
  document.getElementById('recRotation').textContent     = recommendations.crop_rotation ?? '';
  document.getElementById('recIrrigation').textContent   = recommendations.irrigation ?? '';
  document.getElementById('recPest').textContent         = recommendations.pest_management ?? '';
  document.getElementById('recGeneral').textContent      = recommendations.general ?? '';

  // Alternatives list
  const altList = document.getElementById('recAlternatives');
  altList.innerHTML = '';
  (rec.alternatives || []).forEach(alt => {
    const li = document.createElement('li');
    li.textContent = alt;
    altList.appendChild(li);
  });
}

function renderCharts({ prediction, formData, recommendations }) {
  // Bar chart — yield comparison
  renderBarChart({
    labels: prediction.suitable_crops || ['Rice', 'Wheat', 'Maize', 'Soybean'],
    data:   prediction.yield_comparison || [4.2, 3.8, 5.1, 2.9],
  });

  // Radar chart — soil nutrients
  renderRadarChart({
    n:  formData.nitrogen,
    p:  formData.phosphorus,
    k:  formData.potassium,
    ph: formData.ph,
  });

  // Pie chart — fertilizer distribution
  const dist = recommendations.fertilizer?.distribution || {};
  renderPieChart({
    labels: Object.keys(dist),
    data:   Object.values(dist),
  });
}

function setConfidenceBar(barId, valId, pct) {
  const bar = document.getElementById(barId);
  const val = document.getElementById(valId);
  if (!bar || !val) return;
  bar.style.width = `${pct}%`;
  val.textContent = `${pct}%`;
  bar.className = 'confidence-fill ' + (pct >= 80 ? 'high' : pct >= 50 ? 'medium' : 'low');
}

// ─── UI state helpers ─────────────────────────────────────────────────────────

function showLoading() {
  loadingOverlay.hidden = false;
  submitBtn.disabled = true;
  submitBtn.textContent = 'Analysing…';
}

function hideLoading() {
  loadingOverlay.hidden = true;
  submitBtn.disabled = false;
  submitBtn.textContent = '🌾 Predict & Analyse';
}

function showError(msg) {
  errorMessage.textContent = msg;
  errorBanner.hidden = false;
  errorBanner.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function hideError() {
  errorBanner.hidden = true;
}

// Close error banner on click
document.getElementById('closeError')?.addEventListener('click', hideError);
