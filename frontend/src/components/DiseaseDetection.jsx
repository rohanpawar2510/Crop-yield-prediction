import { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { Upload, Image as ImageIcon, Loader2, AlertCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import { detectDisease } from '../services/api';

export default function DiseaseDetection() {
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);

  const handleFile = (file) => {
    if (!file || !file.type.startsWith('image/')) {
      toast.error('Please upload a valid image file');
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

  const handleAnalyze = async () => {
    if (!image) return;
    setLoading(true);
    try {
      const form = new FormData();
      form.append('file', image);
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
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-200 ${
          dragging
            ? 'border-primary bg-emerald-50 dark:bg-emerald-900/20'
            : 'border-gray-300 dark:border-gray-600 hover:border-primary hover:bg-gray-50 dark:hover:bg-gray-700/50'
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={(e) => handleFile(e.target.files[0])}
        />
        <Upload className="mx-auto mb-4 text-gray-400" size={40} />
        <p className="text-gray-600 dark:text-gray-400 font-medium">Drop an image or click to upload</p>
        <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">PNG, JPG, JPEG up to 10MB</p>
      </div>

      {preview && (
        <div className="flex flex-col items-center gap-4">
          <img src={preview} alt="Upload preview" className="max-h-64 rounded-xl shadow-md object-contain" />
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleAnalyze}
            disabled={loading}
            className="btn-primary flex items-center gap-2"
          >
            {loading ? (
              <><Loader2 size={18} className="animate-spin" /> Analyzing...</>
            ) : (
              <><ImageIcon size={18} /> Analyze Disease</>
            )}
          </motion.button>
        </div>
      )}

      {result && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card space-y-3"
        >
          <div className="flex items-center gap-2 text-red-500">
            <AlertCircle size={20} />
            <h3 className="font-bold text-lg">Detection Result</h3>
          </div>
          {result.disease && (
            <div>
              <span className="text-sm text-gray-500 dark:text-gray-400">Disease Detected:</span>
              <p className="font-semibold text-gray-900 dark:text-white text-lg">{result.disease}</p>
            </div>
          )}
          {result.confidence != null && (
            <div>
              <span className="text-sm text-gray-500 dark:text-gray-400">Confidence:</span>
              <div className="flex items-center gap-3 mt-1">
                <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-primary h-2 rounded-full transition-all duration-700"
                    style={{ width: `${(result.confidence * 100).toFixed(0)}%` }}
                  />
                </div>
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  {(result.confidence * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          )}
          {result.treatment && (
            <div>
              <span className="text-sm text-gray-500 dark:text-gray-400">Treatment:</span>
              <p className="mt-1 text-gray-700 dark:text-gray-300 text-sm leading-relaxed">{result.treatment}</p>
            </div>
          )}
          {result.message && (
            <p className="text-gray-700 dark:text-gray-300 text-sm">{result.message}</p>
          )}
        </motion.div>
      )}
    </div>
  );
}
