import { useState } from 'react';
import { motion } from 'framer-motion';
import { Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';
import RecommendationPanel from '../components/RecommendationPanel';
import NPKChart from '../components/NPKChart';
import { getRecommendations } from '../services/api';

export default function Recommend() {
  const [form, setForm] = useState({ location: '', nitrogen: '', phosphorus: '', potassium: '', ph: '' });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleChange = (key, value) => setForm((p) => ({ ...p, [key]: value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const data = {
        location: form.location,
        nitrogen: parseFloat(form.nitrogen),
        phosphorus: parseFloat(form.phosphorus),
        potassium: parseFloat(form.potassium),
        ph: parseFloat(form.ph),
      };
      const res = await getRecommendations(data);
      setResult(res.data);
      toast.success('Recommendations ready!');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to get recommendations');
    } finally {
      setLoading(false);
    }
  };

  const isValid = Object.values(form).every((v) => v !== '');

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-8"
    >
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">AI Recommendations 🤖</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">Get Gemini AI-powered farming recommendations</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">Farm Parameters</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            {[
              { key: 'location', label: 'Location', type: 'text', placeholder: 'e.g. Maharashtra, India' },
              { key: 'nitrogen', label: 'Nitrogen (N)', type: 'number', placeholder: '0-140' },
              { key: 'phosphorus', label: 'Phosphorus (P)', type: 'number', placeholder: '5-145' },
              { key: 'potassium', label: 'Potassium (K)', type: 'number', placeholder: '5-205' },
              { key: 'ph', label: 'pH Level', type: 'number', placeholder: '3.5-9.9', step: '0.1' },
            ].map(({ key, label, type, placeholder, step }) => (
              <div key={key}>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{label}</label>
                <input
                  type={type}
                  value={form[key]}
                  onChange={(e) => handleChange(key, e.target.value)}
                  placeholder={placeholder}
                  step={step}
                  required
                  disabled={loading}
                  className="input-field"
                />
              </div>
            ))}
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              type="submit"
              disabled={loading || !isValid}
              className="btn-primary w-full flex items-center justify-center gap-2"
            >
              {loading ? (
                <><Loader2 size={18} className="animate-spin" /> Getting Recommendations...</>
              ) : (
                'Get AI Recommendations'
              )}
            </motion.button>
          </form>
        </div>

        <div className="space-y-6">
          <NPKChart
            nitrogen={parseFloat(form.nitrogen) || 0}
            phosphorus={parseFloat(form.phosphorus) || 0}
            potassium={parseFloat(form.potassium) || 0}
          />
          {result && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <RecommendationPanel data={result} />
            </motion.div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
