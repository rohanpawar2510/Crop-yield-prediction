import { motion } from 'framer-motion';
import { Droplets, Wind, Thermometer, Cloud } from 'lucide-react';

export default function WeatherCard({ weather }) {
  if (!weather) return null;
  const emoji = weather.icon || '🌤️';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="card overflow-hidden"
    >
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-2xl font-bold text-gray-900 dark:text-white">{weather.location}</h3>
          <p className="text-gray-500 dark:text-gray-400 capitalize">{weather.description}</p>
        </div>
        <span className="text-6xl">{emoji}</span>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="flex items-center gap-2 bg-orange-50 dark:bg-orange-900/20 p-3 rounded-xl">
          <Thermometer className="text-orange-500" size={20} />
          <div>
            <p className="text-xs text-gray-500 dark:text-gray-400">Temp</p>
            <p className="font-bold text-gray-900 dark:text-white">{weather.temperature}°C</p>
          </div>
        </div>
        <div className="flex items-center gap-2 bg-blue-50 dark:bg-blue-900/20 p-3 rounded-xl">
          <Droplets className="text-blue-500" size={20} />
          <div>
            <p className="text-xs text-gray-500 dark:text-gray-400">Humidity</p>
            <p className="font-bold text-gray-900 dark:text-white">{weather.humidity}%</p>
          </div>
        </div>
        <div className="flex items-center gap-2 bg-teal-50 dark:bg-teal-900/20 p-3 rounded-xl">
          <Wind className="text-teal-500" size={20} />
          <div>
            <p className="text-xs text-gray-500 dark:text-gray-400">Wind</p>
            <p className="font-bold text-gray-900 dark:text-white">{weather.wind_speed} km/h</p>
          </div>
        </div>
        <div className="flex items-center gap-2 bg-purple-50 dark:bg-purple-900/20 p-3 rounded-xl">
          <Cloud className="text-purple-500" size={20} />
          <div>
            <p className="text-xs text-gray-500 dark:text-gray-400">Rainfall</p>
            <p className="font-bold text-gray-900 dark:text-white">{weather.rainfall ?? 0} mm</p>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
