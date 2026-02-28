import { Doughnut } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { useTheme } from '../context/ThemeContext';

ChartJS.register(ArcElement, Tooltip, Legend);

export default function NPKChart({ nitrogen = 0, phosphorus = 0, potassium = 0 }) {
  const { isDark } = useTheme();
  const total = nitrogen + phosphorus + potassium || 1;

  const data = {
    labels: ['Nitrogen (N)', 'Phosphorus (P)', 'Potassium (K)'],
    datasets: [
      {
        data: [nitrogen, phosphorus, potassium],
        backgroundColor: ['#10B981', '#3B82F6', '#F59E0B'],
        borderColor: isDark ? '#1E293B' : '#ffffff',
        borderWidth: 3,
        hoverOffset: 8,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          color: isDark ? '#9CA3AF' : '#6B7280',
          padding: 20,
          font: { size: 12 },
        },
      },
      tooltip: {
        callbacks: {
          label: (ctx) => {
            const pct = ((ctx.raw / total) * 100).toFixed(1);
            return ` ${ctx.label}: ${ctx.raw} (${pct}%)`;
          },
        },
      },
    },
    cutout: '65%',
  };

  return (
    <div className="card">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">NPK Distribution</h3>
      <div className="max-w-xs mx-auto">
        <Doughnut data={data} options={options} />
      </div>
    </div>
  );
}
