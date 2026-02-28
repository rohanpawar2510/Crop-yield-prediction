import { motion, AnimatePresence } from 'framer-motion';
import { useState } from 'react';
import { ChevronDown, Droplets, RefreshCw, Bug, Sprout, FlaskConical } from 'lucide-react';

const sections = [
  { key: 'fertilizer', label: 'Fertilizer Recommendation', icon: FlaskConical, color: 'text-emerald-500', bg: 'bg-emerald-50 dark:bg-emerald-900/20' },
  { key: 'crop_rotation', label: 'Crop Rotation', icon: RefreshCw, color: 'text-blue-500', bg: 'bg-blue-50 dark:bg-blue-900/20' },
  { key: 'irrigation', label: 'Irrigation', icon: Droplets, color: 'text-cyan-500', bg: 'bg-cyan-50 dark:bg-cyan-900/20' },
  { key: 'pest_management', label: 'Pest Management', icon: Bug, color: 'text-orange-500', bg: 'bg-orange-50 dark:bg-orange-900/20' },
  { key: 'general_advice', label: 'General Advice', icon: Sprout, color: 'text-purple-500', bg: 'bg-purple-50 dark:bg-purple-900/20' },
];

function AccordionItem({ section, data }) {
  const [open, setOpen] = useState(false);
  const { icon: Icon, label, color, bg } = section;
  const content = data?.[section.key];
  if (!content) return null;

  const text = typeof content === 'string' ? content : JSON.stringify(content, null, 2);

  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen((p) => !p)}
        className={`w-full flex items-center gap-3 p-4 ${bg} text-left transition-all`}
      >
        <div className={`p-2 rounded-lg bg-white/60 dark:bg-gray-800/60 ${color}`}>
          <Icon size={18} />
        </div>
        <span className="font-semibold text-gray-900 dark:text-white flex-1">{label}</span>
        <ChevronDown
          size={18}
          className={`text-gray-500 transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
        />
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="p-4 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">
              {text}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function RecommendationPanel({ data }) {
  if (!data) return null;
  return (
    <div className="space-y-3">
      {sections.map((s) => (
        <AccordionItem key={s.key} section={s} data={data} />
      ))}
    </div>
  );
}
