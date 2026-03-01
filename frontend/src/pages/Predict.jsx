import { useState } from 'react';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';
import PredictionForm from '../components/PredictionForm';
import NPKChart from '../components/NPKChart';
import SoilRadarChart from '../components/SoilRadarChart';
import YieldComparisonChart from '../components/YieldComparisonChart';
import FeatureImportanceChart from '../components/FeatureImportanceChart';
import { predictCrop } from '../services/api';

export default function Predict() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [npk, setNpk] = useState({ nitrogen: 0, phosphorus: 0, potassium: 0 });
  const [formData, setFormData] = useState(null);

  const handleSubmit = async (data) => {
    setLoading(true);
    try {
      const res = await predictCrop(data);
      setResult(res.data);
      setNpk({ nitrogen: data.nitrogen, phosphorus: data.phosphorus, potassium: data.potassium });
      setFormData(data);
      toast.success('Prediction complete!');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Prediction failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-8"
    >
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Crop Prediction 🌾</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">Enter soil & climate parameters to predict the best crop</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">Input Parameters</h2>
          <PredictionForm onSubmit={handleSubmit} loading={loading} />
        </div>

        <div className="space-y-6">
          {result ? (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="card text-center"
            >
              <div className="text-6xl mb-4">🌱</div>
              <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Recommended Crop</h3>
              <p className="text-4xl font-extrabold text-primary capitalize mb-4">
                {result.crop || result.predicted_crop || result.prediction}
              </p>
              {result.confidence != null && (
                <div className="mt-2">
                  <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">
                    Confidence: {result.confidence}%
                  </p>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                    <div
                      className="bg-primary h-3 rounded-full transition-all duration-700"
                      style={{ width: `${result.confidence}%` }}
                    />
                  </div>
                </div>
              )}
              {result.message && (
                <p className="mt-4 text-sm text-gray-500 dark:text-gray-400">{result.message}</p>
              )}
            </motion.div>
          ) : (
            <div className="card text-center py-16">
              <div className="text-6xl mb-4">🌾</div>
              <p className="text-gray-500 dark:text-gray-400">Fill in the parameters and click Predict</p>
            </div>
          )}
          <NPKChart nitrogen={npk.nitrogen} phosphorus={npk.phosphorus} potassium={npk.potassium} />
        </div>
      </div>

      {result && formData && (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
            >
              <SoilRadarChart
                nitrogen={formData.nitrogen}
                phosphorus={formData.phosphorus}
                potassium={formData.potassium}
                temperature={formData.temperature}
                humidity={formData.humidity}
                ph={formData.ph}
                rainfall={formData.rainfall}
              />
            </motion.div>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
            >
              <YieldComparisonChart
                suitable_crops={result.suitable_crops}
                yield_comparison={result.yield_comparison}
                predicted_crop={result.crop || result.predicted_crop || result.prediction}
              />
            </motion.div>
          </div>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <FeatureImportanceChart />
          </motion.div>
        </>
      )}
    </motion.div>
  );
}
