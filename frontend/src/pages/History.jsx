import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  History as HistoryIcon,
  Leaf,
  FlaskConical,
  Trash2,
  ChevronRight,
  TrendingUp,
  Award,
  Calendar,
  Loader2
} from 'lucide-react';

import toast from 'react-hot-toast';

import {
  getPredictions,
  getRecommendationsList,
  deletePrediction,
  deleteRecommendation,
  getStats,

  // ✅ Disease APIs Added
  getDiseaseHistory,
  deleteDiseaseDetection,

} from '../services/api';

import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

const SEASON_LABELS = {
  1: 'Kharif',
  2: 'Rabi',
  3: 'Zaid',
  4: 'Annual'
};

const IRR_LABELS = {
  0: 'Rainfed',
  1: 'Canal',
  2: 'Drip',
  3: 'Flood',
  4: 'Sprinkler'
};

function StatCard({ icon, label, value, color = 'green' }) {
  const colors = {
    green: 'bg-green-500/10 border-green-500/20 text-green-400',
    blue: 'bg-blue-500/10 border-blue-500/20 text-blue-400',
    yellow: 'bg-yellow-500/10 border-yellow-500/20 text-yellow-400',
    purple: 'bg-purple-500/10 border-purple-500/20 text-purple-400',
  };

  return (
    <div className={`rounded-xl border p-4 ${colors[color]}`}>
      <div className="flex items-center gap-2 mb-1">
        {icon}
        <span className="text-xs font-medium opacity-70">
          {label}
        </span>
      </div>

      <p className="text-2xl font-bold">
        {value ?? '—'}
      </p>
    </div>
  );
}

function PredictionCard({ item, onDelete }) {
  const [deleting, setDeleting] = useState(false);

  const handleDelete = async () => {
    if (!confirm('Delete this prediction?')) return;

    setDeleting(true);

    try {
      await deletePrediction(item.id);

      onDelete(item.id);

      toast.success('Prediction deleted');
    } catch {
      toast.error('Failed to delete');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: -20 }}
      className="bg-gray-900 border border-gray-800 rounded-xl p-4 hover:border-gray-700 transition"
    >
      <div className="flex items-start justify-between gap-3">

        <div className="flex-1 min-w-0">

          <div className="flex items-center gap-2 mb-2">

            <span className="text-lg font-bold text-green-400">
              {item.recommended_crop}
            </span>

            <span className="text-xs bg-green-500/10 text-green-400 border border-green-500/20 px-2 py-0.5 rounded-full">
              {item.confidence?.toFixed(1)}% confidence
            </span>

          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs text-gray-400">

            <span>
              📍 {item.location || 'Unknown'}
            </span>

            <span>
              🌾 Yield:
              <strong className="text-gray-200">
                {' '}
                {item.predicted_yield?.toFixed(2)} t/ha
              </strong>
            </span>

            <span>
              💧 N:{item.nitrogen} P:{item.phosphorus} K:{item.potassium}
            </span>

            <span>
              📅 {new Date(item.created_at).toLocaleDateString('en-IN')}
            </span>

          </div>
        </div>

        <button
          onClick={handleDelete}
          disabled={deleting}
          className="p-2 text-gray-600 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition flex-shrink-0"
        >
          {deleting ? (
            <Loader2 size={14} className="animate-spin" />
          ) : (
            <Trash2 size={14} />
          )}
        </button>

      </div>
    </motion.div>
  );
}

function RecommendationCard({ item, onDelete }) {
  const [deleting, setDeleting] = useState(false);

  const handleDelete = async () => {
    if (!confirm('Delete this recommendation?')) return;

    setDeleting(true);

    try {
      await deleteRecommendation(item.id);

      onDelete(item.id);

      toast.success('Recommendation deleted');
    } catch {
      toast.error('Failed to delete');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: -20 }}
      className="bg-gray-900 border border-gray-800 rounded-xl p-4 hover:border-gray-700 transition"
    >
      <div className="flex items-start justify-between gap-3">

        <div className="flex-1 min-w-0">

          <div className="flex items-center gap-2 mb-2">

            <span className="text-lg font-bold text-blue-400">
              {item.crop}
            </span>

            <span className={`text-xs px-2 py-0.5 rounded-full border ${
              item.soil_health_label === 'Good' ||
              item.soil_health_label === 'Excellent'
                ? 'bg-green-500/10 text-green-400 border-green-500/20'
                : 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'
            }`}>
              Soil: {item.soil_health_label} ({item.soil_health_score}/100)
            </span>

          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs text-gray-400">

            <span>
              📍 {item.location || 'Unknown'}
            </span>

            <span>
              🌱 Season: {item.season}
            </span>

            <span>
              📈 Boost:
              <strong className="text-gray-200">
                {' '}
                {item.expected_yield_boost}
              </strong>
            </span>

            <span>
              📅 {new Date(item.created_at).toLocaleDateString('en-IN')}
            </span>

          </div>
        </div>

        <button
          onClick={handleDelete}
          disabled={deleting}
          className="p-2 text-gray-600 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition flex-shrink-0"
        >
          {deleting ? (
            <Loader2 size={14} className="animate-spin" />
          ) : (
            <Trash2 size={14} />
          )}
        </button>

      </div>
    </motion.div>
  );
}


// ✅ Disease Card Added

function DiseaseCard({ item, onDelete }) {
  const [deleting, setDeleting] = useState(false);

  const handleDelete = async () => {
    if (!confirm('Delete this disease detection?')) return;

    setDeleting(true);

    try {
      await deleteDiseaseDetection(item.id);

      onDelete(item.id);

      toast.success('Disease detection deleted');
    } catch {
      toast.error('Failed to delete');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: -20 }}
      className="bg-gray-900 border border-gray-800 rounded-xl p-4 hover:border-gray-700 transition"
    >
      <div className="flex items-start justify-between gap-3">

        <div className="flex-1 min-w-0">

          <div className="flex items-center gap-2 mb-2">

            <span className="text-lg font-bold text-red-400">
              {item.disease || 'Healthy Plant'}
            </span>

            <span className={`text-xs px-2 py-0.5 rounded-full border ${
              item.is_healthy
                ? 'bg-green-500/10 text-green-400 border-green-500/20'
                : 'bg-red-500/10 text-red-400 border-red-500/20'
            }`}>
              {item.is_healthy
                ? 'Healthy'
                : 'Disease Detected'}
            </span>

          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs text-gray-400">

            <span>
              🌿 Plant: {item.plant_name || 'Unknown'}
            </span>

            <span>
              📊 Confidence:
              <strong className="text-gray-200">
                {' '}
                {item.confidence ?? 0}%
              </strong>
            </span>

            <span>
              ⚠ Severity: {item.severity || 'N/A'}
            </span>

            <span>
              📅 {new Date(item.created_at).toLocaleDateString('en-IN')}
            </span>

          </div>
        </div>

        <button
          onClick={handleDelete}
          disabled={deleting}
          className="p-2 text-gray-600 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition flex-shrink-0"
        >
          {deleting ? (
            <Loader2 size={14} className="animate-spin" />
          ) : (
            <Trash2 size={14} />
          )}
        </button>

      </div>
    </motion.div>
  );
}

export default function History() {

  const [tab, setTab] = useState('predictions');

  const [predictions, setPredictions] = useState([]);
  const [recommendations, setRecs] = useState([]);

  // ✅ Disease state added
  const [diseases, setDiseases] = useState([]);

  const [stats, setStats] = useState(null);

  const [loading, setLoading] = useState(true);

  // ✅ Updated auth
  const { user } = useAuth();

  const navigate = useNavigate();

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }

    fetchAll();

  }, [user]);

  const fetchAll = async () => {
    setLoading(true);

    try {

      // ✅ Disease fetch added
      const [pRes, rRes, dRes, sRes] = await Promise.all([
        getPredictions(),
        getRecommendationsList(),
        getDiseaseHistory(),
        getStats(),
      ]);

      setPredictions(pRes.data);
      setRecs(rRes.data);

      // ✅ Disease state update
      setDiseases(dRes.data);

      setStats(sRes.data);

    } catch {
      toast.error('Failed to load history');
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >

      {/* Header */}
      <div>

        <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
          <HistoryIcon size={28} className="text-green-500" />
          My History
        </h1>

        {/* ✅ Updated text */}
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          All your predictions, recommendations and disease checks
        </p>

      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">

          <StatCard
            icon={<Leaf size={16} />}
            label="Total Predictions"
            value={stats.total_predictions}
            color="green"
          />

          <StatCard
            icon={<FlaskConical size={16} />}
            label="Recommendations"
            value={stats.total_recommendations}
            color="blue"
          />

          <StatCard
            icon={<Award size={16} />}
            label="Top Crop"
            value={stats.most_predicted_crop}
            color="yellow"
          />

          <StatCard
            icon={<TrendingUp size={16} />}
            label="Avg Confidence"
            value={stats.avg_confidence ? `${stats.avg_confidence}%` : null}
            color="purple"
          />

        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-200 dark:border-gray-800">

        {[
          {
            key: 'predictions',
            label: 'Predictions',
            count: predictions.length
          },

          {
            key: 'recommendations',
            label: 'Recommendations',
            count: recommendations.length
          },

          // ✅ Disease tab added
          {
            key: 'disease',
            label: 'Disease Checks',
            count: diseases.length
          },

        ].map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition -mb-px ${
              tab === t.key
                ? 'border-green-500 text-green-600 dark:text-green-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
            }`}
          >
            {t.label}

            <span className="ml-2 text-xs bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded-full">
              {t.count}
            </span>

          </button>
        ))}

      </div>

      {/* Content */}
      {loading ? (

        <div className="flex items-center justify-center py-20">
          <Loader2 size={32} className="animate-spin text-green-500" />
        </div>

      ) : (

        <AnimatePresence mode="wait">

          {/* Predictions */}
          {tab === 'predictions' && (
            <motion.div
              key="preds"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="space-y-3"
            >

              {predictions.length === 0 ? (

                <div className="text-center py-16 text-gray-400">

                  <Leaf size={48} className="mx-auto mb-3 opacity-30" />

                  <p>
                    No predictions yet. Go to Predict page to get started.
                  </p>

                </div>

              ) : (

                predictions.map(p => (
                  <PredictionCard
                    key={p.id}
                    item={p}
                    onDelete={id =>
                      setPredictions(prev =>
                        prev.filter(x => x.id !== id)
                      )
                    }
                  />
                ))

              )}

            </motion.div>
          )}

          {/* Recommendations */}
          {tab === 'recommendations' && (
            <motion.div
              key="recs"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="space-y-3"
            >

              {recommendations.length === 0 ? (

                <div className="text-center py-16 text-gray-400">

                  <FlaskConical
                    size={48}
                    className="mx-auto mb-3 opacity-30"
                  />

                  <p>
                    No recommendations yet. Go to Recommend page to get started.
                  </p>

                </div>

              ) : (

                recommendations.map(r => (
                  <RecommendationCard
                    key={r.id}
                    item={r}
                    onDelete={id =>
                      setRecs(prev =>
                        prev.filter(x => x.id !== id)
                      )
                    }
                  />
                ))

              )}

            </motion.div>
          )}

          {/* ✅ Disease Rendering Added */}
          {tab === 'disease' && (
            <motion.div
              key="disease"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="space-y-3"
            >

              {diseases.length === 0 ? (

                <div className="text-center py-16 text-gray-400">

                  <Leaf
                    size={48}
                    className="mx-auto mb-3 opacity-30"
                  />

                  <p>
                    No disease detections yet.
                  </p>

                </div>

              ) : (

                diseases.map(d => (
                  <DiseaseCard
                    key={d.id}
                    item={d}
                    onDelete={id =>
                      setDiseases(prev =>
                        prev.filter(x => x.id !== id)
                      )
                    }
                  />
                ))

              )}

            </motion.div>
          )}

        </AnimatePresence>
      )}

    </motion.div>
  );
}