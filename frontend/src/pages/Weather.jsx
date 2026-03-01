import { useState } from 'react';
import { motion } from 'framer-motion';
import { Search, Loader2, Thermometer, Droplets, Wind } from 'lucide-react';
import toast from 'react-hot-toast';
import WeatherCard from '../components/WeatherCard';
import StatsCard from '../components/StatsCard';
import LoadingSkeleton from '../components/LoadingSkeleton';
import { useWeather } from '../hooks/useWeather';

export default function Weather() {
  const [location, setLocation] = useState('');
  const { weather, loading, error, fetchWeather } = useWeather();

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!location.trim()) return;
    const err = await fetchWeather(location);
    if (err) toast.error(err);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-8"
    >
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Weather 🌤️</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">Real-time weather data for any location</p>
      </div>

      <form onSubmit={handleSearch} className="flex gap-3 max-w-xl">
        <input
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          placeholder="Enter city name (e.g. Mumbai, Delhi)..."
          className="input-field flex-1"
        />
        <button type="submit" disabled={loading || !location.trim()} className="btn-primary flex items-center gap-2">
          {loading ? <Loader2 size={18} className="animate-spin" /> : <Search size={18} />}
          Search
        </button>
      </form>

      {error && (
        <div className="card bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 border-red-200 dark:border-red-800">
          ⚠️ {error}
        </div>
      )}

      {loading && (
        <div className="card">
          <LoadingSkeleton rows={5} />
        </div>
      )}

      {weather && !loading && (
        <>
          <WeatherCard weather={weather} />
          {weather.is_mock && (
            <div role="alert" className="card bg-yellow-50 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-300 border-yellow-200 dark:border-yellow-700">
              ⚠️ Showing sample data — configure <code>OPENWEATHER_API_KEY</code> for live weather
            </div>
          )}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <StatsCard icon={Thermometer} label="Temperature" value={weather.temperature} unit="°C" color="accent" />
            <StatsCard icon={Droplets} label="Humidity" value={weather.humidity} unit="%" color="secondary" />
            <StatsCard icon={Wind} label="Wind Speed" value={weather.wind_speed} unit="km/h" color="primary" />
          </div>
        </>
      )}

      {!weather && !loading && !error && (
        <div className="card text-center py-16">
          <div className="text-6xl mb-4">🌍</div>
          <p className="text-gray-500 dark:text-gray-400 text-lg">Search for a city to see weather data</p>
        </div>
      )}
    </motion.div>
  );
}
