import { motion, AnimatePresence } from 'framer-motion';
import { useState } from 'react';
import { ChevronDown, Droplets, RefreshCw, Bug, Sprout, FlaskConical, MapPin, Cloud, Maximize2 } from 'lucide-react';

const sections = [
  { key: 'fertilizer', label: 'Fertilizer Recommendation', icon: FlaskConical, color: 'text-emerald-500', bg: 'bg-emerald-50 dark:bg-emerald-900/20' },
  { key: 'crop_rotation', label: 'Crop Rotation', icon: RefreshCw, color: 'text-blue-500', bg: 'bg-blue-50 dark:bg-blue-900/20' },
  { key: 'irrigation', label: 'Irrigation', icon: Droplets, color: 'text-cyan-500', bg: 'bg-cyan-50 dark:bg-cyan-900/20' },
  { key: 'pest_management', label: 'Pest Management', icon: Bug, color: 'text-orange-500', bg: 'bg-orange-50 dark:bg-orange-900/20' },
  { key: 'general', label: 'General Advice', icon: Sprout, color: 'text-purple-500', bg: 'bg-purple-50 dark:bg-purple-900/20' },
];

function AccordionItem({ section, data }) {
  const [open, setOpen] = useState(false);
  const { icon: Icon, label, color, bg } = section;
  const content = data?.[section.key];
  if (!content) return null;

  let renderedContent;
  if (section.key === 'fertilizer' && typeof content === 'object') {
    renderedContent = (
      <div className="space-y-1">
        {content.primary && <p><span className="font-medium">Primary:</span> {content.primary}</p>}
        {content.amount && <p><span className="font-medium">Amount:</span> {content.amount}</p>}
        {content.schedule && <p><span className="font-medium">Schedule:</span> {content.schedule}</p>}
        {Array.isArray(content.alternatives) && content.alternatives.length > 0 && (
          <p><span className="font-medium">Alternatives:</span> {content.alternatives.join(', ')}</p>
        )}
      </div>
    );
  } else {
    const text = typeof content === 'string' ? content : JSON.stringify(content, null, 2);
    renderedContent = <span className="whitespace-pre-wrap">{text}</span>;
  }

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
            <div className="p-4 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 text-sm leading-relaxed">
              {renderedContent}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function RecommendationPanel({ data }) {
  if (!data) return null;

  const hasContext = data.district || data.season || (data.area !== undefined && data.area !== null);

  return (
    <div className="space-y-3">
      {hasContext && (
        <div className="flex flex-wrap gap-3 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl">
          {data.district && (
            <div className="flex items-center gap-1.5 text-sm text-green-700 dark:text-green-300">
              <MapPin size={14} />
              <span className="font-medium">District:</span>
              <span>{data.district}</span>
            </div>
          )}
          {data.season && (
            <div className="flex items-center gap-1.5 text-sm text-green-700 dark:text-green-300">
              <Cloud size={14} />
              <span className="font-medium">Season:</span>
              <span>{data.season}</span>
            </div>
          )}
          {data.area != null && (
            <div className="flex items-center gap-1.5 text-sm text-green-700 dark:text-green-300">
              <Maximize2 size={14} />
              <span className="font-medium">Area:</span>
              <span>{data.area} ha</span>
            </div>
          )}
        </div>
      )}
      {sections.map((s) => (
        <AccordionItem key={s.key} section={s} data={data} />
      ))}
    </div>
  );
}
