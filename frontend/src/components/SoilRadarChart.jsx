import { Radar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from 'chart.js';
import { useTheme } from '../context/ThemeContext';

ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend);

const MAXES = {
  Nitrogen: 140,
  Phosphorus: 145,
  Potassium: 205,
  Temperature: 50,
  pH: 14,
  Rainfall: 500,
};

export default function SoilRadarChart({
  nitrogen = 0,
  phosphorus = 0,
  potassium = 0,
  temperature = 0,
  ph = 0,
  rainfall = 0,
}) {
  const { isDark } = useTheme();
  const textColor = isDark ? '#9CA3AF' : '#6B7280';
  const gridColor = isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)';

  const rawValues = [nitrogen, phosphorus, potassium, temperature, ph, rainfall];
  const labels = ['Nitrogen', 'Phosphorus', 'Potassium', 'Temperature', 'pH', 'Rainfall'];
  const maxValues = Object.values(MAXES);
  const normalized = rawValues.map((v, i) => parseFloat(((v / maxValues[i]) * 100).toFixed(1)));

  const data = {
    labels,
    datasets: [
      {
        label: 'Soil & Climate',
        data: normalized,
        backgroundColor: 'rgba(16, 185, 129, 0.3)',
        borderColor: '#10B981',
        borderWidth: 2,
        pointBackgroundColor: '#10B981',
        pointBorderColor: isDark ? '#1E293B' : '#ffffff',
        pointBorderWidth: 2,
        pointRadius: 4,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        callbacks: {
          label: (ctx) => {
            const raw = rawValues[ctx.dataIndex];
            const unit = ['mg/kg', 'mg/kg', 'mg/kg', '°C', '', 'mm'][ctx.dataIndex];
            return ` ${ctx.label}: ${raw}${unit ? ` ${unit}` : ''}`;
          },
        },
      },
    },
    scales: {
      r: {
        min: 0,
        max: 100,
        ticks: {
          stepSize: 25,
          color: textColor,
          backdropColor: 'transparent',
          font: { size: 10 },
        },
        pointLabels: {
          color: textColor,
          font: { size: 12 },
        },
        grid: { color: gridColor },
        angleLines: { color: gridColor },
      },
    },
  };

  return (
    <div className="card">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Soil &amp; Climate Profile 🕸️
      </h3>
      <Radar data={data} options={options} />
    </div>
  );
}
