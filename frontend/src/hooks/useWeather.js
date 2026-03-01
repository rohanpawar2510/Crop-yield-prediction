import { useState } from 'react';
import { getWeather } from '../services/api';

export function useWeather() {
  const [weather, setWeather] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchWeather = async (location) => {
    if (!location.trim()) return null;
    setLoading(true);
    setError(null);
    try {
      const res = await getWeather(location);
      setWeather(res.data);
      return null;
    } catch (err) {
      const message = err.response?.data?.detail || 'Failed to fetch weather data';
      setError(message);
      return message;
    } finally {
      setLoading(false);
    }
  };

  return { weather, loading, error, fetchWeather };
}
