import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Loader2, AlertTriangle, Leaf, Calendar, FlaskConical, Droplets, RotateCcw, Bug, Lightbulb, TrendingUp } from 'lucide-react';
import toast from 'react-hot-toast';
import NPKChart from '../components/NPKChart';
import { getRecommendations } from '../services/api';

// ─── Soil health score color ──────────────────────────────────────────────────
function scoreColor(score) {
  if (score >= 80) return 'text-green-600 dark:text-green-400';
  if (score >= 60) return 'text-yellow-600 dark:text-yellow-400';
  if (score >= 40) return 'text-orange-600 dark:text-orange-400';
  return 'text-red-600 dark:text-red-400';
}

function scoreBarColor(score) {
  if (score >= 80) return 'bg-green-500';
  if (score >= 60) return 'bg-yellow-500';
  if (score >= 40) return 'bg-orange-500';
  return 'bg-red-500';
}

// ─── NPK status badge ─────────────────────────────────────────────────────────
function StatusBadge({ status }) {
  const styles = {
    Deficient: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
    Optimal:   'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    Excess:    'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
    Medium:    'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  };
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${styles[status] || styles.Optimal}`}>
      {status}
    </span>
  );
}

// ─── Section card wrapper ─────────────────────────────────────────────────────
function Section({ icon, title, color = 'green', children }) {
  const colors = {
    green:  'border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-950/30',
    blue:   'border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-950/30',
    yellow: 'border-yellow-200 dark:border-yellow-800 bg-yellow-50 dark:bg-yellow-950/30',
    red:    'border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-950/30',
    purple: 'border-purple-200 dark:border-purple-800 bg-purple-50 dark:bg-purple-950/30',
    teal:   'border-teal-200 dark:border-teal-800 bg-teal-50 dark:bg-teal-950/30',
  };
  return (
    <div className={`rounded-xl border p-5 ${colors[color]}`}>
      <div className="flex items-center gap-2 mb-4">
        {icon}
        <h3 className="font-semibold text-gray-900 dark:text-white">{title}</h3>
      </div>
      {children}
    </div>
  );
}

export default function Recommend() {
  const [form, setForm] = useState({
    location: '', nitrogen: '', phosphorus: '', potassium: '', ph: '',
    crop: '', season: 'Kharif', soil_type: 'Black',
    irrigation_type: 'Rainfed', area: '', temperature: '25',
    rainfall: '800', predicted_yield: '0',
  });
  const [result, setResult]   = useState(null);
  const [loading, setLoading] = useState(false);

  const handleChange = (key, value) =>
    setForm(p => ({ ...p, [key]: value }));

  // ── Area change with max validation ──────────────────────────────────────
  const handleAreaChange = (e) => {
    const raw = e.target.value;
    if (raw === '') { handleChange('area', ''); return; }
    const v = parseFloat(raw);
    if (v > 500) {
      toast.error('Area cannot exceed 500 ha');
      handleChange('area', '500');
      return;
    }
    if (v < 0) { handleChange('area', '0.1'); return; }
    handleChange('area', raw);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // ── Validate area ────────────────────────────────────────────────────
    const areaVal = parseFloat(form.area);
    if (!areaVal || areaVal <= 0) {
      toast.error('Please enter a valid farm area (in hectares)');
      return;
    }
    if (areaVal > 500) {
      toast.error('Area cannot exceed 500 ha. Please enter a realistic value.');
      return;
    }

    setLoading(true);
    try {
      const payload = {
        location:        form.location,
        nitrogen:        parseFloat(form.nitrogen),
        phosphorus:      parseFloat(form.phosphorus),
        potassium:       parseFloat(form.potassium),
        ph:              parseFloat(form.ph),
        crop:            form.crop.trim() || 'Unknown',
        season:          form.season,
        soil_type:       form.soil_type,
        irrigation_type: form.irrigation_type,
        area:            Math.min(Math.max(parseFloat(form.area) || 1, 0.1), 500), // safety clamp
        temperature:     parseFloat(form.temperature) || 25,
        rainfall:        parseFloat(form.rainfall) || 800,
        predicted_yield: parseFloat(form.predicted_yield) || 0,
      };

      const res = await getRecommendations(payload);
      setResult(res.data);
      toast.success('Recommendations ready!');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to get recommendations');
    } finally {
      setLoading(false);
    }
  };

  const isValid = ['location', 'nitrogen', 'phosphorus', 'potassium', 'ph', 'area']
    .every(k => form[k] !== '');

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">

      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">AI Recommendations 🤖</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          Gemini AI-powered fertilizer & farming advice — crop-specific for Maharashtra
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">

        {/* ── Input Form ── */}
        <div className="card space-y-5">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Farm Parameters</h2>
          <form onSubmit={handleSubmit} className="space-y-4">

            {/* Location + Crop */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="field-label">Location</label>
                <input
                  type="text"
                  value={form.location}
                  onChange={e => handleChange('location', e.target.value)}
                  placeholder="e.g. Pune"
                  disabled={loading}
                  className="input-field"
                  required
                />
              </div>
              <div>
                <label className="field-label">Crop (from prediction)</label>
                <input
                  type="text"
                  value={form.crop}
                  onChange={e => handleChange('crop', e.target.value)}
                  placeholder="e.g. SUGARCANE"
                  disabled={loading}
                  className="input-field"
                />
              </div>
            </div>

            {/* Season + Soil */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="field-label">Season</label>
                <select
                  value={form.season}
                  onChange={e => handleChange('season', e.target.value)}
                  disabled={loading}
                  className="input-field"
                >
                  {['Kharif', 'Rabi', 'Zaid', 'Annual'].map(s =>
                    <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
              <div>
                <label className="field-label">Soil Type</label>
                <select
                  value={form.soil_type}
                  onChange={e => handleChange('soil_type', e.target.value)}
                  disabled={loading}
                  className="input-field"
                >
                  {['Black', 'Alluvial', 'Sandy', 'Loamy', 'Clayey'].map(s =>
                    <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
            </div>

            {/* Irrigation + Area */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="field-label">Irrigation Type</label>
                <select
                  value={form.irrigation_type}
                  onChange={e => handleChange('irrigation_type', e.target.value)}
                  disabled={loading}
                  className="input-field"
                >
                  {['Rainfed', 'Canal', 'Drip', 'Flood', 'Sprinkler'].map(i =>
                    <option key={i} value={i}>{i}</option>)}
                </select>
              </div>
              <div>
                <label className="field-label">
                  Area (ha)
                  <span className="text-xs text-gray-400 ml-1 font-normal">max 500</span>
                </label>
                <input
                  type="number"
                  value={form.area}
                  onChange={handleAreaChange}
                  placeholder="e.g. 2.5"
                  min="0.1"
                  max="500"
                  step="0.1"
                  disabled={loading}
                  className="input-field"
                  required
                />
              </div>
            </div>

            {/* NPK */}
            <div className="grid grid-cols-3 gap-3">
              {[
                { key: 'nitrogen',   label: 'N (kg/ha)', min: 20,  max: 150 },
                { key: 'phosphorus', label: 'P (kg/ha)', min: 10,  max: 90  },
                { key: 'potassium',  label: 'K (kg/ha)', min: 5,   max: 150 },
              ].map(({ key, label, min, max }) => (
                <div key={key}>
                  <label className="field-label">{label}</label>
                  <input
                    type="number"
                    value={form[key]}
                    onChange={e => handleChange(key, e.target.value)}
                    placeholder={`${min}–${max}`}
                    min={min}
                    max={max}
                    disabled={loading}
                    className="input-field"
                    required
                  />
                </div>
              ))}
            </div>

            {/* pH + Yield */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="field-label">pH Level</label>
                <input
                  type="number"
                  value={form.ph}
                  onChange={e => handleChange('ph', e.target.value)}
                  placeholder="5.5–8.5"
                  min="5.5"
                  max="8.5"
                  step="0.1"
                  disabled={loading}
                  className="input-field"
                  required
                />
              </div>
              <div>
                <label className="field-label">Predicted Yield (tons/ha)</label>
                <input
                  type="number"
                  value={form.predicted_yield}
                  onChange={e => handleChange('predicted_yield', e.target.value)}
                  placeholder="from prediction"
                  min="0"
                  step="0.1"
                  disabled={loading}
                  className="input-field"
                />
              </div>
            </div>

            <motion.button
              whileHover={{ scale: isValid ? 1.02 : 1 }}
              whileTap={{ scale: isValid ? 0.98 : 1 }}
              type="submit"
              disabled={loading || !isValid}
              className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {loading
                ? <><Loader2 size={18} className="animate-spin" /> Getting Recommendations...</>
                : '🤖 Get AI Recommendations'}
            </motion.button>
          </form>
        </div>

        {/* ── NPK Chart + Soil Health ── */}
        <div className="space-y-6">
          <NPKChart
            nitrogen={parseFloat(form.nitrogen) || 0}
            phosphorus={parseFloat(form.phosphorus) || 0}
            potassium={parseFloat(form.potassium) || 0}
          />

          {result && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
              className="card text-center">
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">Soil Health Score</p>
              <p className={`text-5xl font-extrabold mb-1 ${scoreColor(result.soil_health_score)}`}>
                {result.soil_health_score}
                <span className="text-2xl">/100</span>
              </p>
              <p className={`text-lg font-semibold mb-3 ${scoreColor(result.soil_health_score)}`}>
                {result.soil_health_label}
              </p>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${result.soil_health_score}%` }}
                  transition={{ duration: 1, ease: 'easeOut' }}
                  className={`h-4 rounded-full ${scoreBarColor(result.soil_health_score)}`}
                />
              </div>
            </motion.div>
          )}
        </div>
      </div>

      {/* ── Results ── */}
      <AnimatePresence>
        {result && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            className="space-y-6">

            {/* NPK Status */}
            <Section icon={<FlaskConical size={18} className="text-blue-500" />}
              title="NPK Deficiency Analysis" color="blue">
              <div className="space-y-4">
                {Object.entries(result.npk_status || {}).map(([key, val]) => (
                  <div key={key}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300 capitalize">
                        {key} — Current: {val.current} Kg/Ha | Required: {val.required} Kg/Ha
                      </span>
                      <StatusBadge status={val.status} />
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
                      <div
                        className={`h-2.5 rounded-full transition-all duration-700 ${
                          val.status === 'Optimal' ? 'bg-green-500' :
                          val.status === 'Excess'  ? 'bg-orange-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${Math.min((val.current / val.required) * 100, 100)}%` }}
                      />
                    </div>
                    {val.gap > 0 && val.status !== 'Optimal' && val.status !== 'Excess' && (
                      <p className="text-xs text-red-500 mt-1">
                        ⚠ Deficit: {val.gap} kg/ha — add fertilizer
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </Section>

            {/* Fertilizers */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

              {result.primary_fertilizer?.name && (
                <Section icon={<Leaf size={18} className="text-green-500" />}
                  title="Primary Fertilizer" color="green">
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Name</span>
                      <span className="font-semibold text-gray-900 dark:text-white">
                        {result.primary_fertilizer.name} ({result.primary_fertilizer.grade})
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Quantity/ha</span>
                      <span className="font-medium">{result.primary_fertilizer.quantity_per_ha}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Total</span>
                      <span className="font-medium">{result.primary_fertilizer.total_quantity}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Method</span>
                      <span className="font-medium text-right max-w-[60%]">
                        {result.primary_fertilizer.application_method}
                      </span>
                    </div>
                    <div className="flex justify-between border-t border-green-200 dark:border-green-800 pt-2 mt-2">
                      <span className="text-gray-500">Est. Cost</span>
                      <span className="font-bold text-green-600 dark:text-green-400 text-base">
                        ₹{result.primary_fertilizer.estimated_cost_inr?.toLocaleString('en-IN')}
                      </span>
                    </div>
                  </div>
                </Section>
              )}

              {result.secondary_fertilizer?.name && (
                <Section icon={<Leaf size={18} className="text-teal-500" />}
                  title="Secondary Fertilizer" color="teal">
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Name</span>
                      <span className="font-semibold text-gray-900 dark:text-white">
                        {result.secondary_fertilizer.name} ({result.secondary_fertilizer.grade})
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Quantity/ha</span>
                      <span className="font-medium">{result.secondary_fertilizer.quantity_per_ha}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Total</span>
                      <span className="font-medium">{result.secondary_fertilizer.total_quantity}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Method</span>
                      <span className="font-medium text-right max-w-[60%]">
                        {result.secondary_fertilizer.application_method}
                      </span>
                    </div>
                    <div className="flex justify-between border-t border-teal-200 dark:border-teal-800 pt-2 mt-2">
                      <span className="text-gray-500">Est. Cost</span>
                      <span className="font-bold text-teal-600 dark:text-teal-400 text-base">
                        ₹{result.secondary_fertilizer.estimated_cost_inr?.toLocaleString('en-IN')}
                      </span>
                    </div>
                  </div>
                </Section>
              )}
            </div>

            {/* Micronutrients */}
            {result.micronutrients?.length > 0 && (
              <Section icon={<FlaskConical size={18} className="text-purple-500" />}
                title="Micronutrient Recommendations" color="purple">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {result.micronutrients.map((m, i) => (
                    <div key={i} className="bg-white dark:bg-gray-800 rounded-lg p-3 border border-purple-100 dark:border-purple-900">
                      <p className="font-semibold text-sm text-gray-900 dark:text-white">{m.name}</p>
                      <p className="text-xs text-gray-500">{m.product} — {m.dose}</p>
                      <p className="text-xs text-purple-600 dark:text-purple-400 mt-1">💡 {m.reason}</p>
                    </div>
                  ))}
                </div>
              </Section>
            )}

            {/* Application Schedule */}
            {result.application_schedule?.length > 0 && (
              <Section icon={<Calendar size={18} className="text-yellow-500" />}
                title="Application Schedule" color="yellow">
                <div className="space-y-3">
                  {result.application_schedule.map((s, i) => (
                    <div key={i} className="flex gap-4 items-start">
                      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-yellow-500 text-white flex items-center justify-center text-sm font-bold">
                        {i + 1}
                      </div>
                      <div className="flex-1 bg-white dark:bg-gray-800 rounded-lg p-3 border border-yellow-100 dark:border-yellow-900">
                        <p className="font-semibold text-sm text-gray-900 dark:text-white">{s.stage}</p>
                        <p className="text-xs text-gray-500">⏰ {s.timing}</p>
                        <p className="text-xs text-gray-700 dark:text-gray-300 mt-1">
                          🌱 {s.fertilizers} — {s.quantity}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </Section>
            )}

            {/* Organic Alternatives */}
            {result.organic_alternatives?.length > 0 && (
              <Section icon={<Leaf size={18} className="text-green-600" />}
                title="Organic Alternatives" color="green">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {result.organic_alternatives.map((o, i) => (
                    <div key={i} className="bg-white dark:bg-gray-800 rounded-lg p-3 border border-green-100 dark:border-green-900 text-center">
                      <p className="font-semibold text-sm text-gray-900 dark:text-white">{o.name}</p>
                      <p className="text-xs text-gray-500 mt-1">{o.quantity}</p>
                      <p className="text-xs text-green-600 dark:text-green-400 mt-1">✅ {o.benefit}</p>
                    </div>
                  ))}
                </div>
              </Section>
            )}

            {/* Bottom row */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

              <Section icon={<Droplets size={18} className="text-blue-500" />}
                title="Irrigation Advice" color="blue">
                <p className="text-sm text-gray-700 dark:text-gray-300">{result.irrigation_advice}</p>
              </Section>

              <Section icon={<RotateCcw size={18} className="text-teal-500" />}
                title="Crop Rotation" color="teal">
                <p className="font-semibold text-gray-900 dark:text-white">{result.crop_rotation}</p>
                <p className="text-xs text-gray-500 mt-1">{result.crop_rotation_reason}</p>
              </Section>

              <Section icon={<TrendingUp size={18} className="text-green-500" />}
                title="Expected Yield Boost" color="green">
                <p className="text-2xl font-extrabold text-green-600 dark:text-green-400">
                  {result.expected_yield_boost}
                </p>
                <p className="text-xs text-gray-500 mt-1">with optimized fertilization</p>
              </Section>
            </div>

            {/* Pest Risk */}
            {result.pest_risk && (
              <Section icon={<Bug size={18} className="text-orange-500" />}
                title="Pest Risk Assessment" color="yellow">
                <p className="text-sm text-gray-700 dark:text-gray-300">{result.pest_risk}</p>
              </Section>
            )}

            {/* Warnings */}
            {result.warnings?.length > 0 && (
              <Section icon={<AlertTriangle size={18} className="text-red-500" />}
                title="Warnings & Precautions" color="red">
                <ul className="space-y-2">
                  {result.warnings.map((w, i) => (
                    <li key={i} className="flex gap-2 text-sm text-gray-700 dark:text-gray-300">
                      <span className="text-red-500 flex-shrink-0">⚠</span>
                      {w}
                    </li>
                  ))}
                </ul>
              </Section>
            )}

            {/* General Tips */}
            {result.general_tips && (
              <Section icon={<Lightbulb size={18} className="text-yellow-500" />}
                title="General Tips for Maharashtra Farmers" color="yellow">
                <p className="text-sm text-gray-700 dark:text-gray-300">{result.general_tips}</p>
              </Section>
            )}

          </motion.div>
        )}
      </AnimatePresence>

      {!result && !loading && (
        <div className="card text-center py-16">
          <div className="text-6xl mb-4">🤖</div>
          <p className="text-gray-500 dark:text-gray-400">
            Fill in the farm parameters above to get professional AI recommendations
          </p>
          <p className="text-sm text-gray-400 mt-2">
            💡 Tip: Run crop prediction first, then copy the crop name and yield here
          </p>
        </div>
      )}

    </motion.div>
  );
}