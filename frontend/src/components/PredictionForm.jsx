import { useState } from 'react';
import { motion } from 'framer-motion';
import { Loader2 } from 'lucide-react';

const defaultValues = {
  location: '',
  nitrogen: '',
  phosphorus: '',
  potassium: '',
  temperature: '',
  ph: '',
  rainfall: '',
  district: '',
  season: '',
  area: '',
};

export default function PredictionForm({ onSubmit, loading }) {
  const [values, setValues] = useState(defaultValues);

  const fields = [
    { key: 'location', label: 'Location', placeholder: 'e.g. Pune, Maharashtra', type: 'text' },
    { key: 'nitrogen', label: 'Nitrogen (N)', placeholder: '0-140', min: 0, max: 140 },
    { key: 'phosphorus', label: 'Phosphorus (P)', placeholder: '5-145', min: 0, max: 145 },
    { key: 'potassium', label: 'Potassium (K)', placeholder: '5-205', min: 0, max: 205 },
    { key: 'temperature', label: 'Temperature (°C)', placeholder: '8-44', min: 0, max: 50 },
    { key: 'district', label: 'District', type: 'select', options: ['Pune', 'Nashik', 'Aurangabad', 'Nagpur', 'Amravati', 'Kolhapur', 'Solapur', 'Sangli', 'Satara', 'Ratnagiri', 'Sindhudurg', 'Jalgaon', 'Buldhana', 'Akola', 'Washim', 'Yavatmal', 'Wardha', 'Chandrapur', 'Gondiya', 'Bhandara'] },
    { key: 'season', label: 'Season', type: 'select', options: ['Summer', 'Monsoon', 'Winter'] },
    { key: 'area', label: 'Area (hectares)', placeholder: '0-10000', min: 0, max: 10000 },
    { key: 'ph', label: 'pH Level', placeholder: '3.5-9.9', min: 0, max: 14, step: 0.1 },
    { key: 'rainfall', label: 'Rainfall (mm)', placeholder: '20-300', min: 0, max: 500 },
  ];

  const handleChange = (key, value) => {
    setValues((prev) => ({ ...prev, [key]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const selectKeys = new Set(['location', 'district', 'season']);
    const data = {};
    for (const [k, v] of Object.entries(values)) {
      if (selectKeys.has(k)) {
        data[k] = v;
      } else {
        data[k] = parseFloat(v);
      }
    }
    onSubmit(data);
  };

  const isValid =
    values.location.trim() !== '' &&
    values.district !== '' &&
    values.season !== '' &&
    Object.entries(values)
      .filter(([k]) => !['location', 'district', 'season'].includes(k))
      .every(([, v]) => v !== '' && !isNaN(parseFloat(v)));

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {fields.map(({ key, label, placeholder, type, min, max, step, options }) => (
          <div key={key}>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {label}
            </label>
            {type === 'select' ? (
              <select
                value={values[key]}
                onChange={(e) => handleChange(key, e.target.value)}
                required
                disabled={loading}
                className="input-field"
              >
                <option value="">Select {label}</option>
                {options.map((opt) => (
                  <option key={opt} value={opt}>{opt}</option>
                ))}
              </select>
            ) : (
              <input
                type={type ?? 'number'}
                value={values[key]}
                onChange={(e) => handleChange(key, e.target.value)}
                placeholder={placeholder}
                min={min}
                max={max}
                step={step ?? 1}
                required
                disabled={loading}
                className="input-field"
              />
            )}
          </div>
        ))}
      </div>
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        type="submit"
        disabled={loading || !isValid}
        className="btn-primary w-full flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <Loader2 size={18} className="animate-spin" />
            Predicting...
          </>
        ) : (
          'Predict Crop Yield'
        )}
      </motion.button>
    </form>
  );
}
