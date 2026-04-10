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

// ─── Season → encoded ID ──────────────────────────────────────────────────────
const SEASON_MAP = {
  'Kharif (June – Oct)': 1,
  'Rabi (Nov – Mar)':    2,
  'Zaid (Mar – Jun)':    3,
  'Annual':              4,
};

// ─── Irrigation → encoded ID ──────────────────────────────────────────────────
const IRRIGATION_MAP = {
  'Rainfed':   0,
  'Canal':     1,
  'Drip':      2,
  'Flood':     3,
  'Sprinkler': 4,
};

// ─── Soil → encoded ID ────────────────────────────────────────────────────────
const SOIL_MAP = {
  'Black':    0,
  'Alluvial': 1,
  'Sandy':    2,
  'Loamy':    3,
  'Clayey':   4,
};

const DISTRICTS   = Object.keys(DISTRICT_MAP);
const SEASONS     = Object.keys(SEASON_MAP);
const IRRIGATIONS = Object.keys(IRRIGATION_MAP);
const SOILS       = Object.keys(SOIL_MAP);

// ─── Validation rules ─────────────────────────────────────────────────────────
const FIELD_RULES = {
  nitrogen:    { min: 20,   max: 150,    step: 1,   label: 'Nitrogen (N)',   unit: 'kg/ha', hint: 'Low <60: poor soil · High >120: fertile' },
  phosphorus:  { min: 10,   max: 90,     step: 1,   label: 'Phosphorus (P)', unit: 'kg/ha', hint: 'Typical range for Maharashtra: 40–60' },
  potassium:   { min: 5,    max: 150,    step: 1,   label: 'Potassium (K)',  unit: 'kg/ha', hint: 'Most crops need 40–60 kg/ha' },
  ph:          { min: 5.5,  max: 8.5,    step: 0.1, label: 'pH Level',       unit: '',      hint: 'Ideal for most crops: 6.0–7.0' },
  area:        { min: 2,    max: 416127, step: 1,   label: 'Area',           unit: 'ha',    hint: 'Enter your farm size in hectares' },
};

const defaultValues = {
  district:    '',
  season:      '',
  irrigation:  '',
  soil:        '',
  nitrogen:    '',
  phosphorus:  '',
  potassium:   '',
  ph:          '',
  area:        '',
};

export default function PredictionForm({ onSubmit, loading }) {
  const [values, setValues]                 = useState(defaultValues);
  const [errors, setErrors]                 = useState({});
  const [weather, setWeather]               = useState(null);
  const [weatherLoading, setWeatherLoading] = useState(false);
  const [weatherError, setWeatherError]     = useState('');

  // ── Fetch weather when district changes ──────────────────────────────────
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
        setWeatherError('Could not fetch weather. Please check your connection.');
        setWeather(null);
      } finally {
        setWeatherLoading(false);
      }
    };

    fetchWeather();
  }, [values.district]);

  // ── Validation ────────────────────────────────────────────────────────────
  const validateField = (key, value) => {
    if (key === 'district')   return value ? '' : 'Please select a district';
    if (key === 'season')     return value ? '' : 'Please select a season';
    if (key === 'irrigation') return value ? '' : 'Please select irrigation type';
    if (key === 'soil')       return value ? '' : 'Please select soil type';

    const rule = FIELD_RULES[key];
    if (!rule) return '';
    if (value === '' || value === null || value === undefined)
      return `${rule.label} is required`;
    const num = parseFloat(value);
    if (isNaN(num))     return `${rule.label} must be a number`;
    if (num < rule.min) return `Min value is ${rule.min} ${rule.unit}`;
    if (num > rule.max) return `Max value is ${rule.max} ${rule.unit}`;
    return '';
  };

  const handleChange = (key, value) => {
    setValues(prev => ({ ...prev, [key]: value }));
    setErrors(prev => ({ ...prev, [key]: validateField(key, value) }));
  };

  // ── Submit ────────────────────────────────────────────────────────────────
  const handleSubmit = (e) => {
    e.preventDefault();

    const newErrors = {};
    Object.keys(defaultValues).forEach(key => {
      const err = validateField(key, values[key]);
      if (err) newErrors[key] = err;
    });
    if (!weather) {
      newErrors._weather = 'Weather data is required. Please select a district.';
    }
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    onSubmit({
      // Location
      location:        values.district,
      district:        DISTRICT_MAP[values.district],
      season:          SEASON_MAP[values.season],
      // Yield model inputs (new)
      irrigation_type: IRRIGATION_MAP[values.irrigation],
      soil_type:       SOIL_MAP[values.soil],
      // Soil nutrients
      nitrogen:        parseFloat(values.nitrogen),
      phosphorus:      parseFloat(values.phosphorus),
      potassium:       parseFloat(values.potassium),
      ph:              parseFloat(values.ph),
      area:            parseFloat(values.area),
      // Weather (from API)
      temperature:     parseFloat(weather.temperature),
      humidity:        parseFloat(weather.humidity),
      rainfall:        parseFloat(weather.rainfall),
      // Human-readable labels for display
      district_name:   values.district,
      season_name:     values.season,
      irrigation_name: values.irrigation,
      soil_name:       values.soil,
    });
  };

  const allFilled = Object.keys(defaultValues).every(k => values[k] !== '');
  const noErrors  = Object.keys(errors).filter(k => k !== '_weather').every(k => !errors[k]);
  const isValid   = allFilled && noErrors && !!weather && !weatherLoading;

  return (
    <form onSubmit={handleSubmit} className="space-y-6">

      {/* ── Section 1: Location & Season ── */}
      <div>
        <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-widest mb-3">
          Location & Season
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <FormField label="District" error={errors.district} hint="Select your Maharashtra district">
            <select
              value={values.district}
              onChange={e => handleChange('district', e.target.value)}
              disabled={loading}
              className={`input-field ${errors.district ? 'border-red-500' : ''}`}
            >
              <option value="">Select district...</option>
              {DISTRICTS.map(d => <option key={d} value={d}>{d}</option>)}
            </select>
          </FormField>

          <FormField label="Season" error={errors.season} hint="Kharif=monsoon · Rabi=winter · Zaid=summer">
            <select
              value={values.season}
              onChange={e => handleChange('season', e.target.value)}
              disabled={loading}
              className={`input-field ${errors.season ? 'border-red-500' : ''}`}
            >
              <option value="">Select season...</option>
              {SEASONS.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </FormField>
        </div>
      </div>

      {/* ── Weather Panel ── */}
      <AnimatePresence>
        {(weatherLoading || weather || weatherError || values.district) && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="rounded-xl border border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-950/40 p-4"
          >
            <div className="flex items-center gap-2 mb-3">
              <CloudRain size={16} className="text-blue-500" />
              <span className="text-sm font-semibold text-blue-700 dark:text-blue-300">
                Weather Data — Auto-fetched from OpenWeather API
              </span>
              {weatherLoading && <Loader2 size={14} className="animate-spin text-blue-400 ml-auto" />}
            </div>

            {weatherError && (
              <p className="text-red-500 text-xs">{weatherError}</p>
            )}

            {!weatherLoading && !weather && !weatherError && values.district && (
              <p className="text-gray-400 text-xs">Fetching weather for {values.district}...</p>
            )}

            {weather && !weatherLoading && (
              <div className="grid grid-cols-3 gap-3">
                <WeatherTile icon={<Thermometer size={14} />} label="Temperature" value={`${weather.temperature}°C`} color="orange" />
                <WeatherTile icon={<Droplets size={14} />}    label="Humidity"    value={`${weather.humidity}%`}     color="blue"   />
                <WeatherTile icon={<Wind size={14} />}        label="Rainfall"    value={`${weather.rainfall} mm`}   color="teal"   />
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Section 2: Farm Conditions (NEW) ── */}
      <div>
        <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-widest mb-3">
          Farm Conditions
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <FormField label="Irrigation Type" error={errors.irrigation}
            hint="Rainfed=no irrigation · Drip=high efficiency · Canal=river fed">
            <select
              value={values.irrigation}
              onChange={e => handleChange('irrigation', e.target.value)}
              disabled={loading}
              className={`input-field ${errors.irrigation ? 'border-red-500' : ''}`}
            >
              <option value="">Select irrigation...</option>
              {IRRIGATIONS.map(i => <option key={i} value={i}>{i}</option>)}
            </select>
          </FormField>

          <FormField label="Soil Type" error={errors.soil}
            hint="Black=cotton soil · Alluvial=river plains · Sandy=light soil">
            <select
              value={values.soil}
              onChange={e => handleChange('soil', e.target.value)}
              disabled={loading}
              className={`input-field ${errors.soil ? 'border-red-500' : ''}`}
            >
              <option value="">Select soil type...</option>
              {SOILS.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </FormField>
        </div>
      </div>

      {/* ── Section 3: Soil Nutrients ── */}
      <div>
        <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-widest mb-3">
          Soil Nutrients
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {['nitrogen', 'phosphorus', 'potassium'].map(key => {
            const rule = FIELD_RULES[key];
            return (
              <FormField key={key} label={rule.label} unit={rule.unit} error={errors[key]} hint={rule.hint}>
                <input
                  type="number"
                  value={values[key]}
                  onChange={e => handleChange(key, e.target.value)}
                  placeholder={`${rule.min}–${rule.max}`}
                  min={rule.min} max={rule.max} step={rule.step}
                  disabled={loading}
                  className={`input-field ${errors[key] ? 'border-red-500' : ''}`}
                />
              </FormField>
            );
          })}
        </div>
      </div>

      {/* ── Section 4: Soil Conditions ── */}
      <div>
        <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-widest mb-3">
          Soil Conditions
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {['ph', 'area'].map(key => {
            const rule = FIELD_RULES[key];
            return (
              <FormField key={key} label={rule.label} unit={rule.unit} error={errors[key]} hint={rule.hint}>
                <input
                  type="number"
                  value={values[key]}
                  onChange={e => handleChange(key, e.target.value)}
                  placeholder={`${rule.min}–${rule.max}`}
                  min={rule.min} max={rule.max} step={rule.step}
                  disabled={loading}
                  className={`input-field ${errors[key] ? 'border-red-500' : ''}`}
                />
              </FormField>
            );
          })}
        </div>
      </div>

      {/* ── Weather error ── */}
      {errors._weather && (
        <p className="text-red-500 text-sm text-center">{errors._weather}</p>
      )}

      {/* ── Submit ── */}
      <motion.button
        whileHover={{ scale: isValid ? 1.02 : 1 }}
        whileTap={{ scale: isValid ? 0.98 : 1 }}
        type="submit"
        disabled={loading || !isValid}
        className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? (
          <><Loader2 size={18} className="animate-spin" /> Predicting...</>
        ) : (
          '🌾 Predict Crop & Yield'
        )}
      </motion.button>

      {!weather && !weatherLoading && (
        <p className="text-center text-xs text-gray-400">
          Select a district first to auto-fetch temperature, humidity & rainfall
        </p>
      )}
    </form>
  );
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function FormField({ label, unit, error, hint, children }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
        {label}
        {unit && <span className="text-gray-400 text-xs ml-1">({unit})</span>}
      </label>
      {children}
      {error
        ? <p className="text-red-500 text-xs mt-1">⚠ {error}</p>
        : hint
          ? <p className="text-gray-400 text-xs mt-1">💡 {hint}</p>
          : null
      }
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
      <div className="flex items-center gap-1 mb-1 opacity-70">
        {icon}
        <span className="text-xs">{label}</span>
      </div>
      <p className="font-bold text-sm">{value}</p>
      <p className="text-xs opacity-60 mt-0.5">Read-only</p>
    </div>
  );
}