import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  Sprout,
  CloudSun,
  Brain,
  Microscope,
  BarChart3,
  Droplets,
  ArrowRight,
  CheckCircle2,
  Upload,
  Cpu,
  TrendingUp,
  Lightbulb,
} from 'lucide-react';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.12 } },
};

const itemVariants = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: 'easeOut' } },
};

const features = [
  {
    icon: Sprout,
    title: 'Crop Yield Prediction',
    description: 'ML-powered predictions using soil NPK, pH, temperature & rainfall data for optimal crop selection.',
    color: 'text-emerald-500',
    bg: 'bg-emerald-50 dark:bg-emerald-900/20',
  },
  {
    icon: CloudSun,
    title: 'Live Weather Integration',
    description: 'Real-time weather data via OpenWeather API — temperature, humidity, wind speed & rainfall.',
    color: 'text-blue-500',
    bg: 'bg-blue-50 dark:bg-blue-900/20',
  },
  {
    icon: Brain,
    title: 'AI Recommendations',
    description: 'Gemini AI-powered personalised farming advice based on your soil and environmental conditions.',
    color: 'text-purple-500',
    bg: 'bg-purple-50 dark:bg-purple-900/20',
  },
  {
    icon: Microscope,
    title: 'Disease Detection',
    description: 'Upload plant images to detect diseases early and receive treatment recommendations.',
    color: 'text-red-500',
    bg: 'bg-red-50 dark:bg-red-900/20',
  },
  {
    icon: BarChart3,
    title: 'Data Visualisation',
    description: 'Interactive charts for NPK ratios, soil radar analysis, yield comparisons & feature importance.',
    color: 'text-amber-500',
    bg: 'bg-amber-50 dark:bg-amber-900/20',
  },
  {
    icon: Droplets,
    title: 'Resource Optimisation',
    description: 'Smart irrigation tips and crop rotation strategies to reduce water usage by up to 50%.',
    color: 'text-teal-500',
    bg: 'bg-teal-50 dark:bg-teal-900/20',
  },
];

const stats = [
  { value: '98%', label: 'Prediction Accuracy' },
  { value: '22+', label: 'Supported Crops' },
  { value: '6', label: 'Core AI Features' },
  { value: '50%', label: 'Water Savings' },
];

const steps = [
  {
    icon: Upload,
    step: '01',
    title: 'Input Soil & Location Data',
    description: 'Enter NPK values, soil pH, temperature, humidity, and rainfall for your field.',
  },
  {
    icon: Cpu,
    step: '02',
    title: 'AI Model Analysis',
    description: 'Our Random Forest ML model analyses your data against thousands of agricultural records.',
  },
  {
    icon: TrendingUp,
    step: '03',
    title: 'Get Yield Predictions',
    description: 'Receive crop recommendations with confidence scores and expected yield estimates.',
  },
  {
    icon: Lightbulb,
    step: '04',
    title: 'Optimise with AI Advice',
    description: 'Gemini AI delivers personalised recommendations to maximise your farm productivity.',
  },
];

const benefits = [
  'Real-time OpenWeather API integration',
  'Trained Random Forest classification model',
  'Gemini AI-powered smart recommendations',
  'Plant disease detection via image upload',
  'Interactive NPK & soil radar charts',
  'Full dark mode support',
];

export default function Landing() {
  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-16 pb-8"
    >
      {/* Hero Section */}
      <motion.div
        variants={itemVariants}
        className="relative rounded-3xl overflow-hidden bg-gradient-to-br from-emerald-600 via-emerald-700 to-teal-800 dark:from-emerald-800 dark:via-gray-900 dark:to-gray-900 p-8 md:p-14 text-white shadow-2xl"
      >
        {/* Decorative blobs */}
        <div className="absolute top-0 right-0 w-72 h-72 bg-white/5 rounded-full -translate-y-1/2 translate-x-1/3 pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-56 h-56 bg-white/5 rounded-full translate-y-1/2 -translate-x-1/4 pointer-events-none" />

        <div className="relative z-10 max-w-2xl">
          <motion.div
            variants={itemVariants}
            className="inline-flex items-center gap-2 bg-white/15 backdrop-blur-sm border border-white/20 rounded-full px-4 py-1.5 text-sm font-medium mb-6"
          >
            <Sprout size={15} />
            Smart Agriculture Dashboard — Final Year Project
          </motion.div>

          <motion.h1
            variants={itemVariants}
            className="text-4xl md:text-5xl font-bold leading-tight mb-5"
          >
            Maximise Your Crop Yield with{' '}
            <span className="text-emerald-200">Artificial Intelligence</span>
          </motion.h1>

          <motion.p
            variants={itemVariants}
            className="text-lg text-emerald-100 mb-8 leading-relaxed"
          >
            Smart predictions, real-time weather insights, and expert AI recommendations
            for sustainable, data-driven farming.
          </motion.p>

          <motion.div variants={itemVariants} className="flex flex-wrap gap-4">
            <Link to="/dashboard">
              <motion.button
                whileHover={{ scale: 1.05, y: -2 }}
                whileTap={{ scale: 0.95 }}
                className="flex items-center gap-2 bg-white text-emerald-700 font-bold px-7 py-3.5 rounded-xl shadow-lg hover:shadow-xl transition-shadow duration-200"
              >
                Enter Dashboard
                <ArrowRight size={18} />
              </motion.button>
            </Link>
            <Link to="/predict">
              <motion.button
                whileHover={{ scale: 1.05, y: -2 }}
                whileTap={{ scale: 0.95 }}
                className="flex items-center gap-2 bg-white/15 backdrop-blur-sm border border-white/30 text-white font-semibold px-7 py-3.5 rounded-xl hover:bg-white/25 transition-colors duration-200"
              >
                Try Prediction
              </motion.button>
            </Link>
          </motion.div>
        </div>
      </motion.div>

      {/* Stats Strip */}
      <motion.div
        variants={itemVariants}
        className="grid grid-cols-2 md:grid-cols-4 gap-4"
      >
        {stats.map(({ value, label }) => (
          <motion.div
            key={label}
            whileHover={{ scale: 1.04, y: -3 }}
            className="card text-center py-6"
          >
            <p className="text-3xl font-bold text-primary mb-1">{value}</p>
            <p className="text-sm text-gray-500 dark:text-gray-400 font-medium">{label}</p>
          </motion.div>
        ))}
      </motion.div>

      {/* Features Section */}
      <motion.div variants={itemVariants}>
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-3">
            Everything You Need to Farm Smarter
          </h2>
          <p className="text-gray-500 dark:text-gray-400 max-w-xl mx-auto">
            Six integrated AI features working together to help you make better decisions
            at every stage of the growing cycle.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {features.map(({ icon: Icon, title, description, color, bg }) => (
            <motion.div
              key={title}
              variants={itemVariants}
              whileHover={{ scale: 1.03, y: -4 }}
              className="card cursor-default group"
            >
              <div className={`inline-flex p-3 rounded-xl ${bg} mb-4`}>
                <Icon size={22} className={color} />
              </div>
              <h3 className="text-base font-semibold text-gray-900 dark:text-white mb-2">
                {title}
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 leading-relaxed">
                {description}
              </p>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* How It Works */}
      <motion.div variants={itemVariants}>
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-3">
            How It Works
          </h2>
          <p className="text-gray-500 dark:text-gray-400 max-w-xl mx-auto">
            From soil data to actionable insights in four simple steps.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          {steps.map(({ icon: Icon, step, title, description }, index) => (
            <motion.div
              key={step}
              variants={itemVariants}
              whileHover={{ scale: 1.03, y: -4 }}
              className="card relative"
            >
              <span className="absolute top-5 right-5 text-4xl font-black text-gray-100 dark:text-gray-700 select-none">
                {step}
              </span>
              <div className="inline-flex p-3 rounded-xl bg-primary/10 dark:bg-primary/20 mb-4">
                <Icon size={22} className="text-primary" />
              </div>
              <h3 className="text-base font-semibold text-gray-900 dark:text-white mb-2">
                {title}
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 leading-relaxed">
                {description}
              </p>
              {index < steps.length - 1 && (
                <div className="hidden lg:block absolute -right-3 top-1/2 -translate-y-1/2 z-10">
                  <ArrowRight size={18} className="text-gray-300 dark:text-gray-600" />
                </div>
              )}
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Benefits + CTA */}
      <motion.div
        variants={itemVariants}
        className="grid grid-cols-1 lg:grid-cols-2 gap-6"
      >
        {/* Benefits list */}
        <div className="card">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            Built with Modern Technology
          </h2>
          <p className="text-gray-500 dark:text-gray-400 mb-6 text-sm">
            A full-stack final year engineering project combining React, FastAPI, and
            state-of-the-art ML models.
          </p>
          <ul className="space-y-3">
            {benefits.map((benefit) => (
              <li key={benefit} className="flex items-center gap-3 text-sm text-gray-700 dark:text-gray-300">
                <CheckCircle2 size={18} className="text-primary flex-shrink-0" />
                {benefit}
              </li>
            ))}
          </ul>
        </div>

        {/* CTA card */}
        <motion.div
          whileHover={{ scale: 1.01 }}
          className="relative rounded-2xl overflow-hidden bg-gradient-to-br from-gray-900 to-gray-800 dark:from-gray-800 dark:to-gray-900 border border-gray-700 p-8 flex flex-col justify-between shadow-xl"
        >
          <div className="absolute top-0 right-0 w-40 h-40 bg-primary/10 rounded-full -translate-y-1/2 translate-x-1/2 pointer-events-none" />
          <div>
            <div className="inline-flex p-3 rounded-xl bg-primary/20 mb-5">
              <Sprout size={24} className="text-primary" />
            </div>
            <h3 className="text-2xl font-bold text-white mb-3">
              Ready to get started?
            </h3>
            <p className="text-gray-400 text-sm leading-relaxed mb-8">
              Explore the full dashboard with live weather data, ML crop predictions,
              AI recommendations, and disease detection — all in one place.
            </p>
          </div>
          <div className="flex flex-col sm:flex-row gap-3">
            <Link to="/dashboard" className="flex-1">
              <motion.button
                whileHover={{ scale: 1.04, y: -2 }}
                whileTap={{ scale: 0.96 }}
                className="w-full flex items-center justify-center gap-2 bg-primary hover:bg-emerald-600 text-white font-bold px-6 py-3.5 rounded-xl shadow-lg shadow-emerald-900/40 transition-colors duration-200"
              >
                Open Dashboard
                <ArrowRight size={17} />
              </motion.button>
            </Link>
            <Link to="/predict" className="flex-1">
              <motion.button
                whileHover={{ scale: 1.04, y: -2 }}
                whileTap={{ scale: 0.96 }}
                className="w-full flex items-center justify-center gap-2 bg-white/10 border border-white/20 text-white font-semibold px-6 py-3.5 rounded-xl hover:bg-white/20 transition-colors duration-200"
              >
                Try Prediction
              </motion.button>
            </Link>
          </div>
        </motion.div>
      </motion.div>
    </motion.div>
  );
}
