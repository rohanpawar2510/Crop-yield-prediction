import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  Sprout, Brain, Microscope, History,
  Clock, ChevronRight, TrendingUp,
  BarChart2, Leaf, FlaskConical, Target,
} from 'lucide-react';
import LoadingSkeleton from '../components/LoadingSkeleton';
import { useAuth }     from '../context/AuthContext';
import { getStats, getPredictions } from '../services/api';

// ─── Helpers ──────────────────────────────────────────────────────────────────

function getGreeting() {
  const h = new Date().getHours();
  if (h < 12) return 'Good morning';
  if (h < 17) return 'Good afternoon';
  return 'Good evening';
}

function timeAgo(dateStr) {
  const diff = Math.floor((Date.now() - new Date(dateStr)) / 1000);
  if (diff < 60)    return 'just now';
  if (diff < 3600)  return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

// ─── Quick actions ─────────────────────────────────────────────────────────────

const quickActions = [
  { to: '/predict',   label: 'Crop Prediction',    desc: 'AI crop & yield recommendation',   icon: Sprout,     color: 'emerald' },
  { to: '/recommend', label: 'AI Recommendations', desc: 'Gemini-powered fertilizer advice',  icon: Brain,      color: 'purple'  },
  { to: '/disease',   label: 'Disease Detection',  desc: 'Upload leaf photo for diagnosis',   icon: Microscope, color: 'red'     },
  { to: '/history',   label: 'My History',         desc: 'View past predictions & reports',   icon: History,    color: 'teal'    },
];

const colorMap = {
  emerald: { bg: 'bg-emerald-500/10', icon: 'text-emerald-500', border: 'border-gray-200 dark:border-gray-700' },
  purple:  { bg: 'bg-purple-500/10',  icon: 'text-purple-500',  border: 'border-gray-200 dark:border-gray-700' },
  red:     { bg: 'bg-red-500/10',     icon: 'text-red-500',     border: 'border-gray-200 dark:border-gray-700' },
  teal:    { bg: 'bg-teal-500/10',    icon: 'text-teal-500',    border: 'border-gray-200 dark:border-gray-700' },
};

// ─── Crop data ─────────────────────────────────────────────────────────────────

const CROP_META = {
  SUGARCANE: { tip: 'Sugarcane needs heavy irrigation — consider drip system to save water.',       emoji: '🎋' },
  WHEAT:     { tip: 'Wheat does best in Rabi season. Ensure adequate phosphorus at sowing.',         emoji: '🌾' },
  RICE:      { tip: 'Rice needs standing water. Monitor for blast disease during humid periods.',     emoji: '🌿' },
  COTTON:    { tip: 'Cotton is prone to bollworm. Use pheromone traps for early detection.',         emoji: '🌸' },
  MAIZE:     { tip: 'Maize needs nitrogen top-dressing at knee-high stage for best yield.',          emoji: '🌽' },
  JOWAR:     { tip: 'Jowar is drought-tolerant. Ideal for low-rainfall areas of Marathwada.',       emoji: '🌾' },
  BAJRA:     { tip: 'Bajra thrives in sandy soils. Minimal irrigation after establishment.',         emoji: '🌱' },
  SOYABEAN:  { tip: 'Soyabean fixes nitrogen — reduces fertilizer cost for the next crop.',          emoji: '🫘' },
  GROUNDNUT: { tip: 'Groundnut needs calcium-rich soil. Apply gypsum at pegging stage.',            emoji: '🥜' },
  BANANA:    { tip: 'Banana is a heavy feeder — split potassium application improves bunch weight.', emoji: '🍌' },
  POTATO:    { tip: 'Potato needs well-drained soil. Avoid waterlogging to prevent tuber rot.',     emoji: '🥔' },
  ONION:     { tip: 'Onion bulbing needs dry weather. Reduce irrigation 2 weeks before harvest.',    emoji: '🧅' },
  DEFAULT:   { tip: 'Test your soil annually and maintain pH between 6.5–7.5 for best results.',    emoji: '🌱' },
};

// ─── Main ──────────────────────────────────────────────────────────────────────

export default function Dashboard() {
  const { user } = useAuth();
  const [stats,        setStats]        = useState(null);
  const [recentPreds,  setRecentPreds]  = useState([]);
  const [statsLoading, setStatsLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [statsRes, predsRes] = await Promise.all([
          getStats(),
          getPredictions(3, 0),
        ]);
        setStats(statsRes.data);
        setRecentPreds(predsRes.data || []);
      } catch {
        // fail silently
      } finally {
        setStatsLoading(false);
      }
    };
    loadData();
  }, []);

  // Top crop = from recent 3 predictions, not all-time stats
  // This fixes the "stuck on JOWAR" issue
  const recentTopCrop = recentPreds[0]?.recommended_crop?.toUpperCase() || 'DEFAULT';
  const insight = CROP_META[recentTopCrop] || CROP_META.DEFAULT;

  // Avg yield from recent predictions only (not all-time skewed average)
  const recentAvgYield = recentPreds.length > 0
    ? (recentPreds.reduce((sum, p) => sum + p.predicted_yield, 0) / recentPreds.length).toFixed(2)
    : null;

  // First name only, lowercase fix
  const firstName = user?.name
    ? user.name.split(' ')[0].charAt(0).toUpperCase() + user.name.split(' ')[0].slice(1).toLowerCase()
    : 'Farmer';

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >

      {/* ── Greeting ── */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            {getGreeting()}, {firstName} 👋
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-0.5 text-sm">
            SmartAgri Dashboard · Maharashtra
          </p>
        </div>
        <p className="text-sm text-gray-400 dark:text-gray-500">
          {new Date().toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}
        </p>
      </div>

      {/* ── Stats ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {statsLoading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="card"><LoadingSkeleton rows={2} /></div>
          ))
        ) : (
          <>
            <StatTile
              icon={<Leaf size={18} className="text-emerald-500" />}
              label="Predictions"
              value={stats?.total_predictions ?? 0}
              sub="total crop predictions"
              accent="emerald"
            />
            <StatTile
              icon={<Brain size={18} className="text-purple-500" />}
              label="Recommendations"
              value={stats?.total_recommendations ?? 0}
              sub="AI advice generated"
              accent="purple"
            />
            <StatTile
              icon={<Microscope size={18} className="text-red-500" />}
              label="Disease Checks"
              value={stats?.total_disease_detections ?? 0}
              sub="leaf scans done"
              accent="red"
            />
            <StatTile
              icon={<Target size={18} className="text-amber-500" />}
              label="Avg Confidence"
              value={stats?.avg_confidence ? `${stats.avg_confidence}%` : '—'}
              sub="model accuracy"
              accent="amber"
            />
          </>
        )}
      </div>

      {/* ── Quick Actions ── */}
      <div>
        <h2 className="text-base font-semibold text-gray-700 dark:text-gray-300 mb-3">Quick Actions</h2>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {quickActions.map(({ to, label, desc, icon: Icon, color }) => {
            const c = colorMap[color];
            return (
              <Link key={to}
               to={to}
                className="block h-full outline-none focus:outline-none focus:ring-0"

               >
                <div className="group card h-full hover:shadow-md hover:-translate-y-1 transition-all duration-200 cursor-pointer">
                  <div className="flex items-start justify-between mb-3">
                    <div className={`p-2 rounded-lg ${c.bg}`}>
                      <Icon size={18} className={c.icon} />
                    </div>
                    <ChevronRight size={14} className="text-gray-300 group-hover:text-gray-500 dark:group-hover:text-gray-400 transition-colors mt-0.5" />
                  </div>
                  <p className="font-semibold text-gray-900 dark:text-white text-sm">{label}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 leading-relaxed">{desc}</p>
                </div>
              </Link>
            );
          })}
        </div>
      </div>

      {/* ── Recent Predictions + Insight ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">

        {/* Recent Predictions */}
        <div className="lg:col-span-2 card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-gray-900 dark:text-white">Recent Predictions</h2>
            <Link to="/history"
              className="text-xs text-emerald-600 dark:text-emerald-400 hover:underline flex items-center gap-0.5">
              View all <ChevronRight size={12} />
            </Link>
          </div>

          {statsLoading ? (
            <LoadingSkeleton rows={3} />
          ) : recentPreds.length === 0 ? (
            <div className="text-center py-10">
              <Sprout size={32} className="text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500 dark:text-gray-400 text-sm mb-3">No predictions yet</p>
              <Link to="/predict">
                <button className="text-xs bg-emerald-500 hover:bg-emerald-400 text-white px-4 py-2 rounded-lg transition">
                  Make your first prediction
                </button>
              </Link>
            </div>
          ) : (
            <div className="divide-y divide-gray-100 dark:divide-gray-700/50">
              {recentPreds.map((p) => (
                <div key={p.id}
                  className="flex items-center justify-between py-3 first:pt-0 last:pb-0">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center text-sm flex-shrink-0">
                      {CROP_META[p.recommended_crop?.toUpperCase()]?.emoji || '🌱'}
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-gray-900 dark:text-white capitalize">
                        {p.recommended_crop}
                      </p>
                      <p className="text-xs text-gray-400 dark:text-gray-500">
                        {p.location || 'Maharashtra'} · {p.predicted_yield} t/ha
                      </p>
                    </div>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <p className="text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                      {p.confidence}%
                    </p>
                    <p className="text-xs text-gray-400 flex items-center gap-1 justify-end mt-0.5">
                      <Clock size={10} />
                      {timeAgo(p.created_at)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Crop Insight */}
        <div className="card border border-emerald-200 dark:border-emerald-800/60 bg-emerald-50/30 dark:bg-emerald-950/20 flex flex-col gap-4">

          {/* Insight */}
          <div>
            <div className="flex items-center gap-2 mb-1">
              <FlaskConical size={15} className="text-emerald-500" />
              <h2 className="text-sm font-semibold text-gray-900 dark:text-white">Crop Insight</h2>
            </div>
            <p className="text-xs text-emerald-600 dark:text-emerald-400 mb-2">
              {recentPreds[0]
                ? `Latest — ${recentPreds[0].recommended_crop}`
                : 'General tip'}
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-300 leading-relaxed">
              {insight.tip}
            </p>
          </div>

          <div className="border-t border-emerald-100 dark:border-emerald-800/50" />

          {/* Recent avg yield */}
          <div>
            <div className="flex items-center gap-2 mb-1">
              <TrendingUp size={15} className="text-emerald-500" />
              <p className="text-sm font-semibold text-gray-900 dark:text-white">Recent Avg Yield</p>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Based on last {recentPreds.length} prediction{recentPreds.length !== 1 ? 's' : ''}</p>
            {recentAvgYield ? (
              <p className="text-xl font-bold text-emerald-600 dark:text-emerald-400">
                {recentAvgYield} <span className="text-xs font-normal text-gray-500">t/ha</span>
              </p>
            ) : (
              <p className="text-sm text-gray-400">No data yet</p>
            )}
          </div>

          <div className="border-t border-emerald-100 dark:border-emerald-800/50" />

          {/* Confidence bar */}
          {stats?.avg_confidence != null && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <BarChart2 size={15} className="text-emerald-500" />
                <p className="text-sm font-semibold text-gray-900 dark:text-white">Model Confidence</p>
              </div>
              <div className="flex items-center gap-2">
                <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
                  <div
                    className="bg-emerald-500 h-1.5 rounded-full transition-all duration-700"
                    style={{ width: `${stats.avg_confidence}%` }}
                  />
                </div>
                <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400 w-10 text-right">
                  {stats.avg_confidence}%
                </span>
              </div>
            </div>
          )}

          <Link to="/recommend">
            <button className="w-full text-xs bg-emerald-500 hover:bg-emerald-400 text-white py-2.5 rounded-xl transition font-medium">
              Get AI Recommendations →
            </button>
          </Link>
        </div>
      </div>

    </motion.div>
  );
}

// ─── StatTile ──────────────────────────────────────────────────────────────────

const accentBg = {
  emerald: 'bg-emerald-500/10 dark:bg-emerald-500/10 border-emerald-200/60 dark:border-emerald-800/40',
  purple:  'bg-purple-500/10  dark:bg-purple-500/10  border-purple-200/60  dark:border-purple-800/40',
  red:     'bg-red-500/10     dark:bg-red-500/10     border-red-200/60     dark:border-red-800/40',
  amber:   'bg-amber-500/10   dark:bg-amber-500/10   border-amber-200/60   dark:border-amber-800/40',
};

function StatTile({ icon, label, value, sub, accent }) {
  return (
    <div className={`rounded-xl p-4 border ${accentBg[accent] || 'border-gray-100 dark:border-gray-700/50'}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="p-1.5 rounded-lg bg-white dark:bg-gray-800 shadow-sm">
          {icon}
        </div>
      </div>
      <p className="text-2xl font-bold text-gray-900 dark:text-white capitalize min-h-[2rem] flex items-center">
        {value}
      </p>
      <p className="text-xs font-semibold text-gray-600 dark:text-gray-300 mt-0.5">{label}</p>
      <p className="text-xs text-gray-400 mt-0.5">{sub}</p>
    </div>
  );
}