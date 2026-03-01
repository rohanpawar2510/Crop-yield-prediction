import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
  Legend,
} from 'chart.js';
import { useTheme } from '../context/ThemeContext';

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

const IMPORTANCE = {
  Rainfall: 28,
  Temperature: 22,
  Humidity: 18,
  Nitrogen: 12,
  Potassium: 9,
  Phosphorus: 7,
  pH: 4,
};

const COLORS = ['#10B981', '#34D399', '#6EE7B7', '#3B82F6', '#60A5FA', '#93C5FD', '#BFDBFE'];

const sorted = Object.entries(IMPORTANCE).sort((a, b) => b[1] - a[1]);

export default function FeatureImportanceChart() {
  const { isDark } = useTheme();
  const gridColor = isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)';

  const data = {
    labels: sorted.map(([k]) => k),
    datasets: [
      {
        label: 'Importance (%)',
        data: sorted.map(([, v]) => v),
        backgroundColor: COLORS,
        borderRadius: 4,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (ctx) => ` ${ctx.raw}%`,
        },
      },
    },
    scales: {
      y: {
        title: {
          display: true,
          text: 'Importance (%)',
          color: textColor,
          font: { size: 12 },
        },
        ticks: { color: textColor },
        grid: { color: gridColor },
      },
      x: {
        ticks: { color: textColor },
        grid: { color: gridColor },
      },
    },
  };

  return (
    <div className="card">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Feature Importance 🔍</h3>
      <Bar data={data} options={options} />
      <p className="text-xs text-gray-400 mt-3">* Feature importance based on Random Forest model weights</p>
    </div>
  );
}
