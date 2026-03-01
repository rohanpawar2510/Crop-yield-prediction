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

export default function YieldComparisonChart({ suitable_crops = [], yield_comparison = [], predicted_crop = '' }) {
  const { isDark } = useTheme();
  const textColor = isDark ? '#9CA3AF' : '#6B7280';
  const gridColor = isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)';

  if (!suitable_crops.length || !yield_comparison.length) return null;

  const colors = suitable_crops.map((crop) =>
    crop === predicted_crop ? '#10B981' : '#3B82F6'
  );

  const data = {
    labels: suitable_crops,
    datasets: [
      {
        label: 'Yield (tons/hectare)',
        data: yield_comparison,
        backgroundColor: colors,
        borderRadius: 4,
      },
    ],
  };

  const options = {
    indexAxis: 'y',
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (ctx) => ` ${ctx.raw} tons/hectare`,
        },
      },
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Yield (tons/hectare)',
          color: textColor,
          font: { size: 12 },
        },
        ticks: { color: textColor },
        grid: { color: gridColor },
      },
      y: {
        ticks: { color: textColor },
        grid: { color: gridColor },
      },
    },
  };

  return (
    <div className="card">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Yield Comparison 📊</h3>
      <Bar data={data} options={options} />
    </div>
  );
}
