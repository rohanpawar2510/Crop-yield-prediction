import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { Thermometer, Droplets, Wind, CloudRain, Search, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';
import StatsCard from '../components/StatsCard';
import WeatherCard from '../components/WeatherCard';
import NPKChart from '../components/NPKChart';
import LoadingSkeleton from '../components/LoadingSkeleton';
import { useWeather } from '../hooks/useWeather';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.1 } },
};
const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
};

export default function Dashboard() {
  const [location, setLocation] = useState('Mumbai');
  const { weather, loading, error, fetchWeather } = useWeather();

  const handleSearch = async (e) => {
    e.preventDefault();
    const err = await fetchWeather(location);
    if (err) toast.error(err);
  };

  useEffect(() => {
    fetchWeather('Mumbai');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const quickActions = [
    { to: '/weather', label: 'Get Weather', emoji: '🌤️', color: 'bg-blue-500' },
    { to: '/predict', label: 'Predict Crop', emoji: '🌾', color: 'bg-emerald-500' },
    { to: '/recommend', label: 'AI Advice', emoji: '🤖', color: 'bg-purple-500' },
    { to: '/disease', label: 'Detect Disease', emoji: '🔬', color: 'bg-red-500' },
  ];

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-8">
      {/* Header */}
      <motion.div variants={itemVariants}>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Welcome to Smart Agriculture 🌱
        </h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">AI-powered crop yield prediction & farming insights</p>
      </motion.div>

      {/* Weather Search */}
      <motion.div variants={itemVariants}>
        <form onSubmit={handleSearch} className="flex gap-3">
          <input
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="Search location..."
            className="input-field flex-1"
          />
          <button type="submit" disabled={loading} className="btn-primary flex items-center gap-2">
            {loading ? <Loader2 size={18} className="animate-spin" /> : <Search size={18} />}
            Search
          </button>
        </form>
      </motion.div>

      {/* Stats Cards */}
      <motion.div variants={itemVariants} className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {loading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="card">
              <LoadingSkeleton rows={2} />
            </div>
          ))
        ) : weather ? (
          <>
            <StatsCard icon={Thermometer} label="Temperature" value={weather.temperature} unit="°C" color="accent" />
            <StatsCard icon={Droplets} label="Humidity" value={weather.humidity} unit="%" color="secondary" />
            <StatsCard icon={Wind} label="Wind Speed" value={weather.wind_speed} unit="km/h" color="primary" />
            <StatsCard icon={CloudRain} label="Rainfall" value={weather.rainfall ?? 0} unit="mm" color="purple" />
          </>
        ) : (
          <div className="col-span-4 card text-center text-gray-400 py-8">
            Search for a location to see weather stats
          </div>
        )}
      </motion.div>

      {/* Weather Card */}
      {weather && (
        <motion.div variants={itemVariants}>
          <WeatherCard weather={weather} />
          {weather.is_mock && (
            <div role="alert" className="card bg-yellow-50 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-300 border-yellow-200 dark:border-yellow-700 mt-4">
              ⚠️ Showing sample data — configure <code>OPENWEATHER_API_KEY</code> for live weather
            </div>
          )}
        </motion.div>
      )}

      {/* Quick Actions */}
      <motion.div variants={itemVariants}>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Quick Actions</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {quickActions.map(({ to, label, emoji, color }) => (
            <Link key={to} to={to}>
              <motion.div
                whileHover={{ scale: 1.05, y: -2 }}
                whileTap={{ scale: 0.95 }}
                className={`${color} text-white rounded-2xl p-6 text-center cursor-pointer shadow-md`}
              >
                <div className="text-3xl mb-2">{emoji}</div>
                <p className="font-semibold">{label}</p>
              </motion.div>
            </Link>
          ))}
        </div>
      </motion.div>

      {/* NPK Chart */}
      <motion.div variants={itemVariants}>
        <NPKChart nitrogen={80} phosphorus={40} potassium={60} />
      </motion.div>

      {/* Tips Section */}
      <motion.div variants={itemVariants} className="card">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">🌿 Farming Tips</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { title: 'Soil Health', tip: 'Maintain pH between 6.0–7.0 for optimal nutrient absorption.', emoji: '🌱' },
            { title: 'Water Management', tip: 'Drip irrigation can reduce water usage by up to 50%.', emoji: '💧' },
            { title: 'Crop Rotation', tip: 'Rotate legumes with cereals to naturally replenish nitrogen.', emoji: '🔄' },
          ].map(({ title, tip, emoji }) => (
            <div key={title} className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
              <div className="text-2xl mb-2">{emoji}</div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-1">{title}</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">{tip}</p>
            </div>
          ))}
        </div>
      </motion.div>
    </motion.div>
  );
}
