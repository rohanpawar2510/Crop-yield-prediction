import { motion } from 'framer-motion';

export default function StatsCard({ icon: Icon, label, value, unit = '', color = 'primary', trend }) {
  const colorMap = {
    primary: 'bg-emerald-100 dark:bg-emerald-900/30 text-primary',
    secondary: 'bg-blue-100 dark:bg-blue-900/30 text-secondary',
    accent: 'bg-amber-100 dark:bg-amber-900/30 text-accent',
    purple: 'bg-purple-100 dark:bg-purple-900/30 text-purple-500',
  };

  return (
    <motion.div
      whileHover={{ scale: 1.02, y: -2 }}
      className="card flex items-center gap-4"
    >
      <div className={`p-3 rounded-xl ${colorMap[color]}`}>
        <Icon size={24} />
      </div>
      <div className="flex-1">
        <p className="text-sm text-gray-500 dark:text-gray-400">{label}</p>
        <p className="text-2xl font-bold text-gray-900 dark:text-white">
          {value}<span className="text-sm font-normal text-gray-500 dark:text-gray-400 ml-1">{unit}</span>
        </p>
        {trend && <p className="text-xs text-gray-400 mt-1">{trend}</p>}
      </div>
    </motion.div>
  );
}
