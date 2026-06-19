import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Upload, Loader2, AlertCircle, CheckCircle2,
  Leaf, FlaskConical, Shield, Bug, RefreshCw, X
} from 'lucide-react';
import toast from 'react-hot-toast';
import { detectDisease } from '../services/api';

// ─── Severity config ──────────────────────────────────────────────────────────
const SEVERITY = {
  Severe:    { color: 'text-red-600 dark:text-red-400',       bg: 'bg-red-100 dark:bg-red-900/30',       bar: 'bg-red-500'    },
  Moderate:  { color: 'text-orange-600 dark:text-orange-400', bg: 'bg-orange-100 dark:bg-orange-900/30', bar: 'bg-orange-500' },
  Mild:      { color: 'text-yellow-600 dark:text-yellow-400', bg: 'bg-yellow-100 dark:bg-yellow-900/30', bar: 'bg-yellow-500' },
  Suspected: { color: 'text-blue-600 dark:text-blue-400',     bg: 'bg-blue-100 dark:bg-blue-900/30',     bar: 'bg-blue-500'   },
  None:      { color: 'text-green-600 dark:text-green-400',   bg: 'bg-green-100 dark:bg-green-900/30',   bar: 'bg-green-500'  },
};

function getSeverity(s) {
  return SEVERITY[s] || SEVERITY.Suspected;
}

export default function DiseaseDetection() {
  const [image,    setImage]    = useState(null);
  const [preview,  setPreview]  = useState(null);
  const [result,   setResult]   = useState(null);
  const [loading,  setLoading]  = useState(false);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);

  const handleFile = (file) => {
    if (!file || !file.type.startsWith('image/')) {
      toast.error('Please upload a valid image file');
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      toast.error('Image must be smaller than 5MB');
      return;
    }
    setImage(file);
    setPreview(URL.createObjectURL(file));
    setResult(null);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    handleFile(e.dataTransfer.files[0]);
  };

  const handleReset = () => {
    setImage(null);
    setPreview(null);
    setResult(null);
  };

  const handleAnalyze = async () => {
    if (!image) return;
    setLoading(true);
    try {
      const form = new FormData();
      form.append('image', image);
      const res = await detectDisease(form);
      setResult(res.data);
      toast.success('Analysis complete!');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Disease detection failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">

      {/* ── Upload Zone ── */}
      {!preview && (
        <div
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-200 ${
            dragging
              ? 'border-primary bg-emerald-50 dark:bg-emerald-900/20 scale-[1.01]'
              : 'border-gray-300 dark:border-gray-600 hover:border-primary hover:bg-gray-50 dark:hover:bg-gray-700/50'
          }`}
        >
          <input ref={inputRef} type="file" accept="image/*" className="hidden"
            onChange={(e) => handleFile(e.target.files[0])} />
          <Upload className="mx-auto mb-4 text-gray-400" size={40} />
          <p className="text-gray-600 dark:text-gray-400 font-medium text-lg">
            Drop a leaf/plant image or click to upload
          </p>
          <p className="text-sm text-gray-400 mt-2">PNG, JPG, WebP — max 5MB</p>
          <p className="text-xs text-gray-400 mt-1">
            💡 Use a clear close-up image of the affected leaf for best results
          </p>
        </div>
      )}

      {/* ── Image Preview — centered, fixed size, not full width ── */}
      {preview && (
        <div className="flex flex-col items-center space-y-4">
          <div className="relative w-full max-w-md">
            <img src={preview} alt="Upload preview"
              className="w-full max-h-80 rounded-xl shadow-md object-contain bg-gray-50 dark:bg-gray-800 mx-auto" />
            <button onClick={handleReset}
              className="absolute top-2 right-2 bg-white dark:bg-gray-800 rounded-full p-1.5 shadow-md hover:bg-red-50 dark:hover:bg-red-900/30">
              <X size={16} className="text-gray-500 hover:text-red-500" />
            </button>
          </div>

          <div className="flex gap-3 w-full max-w-md">
            <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
              onClick={handleAnalyze} disabled={loading}
              className="btn-primary flex-1 flex items-center justify-center gap-2 disabled:opacity-50">
              {loading
                ? <><Loader2 size={18} className="animate-spin" /> Analyzing...</>
                : <><Bug size={18} /> Detect Disease</>
              }
            </motion.button>
            <button onClick={handleReset} disabled={loading}
              className="px-4 py-2 rounded-xl border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center gap-2 text-sm">
              <RefreshCw size={16} /> Reset
            </button>
          </div>
        </div>
      )}

      {/* ── Results — FULL WIDTH below the image ── */}
      <AnimatePresence>
        {result && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            className="space-y-5 w-full">

            {/* Mock warning */}
            {result.is_mock && (
              <div className="flex items-center gap-2 rounded-lg bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 px-3 py-2 text-yellow-700 dark:text-yellow-400 text-sm">
                <AlertCircle size={16} />
                <span>Sample data — add <code className="font-mono">PLANT_ID_API_KEY</code> to .env for real detection</span>
              </div>
            )}

            {/* Plant + Health Status */}
            <div className="rounded-xl border border-gray-200 dark:border-gray-700 p-4">
              <div className="flex items-center justify-between flex-wrap gap-3">
                <div className="flex items-center gap-3">
                  <Leaf size={20} className="text-green-500" />
                  <div>
                    <p className="text-xs text-gray-500">Identified Plant</p>
                    <p className="font-semibold text-gray-900 dark:text-white">
                      {result.plant_name || 'Unknown Plant'}
                    </p>
                  </div>
                </div>
                <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-semibold
                  ${result.is_healthy
                    ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                    : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'}`}>
                  {result.is_healthy
                    ? <><CheckCircle2 size={16} /> Healthy</>
                    : <><AlertCircle size={16} /> Diseased</>}
                </div>
              </div>
            </div>

            {/* Disease Detection — full width, 2-col internal layout */}
            {result.detected && (
              <div className="rounded-xl border border-gray-200 dark:border-gray-700 p-5">
                <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2 mb-4">
                  <Bug size={18} className="text-red-500" /> Disease Detected
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Disease Name</p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">{result.disease}</p>
                  </div>

                  <div>
                    <p className="text-xs text-gray-500 mb-1">Confidence</p>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${result.confidence}%` }}
                          transition={{ duration: 0.8, ease: 'easeOut' }}
                          className={`h-2.5 rounded-full ${getSeverity(result.severity).bar}`}
                        />
                      </div>
                      <span className="text-sm font-bold text-gray-700 dark:text-gray-300">
                        {result.confidence}%
                      </span>
                    </div>
                  </div>

                  <div>
                    <p className="text-xs text-gray-500 mb-1">Severity</p>
                    <span className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${getSeverity(result.severity).bg} ${getSeverity(result.severity).color}`}>
                      {result.severity}
                    </span>
                  </div>
                </div>

                {result.affected_area && result.affected_area !== '0%' && (
                  <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-700">
                    <p className="text-xs text-gray-500">Estimated Affected Area</p>
                    <p className="font-medium text-gray-800 dark:text-gray-200">{result.affected_area}</p>
                  </div>
                )}
              </div>
            )}

            {/* No Disease */}
            {!result.detected && (
              <div className="rounded-xl border border-gray-200 dark:border-gray-700 text-center py-8">
                <CheckCircle2 size={48} className="mx-auto mb-3 text-green-500" />
                <p className="text-xl font-bold text-green-600 dark:text-green-400">Plant is Healthy!</p>
                <p className="text-gray-500 text-sm mt-1">No disease detected. Continue regular monitoring.</p>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mt-2">
                  Confidence: {result.confidence}%
                </p>
              </div>
            )}

            {/* Treatment Cards — full width, 3 columns */}
            {result.detected && (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {result.chemical_treatment && (
                  <div className="rounded-xl border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-950/30 p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <FlaskConical size={16} className="text-red-500" />
                      <p className="text-sm font-semibold text-red-700 dark:text-red-400">Chemical</p>
                    </div>
                    <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{result.chemical_treatment}</p>
                  </div>
                )}

                {result.biological_treatment && (
                  <div className="rounded-xl border border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-950/30 p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Leaf size={16} className="text-green-500" />
                      <p className="text-sm font-semibold text-green-700 dark:text-green-400">Biological</p>
                    </div>
                    <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{result.biological_treatment}</p>
                  </div>
                )}

                {result.prevention && (
                  <div className="rounded-xl border border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-950/30 p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Shield size={16} className="text-blue-500" />
                      <p className="text-sm font-semibold text-blue-700 dark:text-blue-400">Prevention</p>
                    </div>
                    <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{result.prevention}</p>
                  </div>
                )}
              </div>
            )}

            {/* General treatment fallback */}
            {result.detected && result.treatment && !result.chemical_treatment && (
              <div className="rounded-xl border border-gray-200 dark:border-gray-700 p-4">
                <p className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">Treatment</p>
                <p className="text-sm text-gray-600 dark:text-gray-400">{result.treatment}</p>
              </div>
            )}

            {/* All Diseases */}
            {result.all_diseases?.length > 0 && (
              <div className="rounded-xl border border-gray-200 dark:border-gray-700 p-5">
                <h3 className="font-semibold text-gray-900 dark:text-white mb-4">
                  All Detected Conditions
                </h3>
                <div className="space-y-3">
                  {result.all_diseases.map((d, i) => (
                    <div key={i} className="flex items-center gap-3">
                      <span className="text-xs text-gray-400 w-4">{i + 1}</span>
                      <div className="flex-1">
                        <div className="flex justify-between mb-1">
                          <span className="text-sm text-gray-700 dark:text-gray-300">{d.name}</span>
                          <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                            {d.probability}%
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
                          <div
                            className={`h-1.5 rounded-full ${i === 0 ? 'bg-red-500' : 'bg-gray-400'}`}
                            style={{ width: `${d.probability}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Try Another */}
            <button onClick={handleReset}
              className="w-full py-3 rounded-xl border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center justify-center gap-2 text-sm font-medium transition-colors">
              <RefreshCw size={16} /> Try Another Image
            </button>

          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}