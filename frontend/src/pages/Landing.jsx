import { useState } from 'react';
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
  Menu,
  X,
  Moon,
  Sun,
  Github,
  Mail,
  MapPin,
} from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

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
    description: 'Predict yields with 98% accuracy using soil NPK, pH, temperature & rainfall data.',
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
    description: 'Gemini-powered smart advice tailored to your soil conditions and local environment.',
    color: 'text-purple-500',
    bg: 'bg-purple-50 dark:bg-purple-900/20',
  },
  {
    icon: Microscope,
    title: 'Disease Detection',
    description: 'Early disease identification via image upload with treatment recommendations.',
    color: 'text-red-500',
    bg: 'bg-red-50 dark:bg-red-900/20',
  },
  {
    icon: BarChart3,
    title: 'Advanced Analytics',
    description: 'Interactive data visualisation & insights — NPK ratios, soil radar, yield comparisons.',
    color: 'text-amber-500',
    bg: 'bg-amber-50 dark:bg-amber-900/20',
  },
  {
    icon: Droplets,
    title: 'Smart Insights',
    description: 'Personalised farming tips and irrigation strategies to optimise resources.',
    color: 'text-teal-500',
    bg: 'bg-teal-50 dark:bg-teal-900/20',
  },
];

const stats = [
  { value: '98%', label: 'Model Accuracy' },
  { value: '⚡', label: 'Real-time Processing' },
  { value: '24/7', label: 'Monitoring' },
  { value: '🌿', label: 'Sustainable Farming' },
];

const steps = [
  {
    icon: Upload,
    step: '01',
    title: 'Input Soil Data',
    description: 'Enter NPK values, soil pH, temperature, humidity, and rainfall for your field.',
  },
  {
    icon: Cpu,
    step: '02',
    title: 'AI Analyzes',
    description: 'Our Random Forest ML model analyses your data against thousands of agricultural records.',
  },
  {
    icon: TrendingUp,
    step: '03',
    title: 'Get Predictions',
    description: 'Receive crop recommendations with confidence scores and expected yield estimates.',
  },
  {
    icon: Lightbulb,
    step: '04',
    title: 'Maximize Yield',
    description: 'Gemini AI delivers personalised recommendations to maximise your farm productivity.',
  },
];

const navLinks = [
  { label: 'Features', href: '#features' },
  { label: 'About', href: '#about' },
  { label: 'Contact', href: '#contact' },
];

function LandingNavbar() {
  const { isDark, toggleTheme } = useTheme();
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-white/80 dark:bg-gray-900/80 backdrop-blur-lg border-b border-gray-200 dark:border-gray-700">
      <div className="max-w-7xl mx-auto flex items-center justify-between px-6 h-16">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2 font-bold text-lg text-gray-900 dark:text-white">
          <div className="p-1.5 rounded-lg bg-emerald-500 text-white">
            <Sprout size={20} />
          </div>
          <span>Smart Agriculture</span>
        </Link>

        {/* Desktop Nav */}
        <nav className="hidden md:flex items-center gap-8">
          {navLinks.map(({ label, href }) => (
            <a
              key={label}
              href={href}
              className="text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors duration-200"
            >
              {label}
            </a>
          ))}
        </nav>

        {/* Right controls */}
        <div className="hidden md:flex items-center gap-3">
          <button
            onClick={toggleTheme}
            className="p-2 rounded-xl bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 transition-all duration-200"
            aria-label="Toggle dark mode"
          >
            {isDark ? <Sun size={20} /> : <Moon size={20} />}
          </button>
          <Link to="/dashboard">
            <motion.button
              whileHover={{ scale: 1.04 }}
              whileTap={{ scale: 0.96 }}
              className="flex items-center gap-2 bg-emerald-500 hover:bg-emerald-600 text-white font-semibold px-5 py-2 rounded-xl shadow transition-colors duration-200 text-sm"
            >
              Get Started
              <ArrowRight size={15} />
            </motion.button>
          </Link>
        </div>

        {/* Mobile menu button */}
        <div className="flex md:hidden items-center gap-2">
          <button
            onClick={toggleTheme}
            className="p-2 rounded-xl bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300"
            aria-label="Toggle dark mode"
          >
            {isDark ? <Sun size={18} /> : <Moon size={18} />}
          </button>
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="p-2 rounded-xl text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            aria-label="Toggle menu"
          >
            {menuOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className="md:hidden bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 px-6 py-4 flex flex-col gap-4">
          {navLinks.map(({ label, href }) => (
            <a
              key={label}
              href={href}
              onClick={() => setMenuOpen(false)}
              className="text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors"
            >
              {label}
            </a>
          ))}
          <Link to="/dashboard" onClick={() => setMenuOpen(false)}>
            <button className="w-full flex items-center justify-center gap-2 bg-emerald-500 hover:bg-emerald-600 text-white font-semibold px-5 py-2.5 rounded-xl text-sm transition-colors duration-200">
              Get Started
              <ArrowRight size={15} />
            </button>
          </Link>
        </div>
      )}
    </header>
  );
}

export default function Landing() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-white">
      <LandingNavbar />

      <main className="pt-16">
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="space-y-20 pb-0"
        >
          {/* Hero Section */}
          <motion.section
            variants={itemVariants}
            className="relative overflow-hidden bg-gradient-to-br from-emerald-600 via-emerald-700 to-teal-800 dark:from-emerald-900 dark:via-gray-900 dark:to-gray-950 text-white"
          >
            <div className="absolute top-0 right-0 w-96 h-96 bg-white/5 rounded-full -translate-y-1/2 translate-x-1/3 pointer-events-none" />
            <div className="absolute bottom-0 left-0 w-72 h-72 bg-white/5 rounded-full translate-y-1/2 -translate-x-1/4 pointer-events-none" />

            <div className="relative z-10 max-w-7xl mx-auto px-6 py-24 md:py-32">
              <motion.div
                variants={itemVariants}
                className="inline-flex items-center gap-2 bg-white/15 backdrop-blur-sm border border-white/20 rounded-full px-4 py-1.5 text-sm font-medium mb-6"
              >
                <Sprout size={15} />
                Smart Agriculture Dashboard — AI-Powered Farming
              </motion.div>

              <motion.h1
                variants={itemVariants}
                className="text-4xl md:text-6xl font-bold leading-tight mb-6 max-w-3xl"
              >
                Transform Your Farming with{' '}
                <span className="text-emerald-200">AI</span>
              </motion.h1>

              <motion.p
                variants={itemVariants}
                className="text-lg md:text-xl text-emerald-100 mb-10 leading-relaxed max-w-2xl"
              >
                Harness the power of AI-powered predictions, real-time weather data, and
                intelligent recommendations to maximise your crop yield sustainably.
              </motion.p>

              <motion.div variants={itemVariants} className="flex flex-wrap gap-4">
                <Link to="/dashboard">
                  <motion.button
                    whileHover={{ scale: 1.05, y: -2 }}
                    whileTap={{ scale: 0.95 }}
                    className="flex items-center gap-2 bg-white text-emerald-700 font-bold px-8 py-4 rounded-xl shadow-lg hover:shadow-xl transition-shadow duration-200 text-base"
                  >
                    Get Started
                    <ArrowRight size={18} />
                  </motion.button>
                </Link>
                <a href="#features">
                  <motion.button
                    whileHover={{ scale: 1.05, y: -2 }}
                    whileTap={{ scale: 0.95 }}
                    className="flex items-center gap-2 bg-white/15 backdrop-blur-sm border border-white/30 text-white font-semibold px-8 py-4 rounded-xl hover:bg-white/25 transition-colors duration-200 text-base"
                  >
                    Learn More
                  </motion.button>
                </a>
              </motion.div>
            </div>
          </motion.section>

          {/* Stats Section */}
          <motion.section variants={itemVariants} className="max-w-7xl mx-auto px-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {stats.map(({ value, label }) => (
                <motion.div
                  key={label}
                  whileHover={{ scale: 1.04, y: -3 }}
                  className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-sm text-center py-8 px-4"
                >
                  <p className="text-3xl font-bold text-emerald-500 mb-1">{value}</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400 font-medium">{label}</p>
                </motion.div>
              ))}
            </div>
          </motion.section>

          {/* Features Section */}
          <motion.section id="features" variants={itemVariants} className="max-w-7xl mx-auto px-6">
            <div className="text-center mb-12">
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-4">
                Everything You Need to Farm Smarter
              </h2>
              <p className="text-gray-500 dark:text-gray-400 max-w-xl mx-auto text-lg">
                Six integrated AI features working together to help you make better decisions
                at every stage of the growing cycle.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {features.map(({ icon: Icon, title, description, color, bg }) => (
                <motion.div
                  key={title}
                  variants={itemVariants}
                  whileHover={{ scale: 1.03, y: -4 }}
                  className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-sm p-6 cursor-default"
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
          </motion.section>

          {/* How It Works */}
          <motion.section id="about" variants={itemVariants} className="bg-white dark:bg-gray-900 py-20">
            <div className="max-w-7xl mx-auto px-6">
              <div className="text-center mb-12">
                <h2 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-4">
                  How It Works
                </h2>
                <p className="text-gray-500 dark:text-gray-400 max-w-xl mx-auto text-lg">
                  From soil data to actionable insights in four simple steps.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {steps.map(({ icon: Icon, step, title, description }, index) => (
                  <motion.div
                    key={step}
                    variants={itemVariants}
                    whileHover={{ scale: 1.03, y: -4 }}
                    className="relative bg-gray-50 dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6"
                  >
                    <span className="absolute top-5 right-5 text-4xl font-black text-gray-100 dark:text-gray-700 select-none">
                      {step}
                    </span>
                    <div className="inline-flex p-3 rounded-xl bg-emerald-100 dark:bg-emerald-900/30 mb-4">
                      <Icon size={22} className="text-emerald-600 dark:text-emerald-400" />
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
            </div>
          </motion.section>

          {/* CTA Section */}
          <motion.section variants={itemVariants} className="max-w-7xl mx-auto px-6">
            <motion.div
              whileHover={{ scale: 1.01 }}
              className="relative rounded-3xl overflow-hidden bg-gradient-to-br from-gray-900 to-gray-800 dark:from-gray-800 dark:to-gray-900 border border-gray-700 p-10 md:p-16 text-center shadow-2xl"
            >
              <div className="absolute top-0 right-0 w-56 h-56 bg-emerald-500/10 rounded-full -translate-y-1/2 translate-x-1/2 pointer-events-none" />
              <div className="absolute bottom-0 left-0 w-56 h-56 bg-emerald-500/10 rounded-full translate-y-1/2 -translate-x-1/2 pointer-events-none" />
              <div className="relative z-10">
                <div className="inline-flex p-3 rounded-xl bg-emerald-500/20 mb-6">
                  <Sprout size={28} className="text-emerald-400" />
                </div>
                <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
                  Ready to Boost Your Yield?
                </h2>
                <p className="text-gray-400 text-lg mb-8 max-w-xl mx-auto">
                  Join thousands of farmers using AI to make smarter decisions and grow better crops.
                </p>
                <Link to="/dashboard">
                  <motion.button
                    whileHover={{ scale: 1.05, y: -2 }}
                    whileTap={{ scale: 0.95 }}
                    className="inline-flex items-center gap-2 bg-emerald-500 hover:bg-emerald-600 text-white font-bold px-10 py-4 rounded-xl shadow-lg shadow-emerald-900/40 transition-colors duration-200 text-base"
                  >
                    Get Started Now
                    <ArrowRight size={18} />
                  </motion.button>
                </Link>
              </div>
            </motion.div>
          </motion.section>

          {/* Footer */}
          <footer id="contact" className="bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700">
            <div className="max-w-7xl mx-auto px-6 py-12">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-10 mb-10">
                {/* Company Info */}
                <div>
                  <div className="flex items-center gap-2 font-bold text-lg text-gray-900 dark:text-white mb-3">
                    <div className="p-1.5 rounded-lg bg-emerald-500 text-white">
                      <Sprout size={18} />
                    </div>
                    Smart Agriculture
                  </div>
                  <p className="text-sm text-gray-500 dark:text-gray-400 leading-relaxed">
                    AI-powered crop yield prediction and smart farming insights for
                    sustainable, data-driven agriculture.
                  </p>
                </div>

                {/* Quick Links */}
                <div>
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-4">Quick Links</h4>
                  <ul className="space-y-2 text-sm">
                    {[
                      { label: 'Dashboard', to: '/dashboard' },
                      { label: 'Predict Crop', to: '/predict' },
                      { label: 'Weather Data', to: '/weather' },
                      { label: 'AI Recommendations', to: '/recommend' },
                      { label: 'Disease Detection', to: '/disease' },
                    ].map(({ label, to }) => (
                      <li key={label}>
                        <Link
                          to={to}
                          className="text-gray-500 dark:text-gray-400 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors"
                        >
                          {label}
                        </Link>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Contact */}
                <div>
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-4">Contact</h4>
                  <ul className="space-y-3 text-sm">
                    <li className="flex items-center gap-2 text-gray-500 dark:text-gray-400">
                      <Mail size={16} className="text-emerald-500 flex-shrink-0" />
                      support@smartagri.dev
                    </li>
                    <li className="flex items-center gap-2 text-gray-500 dark:text-gray-400">
                      <MapPin size={16} className="text-emerald-500 flex-shrink-0" />
                      India
                    </li>
                    <li className="flex items-center gap-2 text-gray-500 dark:text-gray-400">
                      <Github size={16} className="text-emerald-500 flex-shrink-0" />
                      <a
                        href="https://github.com/rohanpawar2510/Crop-yield-prediction"
                        target="_blank"
                        rel="noreferrer"
                        className="hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors"
                      >
                        GitHub Repository
                      </a>
                    </li>
                  </ul>
                </div>
              </div>

              <div className="border-t border-gray-200 dark:border-gray-700 pt-6 flex flex-col sm:flex-row items-center justify-between gap-3">
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  © {new Date().getFullYear()} Smart Agriculture Dashboard. All rights reserved.
                </p>
                <div className="flex items-center gap-1 text-sm text-gray-500 dark:text-gray-400">
                  <CheckCircle2 size={14} className="text-emerald-500" />
                  Built with React, FastAPI & Machine Learning
                </div>
              </div>
            </div>
          </footer>
        </motion.div>
      </main>
    </div>
  );
}
