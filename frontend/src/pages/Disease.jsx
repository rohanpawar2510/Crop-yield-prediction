import { motion } from 'framer-motion';
import DiseaseDetection from '../components/DiseaseDetection';

export default function Disease() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-8"
    >
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Disease Detection 🔬</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">Upload a plant image to detect diseases using AI</p>
      </div>
      <div className="max-w-2xl">
        <div className="card">
          <DiseaseDetection />
        </div>
      </div>
    </motion.div>
  );
}
