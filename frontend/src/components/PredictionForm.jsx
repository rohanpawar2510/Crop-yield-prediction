import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Loader2, CloudRain, Thermometer, Droplets, Wind } from 'lucide-react';

// ─── District → encoded ID ────────────────────────────────────────────────────
const DISTRICT_MAP = {
  'Ahmednagar': 0,  'Akola': 1,       'Amravati': 2,    'Aurangabad': 3,
  'Beed': 4,        'Bhandara': 5,    'Buldhana': 6,    'Chandrapur': 7,
  'Dhule': 8,       'Gadchiroli': 9,  'Gondia': 10,     'Hingoli': 11,
  'Jalgaon': 12,    'Jalna': 13,      'Kolhapur': 14,   'Latur': 15,
  'Mumbai': 17,     'Nagpur': 18,     'Nanded': 19,     'Nandurbar': 20,
  'Nashik': 21,     'Osmanabad': 22,  'Palghar': 23,    'Parbhani': 24,
  'Pune': 25,       'Raigad': 26,     'Ratnagiri': 27,  'Sangli': 28,
  'Satara': 29,     'Sindhudurg': 30, 'Solapur': 31,    'Thane': 32,
  'Wardha': 33,     'Washim': 34,     'Yavatmal': 35,
};

const SEASON_MAP = {
  'Kharif (June – Oct)': 1,
  'Rabi (Nov – Mar)':    2,
  'Zaid (Mar – Jun)':    3,
  'Annual':              4,
};

const IRRIGATION_MAP = {
  'Rainfed': 0, 'Canal': 1, 'Drip': 2, 'Flood': 3, 'Sprinkler': 4,
};

const SOIL_MAP = {
  'Black': 0, 'Alluvial': 1, 'Sandy': 2, 'Loamy': 3, 'Clayey': 4,
};

const DISTRICTS   = Object.keys(DISTRICT_MAP);
const SEASONS     = Object.keys(SEASON_MAP);
const IRRIGATIONS = Object.keys(IRRIGATION_MAP);
const SOILS       = Object.keys(SOIL_MAP);

const FIELD_RULES = {
  nitrogen:   { min: 20,  max: 150,    step: 1,   label: 'Nitrogen (N)',   unit: 'kg/ha' },
  phosphorus: { min: 10,  max: 90,     step: 1,   label: 'Phosphorus (P)', unit: 'kg/ha' },
  potassium:  { min: 5,   max: 150,    step: 1,   label: 'Potassium (K)',  unit: 'kg/ha' },
  ph:         { min: 5.5, max: 8.5,    step: 0.1, label: 'pH Level',       unit: ''      },
  area:       { min: 2,   max: 416127, step: 1,   label: 'Area',           unit: 'ha'    },
};

const defaultValues = {
  district: '', season: '', irrigation: '', soil: '',
  nitrogen: '', phosphorus: '', potassium: '', ph: '', area: '',
};

export default function PredictionForm({ onSubmit, loading }) {
  const [values, setValues]                 = useState(defaultValues);
  const [errors, setErrors]                 = useState({});
  const [weather, setWeather]               = useState(null);
  const [weatherLoading, setWeatherLoading] = useState(false);
  const [weatherError, setWeatherError]     = useState('');
  const [useCustomWeather, setUseCustomWeather] = useState(false);
  const [customWeather, setCustomWeather]   = useState({ temperature: '', humidity: '', rainfall: '' });

  useEffect(() => {
    if (!values.district) { setWeather(null); return; }
    const fetchWeather = async () => {
      setWeatherLoading(true);
      setWeatherError('');
      try {
        const res  = await fetch(`/api/weather?location=${encodeURIComponent(values.district)}`);
        if (!res.ok) throw new Error('Weather fetch failed');
        const data = await res.json();
        setWeather({
          temperature: data.temperature ?? data.temp ?? '',
          humidity:    data.humidity    ?? '',
          rainfall:    data.rainfall    ?? data.precipitation ?? '',
        });
      } catch {
        setWeatherError('Could not fetch weather.');
        setWeather(null);
      } finally {
        setWeatherLoading(false);
      }
    };
    fetchWeather();
  }, [values.district]);

  const validateField = (key, value) => {
    if (['district', 'season', 'irrigation', 'soil'].includes(key))
      return value ? '' : `Required`;
    const rule = FIELD_RULES[key];
    if (!rule) return '';
    if (value === '') return `${rule.label} is required`;
    const num = parseFloat(value);
    if (isNaN(num))     return `Must be a number`;
    if (num < rule.min) return `Min: ${rule.min} ${rule.unit}`;
    if (num > rule.max) return `Max: ${rule.max} ${rule.unit}`;
    return '';
  };

  const handleChange = (key, value) => {
    setValues(prev => ({ ...prev, [key]: value }));
    setErrors(prev => ({ ...prev, [key]: validateField(key, value) }));
  };

  const validateCustomWeather = () => {
    if (!useCustomWeather) return true;
    const t = parseFloat(customWeather.temperature);
    const h = parseFloat(customWeather.humidity);
    const r = parseFloat(customWeather.rainfall);
    return !isNaN(t) && t >= 10 && t <= 40 &&
           !isNaN(h) && h >= 0  && h <= 100 &&
           !isNaN(r) && r >= 0  && r <= 2000;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const newErrors = {};
    Object.keys(defaultValues).forEach(key => {
      const err = validateField(key, values[key]);
      if (err) newErrors[key] = err;
    });
    const activeWeather = useCustomWeather ? customWeather : weather;
    if (!activeWeather) newErrors._weather = 'Weather data is required. Select a district.';
    if (!validateCustomWeather()) newErrors._weather = 'Custom weather values out of range.';
    if (Object.keys(newErrors).length > 0) { setErrors(newErrors); return; }

    onSubmit({
      location:        values.district,
      district:        DISTRICT_MAP[values.district],
      season:          SEASON_MAP[values.season],
      irrigation_type: IRRIGATION_MAP[values.irrigation],
      soil_type:       SOIL_MAP[values.soil],
      nitrogen:        parseFloat(values.nitrogen),
      phosphorus:      parseFloat(values.phosphorus),
      potassium:       parseFloat(values.potassium),
      ph:              parseFloat(values.ph),
      area:            parseFloat(values.area),
      temperature:     parseFloat(activeWeather.temperature),
      humidity:        parseFloat(activeWeather.humidity),
      rainfall:        parseFloat(activeWeather.rainfall),
      district_name:   values.district,
      season_name:     values.season,
      irrigation_name: values.irrigation,
      soil_name:       values.soil,
      weather_source:  useCustomWeather ? 'custom' : 'api',
    });
  };

  const allFilled    = Object.keys(defaultValues).every(k => values[k] !== '');
  const noErrors     = Object.keys(errors).filter(k => k !== '_weather').every(k => !errors[k]);
  const weatherValid = !!((useCustomWeather && validateCustomWeather()) || (!useCustomWeather && weather));
  const isValid      = allFilled && noErrors && weatherValid && !weatherLoading;

  return (
    <form onSubmit={handleSubmit} className="space-y-5">

      {/* ── Location & Season ── */}
      <Section label="Location & Season">
        <div className="grid grid-cols-2 gap-3">
          <Field label="District" error={errors.district}>
            <select value={values.district} onChange={e => handleChange('district', e.target.value)}
              disabled={loading} className={`input-field ${errors.district ? 'border-red-500' : ''}`}>
              <option value="">Select district...</option>
              {DISTRICTS.map(d => <option key={d} value={d}>{d}</option>)}
            </select>
          </Field>
          <Field label="Season" error={errors.season}>
            <select value={values.season} onChange={e => handleChange('season', e.target.value)}
              disabled={loading} className={`input-field ${errors.season ? 'border-red-500' : ''}`}>
              <option value="">Select season...</option>
              {SEASONS.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </Field>
        </div>
      </Section>

      {/* ── Weather Panel ── */}
      <AnimatePresence>
        {values.district && (
          <motion.div initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
            className="rounded-xl border border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-950/40 p-4">

            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <CloudRain size={15} className="text-blue-500" />
                <span className="text-xs font-semibold text-blue-700 dark:text-blue-300">
                  {useCustomWeather ? 'Custom Weather' : 'Live Weather — ' + values.district}
                </span>
              </div>
              {weatherLoading && <Loader2 size={13} className="animate-spin text-blue-400" />}
            </div>

            {weatherError && <p className="text-red-500 text-xs mb-2">{weatherError}</p>}

            {weather && !weatherLoading && !useCustomWeather && (
              <div className="grid grid-cols-3 gap-2 mb-3">
                <WeatherTile icon={<Thermometer size={13} />} label="Temp"     value={`${weather.temperature}°C`} color="orange" />
                <WeatherTile icon={<Droplets size={13} />}    label="Humidity" value={`${weather.humidity}%`}     color="blue"   />
                <WeatherTile icon={<Wind size={13} />}        label="Rainfall" value={`${weather.rainfall} mm`}   color="teal"   />
              </div>
            )}

            {weather && (
              <div className="flex items-center gap-2 pt-2 border-t border-blue-200 dark:border-blue-700">
                <button type="button" onClick={() => setUseCustomWeather(!useCustomWeather)}
                  className={`text-xs px-3 py-1 rounded-full border transition-all font-medium ${
                    useCustomWeather
                      ? 'bg-orange-100 border-orange-400 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300'
                      : 'border-gray-300 text-gray-500 hover:border-orange-400 dark:border-gray-600 dark:text-gray-400'
                  }`}>
                  {useCustomWeather ? '⚙️ Custom (active)' : '✏️ Override weather'}
                </button>
              </div>
            )}

            <AnimatePresence>
              {useCustomWeather && (
                <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }} className="mt-3">
                  <div className="grid grid-cols-3 gap-3 p-3 rounded-lg border border-orange-200 bg-orange-50 dark:bg-orange-950/30 dark:border-orange-800">
                    {[
                      { key: 'temperature', label: 'Temperature (°C)', placeholder: '10–40',   min: 10,  max: 40,   step: 0.1 },
                      { key: 'humidity',    label: 'Humidity (%)',      placeholder: '0–100',   min: 0,   max: 100,  step: 1   },
                      { key: 'rainfall',    label: 'Rainfall (mm)',     placeholder: '0–2000',  min: 0,   max: 2000, step: 1   },
                    ].map(({ key, label, placeholder, min, max, step }) => (
                      <div key={key}>
                        <label className="block text-xs font-medium text-gray-600 dark:text-gray-300 mb-1">{label}</label>
                        <input type="number" value={customWeather[key]}
                          onChange={e => setCustomWeather(p => ({ ...p, [key]: e.target.value }))}
                          placeholder={placeholder} min={min} max={max} step={step}
                          className="input-field w-full" />
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Farm Conditions ── */}
      <Section label="Farm Conditions">
        <div className="grid grid-cols-2 gap-3">
          <Field label="Irrigation Type" error={errors.irrigation}>
            <select value={values.irrigation} onChange={e => handleChange('irrigation', e.target.value)}
              disabled={loading} className={`input-field ${errors.irrigation ? 'border-red-500' : ''}`}>
              <option value="">Select irrigation...</option>
              {IRRIGATIONS.map(i => <option key={i} value={i}>{i}</option>)}
            </select>
          </Field>
          <Field label="Soil Type" error={errors.soil}>
            <select value={values.soil} onChange={e => handleChange('soil', e.target.value)}
              disabled={loading} className={`input-field ${errors.soil ? 'border-red-500' : ''}`}>
              <option value="">Select soil type...</option>
              {SOILS.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </Field>
        </div>
      </Section>

      {/* ── Soil Nutrients ── */}
      <Section label="Soil Nutrients">
        <div className="grid grid-cols-3 gap-3">
          {['nitrogen', 'phosphorus', 'potassium'].map(key => {
            const r = FIELD_RULES[key];
            return (
              <Field key={key} label={`${r.label} (${r.unit})`} error={errors[key]}>
                <input type="number" value={values[key]}
                  onChange={e => handleChange(key, e.target.value)}
                  placeholder={`${r.min}–${r.max}`} min={r.min} max={r.max} step={r.step}
                  disabled={loading} className={`input-field ${errors[key] ? 'border-red-500' : ''}`} />
              </Field>
            );
          })}
        </div>
      </Section>

      {/* ── Soil Conditions ── */}
      <Section label="Soil Conditions">
        <div className="grid grid-cols-2 gap-3">
          {['ph', 'area'].map(key => {
            const r = FIELD_RULES[key];
            return (
              <Field key={key} label={r.unit ? `${r.label} (${r.unit})` : r.label} error={errors[key]}>
                <input type="number" value={values[key]}
                  onChange={e => handleChange(key, e.target.value)}
                  placeholder={`${r.min}–${r.max}`} min={r.min} max={r.max} step={r.step}
                  disabled={loading} className={`input-field ${errors[key] ? 'border-red-500' : ''}`} />
              </Field>
            );
          })}
        </div>
      </Section>

      {/* ── Weather error ── */}
      {errors._weather && (
        <p className="text-red-500 text-xs text-center">{errors._weather}</p>
      )}

      {/* ── Submit ── */}
      <motion.button
        whileHover={{ scale: isValid ? 1.02 : 1 }}
        whileTap={{ scale: isValid ? 0.98 : 1 }}
        type="submit" disabled={loading || !isValid}
        className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed">
        {loading
          ? <><Loader2 size={18} className="animate-spin" /> Predicting...</>
          : '🌾 Predict Crop & Yield'}
      </motion.button>

    </form>
  );
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function Section({ label, children }) {
  return (
    <div>
      <p className="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider mb-2">
        {label}
      </p>
      {children}
    </div>
  );
}

function Field({ label, error, children }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
        {label}
      </label>
      {children}
      {error && <p className="text-red-500 text-xs mt-1">⚠ {error}</p>}
    </div>
  );
}

function WeatherTile({ icon, label, value, color }) {
  const colors = {
    orange: 'text-orange-600 dark:text-orange-400 bg-orange-100 dark:bg-orange-900/30',
    blue:   'text-blue-600   dark:text-blue-400   bg-blue-100   dark:bg-blue-900/30',
    teal:   'text-teal-600   dark:text-teal-400   bg-teal-100   dark:bg-teal-900/30',
  };
  return (
    <div className={`rounded-lg px-3 py-2 ${colors[color]}`}>
      <div className="flex items-center gap-1 mb-1 opacity-60">
        {icon}
        <span className="text-xs">{label}</span>
      </div>
      <p className="font-bold text-sm">{value}</p>
    </div>
  );
}