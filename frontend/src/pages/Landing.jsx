import { useState, useEffect } from 'react';
import { motion, useInView } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  Sprout, CloudSun, Brain, Microscope, BarChart3,
  ArrowRight, CheckCircle2, Upload, Cpu, TrendingUp,
  Lightbulb, Menu, X, Moon, Sun, Mail, MapPin,
  History, Github, ChevronDown,
} from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';

// ── Features ──────────────────────────────────────────────────────────────────
const features = [
  {
    icon: Sprout,
    title: 'Crop Prediction',
    desc: 'XGBoost model delivering 99% accuracy across 20 Maharashtra crops based on soil and climate data.',
    color: 'emerald',
    tag: 'ML Model',
  },
  {
    icon: CloudSun,
    title: 'Live Weather',
    desc: 'OpenWeather API integration — real-time temperature, humidity and rainfall for your district.',
    color: 'blue',
    tag: 'Real-time',
  },
  {
    icon: Brain,
    title: 'AI Recommendations',
    desc: 'Gemini AI generates crop-specific fertilizer plans personalised to your soil and location.',
    color: 'purple',
    tag: 'Gemini AI',
  },
  {
    icon: Microscope,
    title: 'Disease Detection',
    desc: 'Upload a leaf photo — Plant.id API identifies disease and suggests treatment instantly.',
    color: 'red',
    tag: 'Vision AI',
  },
  {
    icon: BarChart3,
    title: 'Analytics Dashboard',
    desc: 'NPK radar charts, yield comparisons, confidence scores and visual soil insights.',
    color: 'amber',
    tag: 'Charts',
  },
  {
    icon: History,
    title: 'Prediction History',
    desc: 'Every prediction and recommendation saved securely to your account — review anytime.',
    color: 'teal',
    tag: 'Database',
  },
];

const colorMap = {
  emerald: { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/20', tag: 'bg-emerald-500/10 text-emerald-400' },
  blue:    { bg: 'bg-blue-500/10',    text: 'text-blue-400',    border: 'border-blue-500/20',    tag: 'bg-blue-500/10 text-blue-400' },
  purple:  { bg: 'bg-purple-500/10',  text: 'text-purple-400',  border: 'border-purple-500/20',  tag: 'bg-purple-500/10 text-purple-400' },
  red:     { bg: 'bg-red-500/10',     text: 'text-red-400',     border: 'border-red-500/20',     tag: 'bg-red-500/10 text-red-400' },
  amber:   { bg: 'bg-amber-500/10',   text: 'text-amber-400',   border: 'border-amber-500/20',   tag: 'bg-amber-500/10 text-amber-400' },
  teal:    { bg: 'bg-teal-500/10',    text: 'text-teal-400',    border: 'border-teal-500/20',    tag: 'bg-teal-500/10 text-teal-400' },
};

const steps = [
  { icon: Upload,     num: '01', title: 'Enter Soil Data',  desc: 'Input NPK values, pH, area, irrigation type and your district.',           color: 'emerald' },
  { icon: Cpu,        num: '02', title: 'AI Processes',     desc: 'XGBoost model analyses your data against agronomic records.',               color: 'blue'    },
  { icon: TrendingUp, num: '03', title: 'Get Predictions',  desc: 'Receive crop recommendation, confidence score and yield in tons/ha.',       color: 'purple'  },
  { icon: Lightbulb,  num: '04', title: 'Act on Insights',  desc: 'Get Gemini AI fertilizer plan and save results to your history.',           color: 'amber'   },
];

const navLinks = [
  { label: 'Features',     href: '#features' },
  { label: 'How It Works', href: '#how'      },
  { label: 'Contact',      href: '#contact'  },
];

// ── Navbar ────────────────────────────────────────────────────────────────────
function LandingNavbar() {
  const { isDark, toggleTheme } = useTheme();
  const { loggedIn, user }      = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <header className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
      scrolled
        ? 'bg-gray-950/90 backdrop-blur-xl border-b border-white/5 shadow-lg'
        : 'bg-transparent'
    }`}>
      <div className="max-w-7xl mx-auto flex items-center justify-between px-6 h-16">

        {/* Logo */}
        <Link to="/" className="flex items-center gap-2.5 font-bold text-lg text-white">
          <div className="p-1.5 rounded-lg bg-emerald-500">
            <Sprout size={20} />
          </div>
          <span className="tracking-tight">Smart<span className="text-emerald-400">Agri</span></span>
        </Link>

        {/* Desktop nav */}
        <nav className="hidden md:flex items-center gap-8">
          {navLinks.map(({ label, href }) => (
            <a key={label} href={href}
              className="text-sm font-medium text-gray-400 hover:text-white transition-colors duration-200">
              {label}
            </a>
          ))}
        </nav>

        {/* Desktop actions */}
        <div className="hidden md:flex items-center gap-3">
          <button onClick={toggleTheme}
            className="p-2 rounded-xl text-gray-400 hover:text-white hover:bg-white/10 transition-all duration-200">
            {isDark ? <Sun size={18} /> : <Moon size={18} />}
          </button>
          {loggedIn ? (
            <div className="flex items-center gap-3">
              <span className="text-sm text-gray-400">
                Hi, <span className="text-white font-medium">{user?.name?.split(' ')[0]}</span>
              </span>
              <Link to="/dashboard">
                <button className="flex items-center gap-2 bg-emerald-500 hover:bg-emerald-400 text-white font-semibold px-5 py-2 rounded-xl transition text-sm">
                  Dashboard <ArrowRight size={14} />
                </button>
              </Link>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Link to="/login">
                <button className="text-sm font-medium text-gray-400 hover:text-white px-4 py-2 rounded-xl hover:bg-white/10 transition">
                  Sign In
                </button>
              </Link>
              <Link to="/register">
                <button className="flex items-center gap-2 bg-emerald-500 hover:bg-emerald-400 text-white font-semibold px-5 py-2 rounded-xl transition text-sm">
                  Get Started <ArrowRight size={14} />
                </button>
              </Link>
            </div>
          )}
        </div>

        {/* Mobile menu toggle */}
        <div className="flex md:hidden items-center gap-2">
          <button onClick={toggleTheme} className="p-2 rounded-xl text-gray-400 hover:text-white">
            {isDark ? <Sun size={18} /> : <Moon size={18} />}
          </button>
          <button onClick={() => setMenuOpen(!menuOpen)} className="p-2 rounded-xl text-gray-400 hover:text-white">
            {menuOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className="md:hidden bg-gray-950/95 backdrop-blur-xl border-t border-white/5 px-6 py-5 flex flex-col gap-4">
          {navLinks.map(({ label, href }) => (
            <a key={label} href={href} onClick={() => setMenuOpen(false)}
              className="text-sm font-medium text-gray-400 hover:text-white transition">
              {label}
            </a>
          ))}
          <div className="flex flex-col gap-2 pt-2 border-t border-white/5">
            {loggedIn ? (
              <Link to="/dashboard" onClick={() => setMenuOpen(false)}>
                <button className="w-full bg-emerald-500 text-white font-semibold py-2.5 rounded-xl text-sm">
                  Dashboard
                </button>
              </Link>
            ) : (
              <>
                <Link to="/login" onClick={() => setMenuOpen(false)}>
                  <button className="w-full border border-white/10 text-gray-300 py-2.5 rounded-xl text-sm">
                    Sign In
                  </button>
                </Link>
                <Link to="/register" onClick={() => setMenuOpen(false)}>
                  <button className="w-full bg-emerald-500 text-white font-semibold py-2.5 rounded-xl text-sm">
                    Get Started
                  </button>
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </header>
  );
}

// ── Main ──────────────────────────────────────────────────────────────────────
export default function Landing() {
  const { loggedIn } = useAuth();

  return (
    <div className="min-h-screen bg-white dark:bg-gray-950 text-gray-900 dark:text-white overflow-x-hidden transition-colors duration-300">
      <LandingNavbar />

      {/* ── Hero ── */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden">

        {/* Background grid */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(16,185,129,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(16,185,129,0.03)_1px,transparent_1px)] bg-[size:60px_60px]" />

        {/* Radial glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-emerald-500/8 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 max-w-5xl mx-auto px-6 text-center pt-20">

          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
            className="inline-flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/20 rounded-full px-4 py-1.5 text-sm text-emerald-400 font-medium mb-8">
            🌾 AI-Powered · Maharashtra Focused
          </motion.div>

          {/* Heading */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35 }}
            className="text-5xl md:text-7xl font-black leading-[1.05] tracking-tight mb-6">
            <span className="text-white">Farm Smarter</span>
            <br />
            <span className="bg-gradient-to-r from-emerald-400 via-teal-400 to-emerald-300 bg-clip-text text-transparent">
              with AI Precision
            </span>
          </motion.h1>

          {/* Subtext */}
          <motion.p
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}
            className="text-lg md:text-xl text-gray-400 mb-10 max-w-2xl mx-auto leading-relaxed">
            Predict the best crop for your soil, get real yield estimates in tons/ha,
            and receive AI-powered fertilizer plans — all in seconds.
          </motion.p>

          {/* CTA buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.65 }}
            className="flex flex-wrap gap-4 justify-center">
            {loggedIn ? (
              <Link to="/predict">
                <button className="flex items-center gap-2 bg-emerald-500 hover:bg-emerald-400 text-white font-bold px-8 py-4 rounded-2xl shadow-xl transition text-base">
                  Go to Dashboard <ArrowRight size={18} />
                </button>
              </Link>
            ) : (
              <>
                <Link to="/register">
                  <button className="flex items-center gap-2 bg-emerald-500 hover:bg-emerald-400 text-white font-bold px-8 py-4 rounded-2xl shadow-xl transition text-base">
                    Get Started <ArrowRight size={18} />
                  </button>
                </Link>
                <Link to="/login">
                  <button className="flex items-center gap-2 border border-white/10 hover:border-white/20 hover:bg-white/5 text-gray-300 font-semibold px-8 py-4 rounded-2xl transition text-base">
                    Sign In
                  </button>
                </Link>
              </>
            )}
          </motion.div>

          {/* Trust badges */}
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.9 }}
            className="flex flex-wrap justify-center gap-6 mt-10 text-xs text-gray-500">
            {[
              '✅ Free to use',
              '🔒 JWT secured',
              '🌾 35 Maharashtra districts',
              '🤖 Gemini AI powered',
            ].map(t => <span key={t}>{t}</span>)}
          </motion.div>

          {/* Scroll cue */}
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.1 }}
            className="mt-16 flex flex-col items-center gap-1 text-gray-600 cursor-pointer"
            onClick={() => document.getElementById('stats')?.scrollIntoView({ behavior: 'smooth' })}>
            <span className="text-xs">Scroll to explore</span>
            <ChevronDown size={16} />
          </motion.div>
        </div>
      </section>

      {/* ── Stats ── */}
      <section id="stats" className="py-20 border-t border-white/5">
        <div className="max-w-5xl mx-auto px-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {[
              { value: '99%',  label: 'Model Accuracy',    sub: 'XGBClassifier on test data' },
              { value: '20+',  label: 'Crops Supported',   sub: 'Maharashtra crops'          },
              { value: '35',   label: 'Districts Covered', sub: 'all of Maharashtra'         },
              { value: 'R²=0.99', label: 'Yield Model',   sub: 'XGBRegressor performance'   },
            ].map(({ value, label, sub }) => (
              <motion.div key={label}
                initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }} transition={{ duration: 0.4 }}
                className="text-center p-6 rounded-2xl bg-white/3 border border-white/5 hover:border-emerald-500/20 transition-all duration-300">
                <p className="text-3xl font-black text-emerald-400 mb-1">{value}</p>
                <p className="text-sm font-semibold text-white mb-0.5">{label}</p>
                <p className="text-xs text-gray-500">{sub}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Features ── */}
      <section id="features" className="py-24">
        <div className="max-w-7xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }} className="text-center mb-16">
            <p className="text-emerald-400 text-sm font-semibold tracking-widest uppercase mb-3">What We Offer</p>
            <h2 className="text-4xl md:text-5xl font-black tracking-tight mb-4">
              Everything a Maharashtra Farmer Needs
            </h2>
            <p className="text-gray-400 max-w-xl mx-auto text-lg">
              Six integrated modules — from AI crop prediction to disease detection and smart recommendations.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {features.map(({ icon: Icon, title, desc, color, tag }, i) => {
              const c = colorMap[color];
              return (
                <motion.div key={title}
                  initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }} transition={{ delay: i * 0.06 }}
                  className={`p-6 rounded-2xl bg-white/3 border ${c.border} hover:bg-white/5 transition-all duration-300`}>
                  <div className="flex items-start justify-between mb-4">
                    <div className={`p-2.5 rounded-xl ${c.bg}`}>
                      <Icon size={20} className={c.text} />
                    </div>
                    <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${c.tag}`}>{tag}</span>
                  </div>
                  <h3 className="text-base font-bold text-white mb-2">{title}</h3>
                  <p className="text-sm text-gray-400 leading-relaxed">{desc}</p>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── How It Works ── */}
      <section id="how" className="py-24 border-t border-white/5">
        <div className="max-w-5xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }} className="text-center mb-16">
            <p className="text-emerald-400 text-sm font-semibold tracking-widest uppercase mb-3">Simple Process</p>
            <h2 className="text-4xl md:text-5xl font-black tracking-tight mb-4">From Soil to Insight</h2>
            <p className="text-gray-400 max-w-lg mx-auto">
              Four steps from your soil data to actionable farming decisions.
            </p>
          </motion.div>

          <div className="relative">
            {/* Connector line */}
            <div className="hidden lg:block absolute top-12 left-[12.5%] right-[12.5%] h-px bg-gradient-to-r from-transparent via-emerald-500/30 to-transparent" />

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {steps.map(({ icon: Icon, title, desc, color }, i) => {
                const c = colorMap[color];
                return (
                  <motion.div key={i}
                    initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }} transition={{ delay: i * 0.1 }}
                    className="relative text-center">
                    <div className="flex justify-center mb-4">
                      <div className={`relative p-4 rounded-2xl ${c.bg} border ${c.border}`}>
                        <Icon size={24} className={c.text} />
                        <span className={`absolute -top-2 -right-2 text-xs font-black ${c.text} ${c.bg} border ${c.border} w-6 h-6 rounded-full flex items-center justify-center`}>
                          {i + 1}
                        </span>
                      </div>
                    </div>
                    <h3 className="text-base font-bold text-white mb-2">{title}</h3>
                    <p className="text-sm text-gray-400 leading-relaxed">{desc}</p>
                  </motion.div>
                );
              })}
            </div>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }} className="text-center mt-12">
            <Link to={loggedIn ? '/predict' : '/register'}>
              <button className="inline-flex items-center gap-2 bg-emerald-500 hover:bg-emerald-400 text-white font-bold px-8 py-3.5 rounded-xl shadow-lg transition text-sm">
                {loggedIn ? 'Start Predicting' : 'Get Started — Free'} <ArrowRight size={16} />
              </button>
            </Link>
          </motion.div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="py-24">
        <div className="max-w-4xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="relative rounded-3xl overflow-hidden border border-emerald-500/20 bg-gradient-to-br from-emerald-950/80 via-gray-900 to-teal-950/50 p-12 md:p-16 text-center">

            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-96 h-1 bg-gradient-to-r from-transparent via-emerald-500/50 to-transparent" />

            <div className="relative z-10">
              <div className="inline-flex p-3 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 mb-6">
                <Sprout size={28} className="text-emerald-400" />
              </div>
              <h2 className="text-3xl md:text-5xl font-black tracking-tight text-white mb-4">
                Ready to Farm Smarter?
              </h2>
              <p className="text-gray-400 text-lg mb-8 max-w-lg mx-auto">
                Create a free account and get your first crop prediction in under 60 seconds.
              </p>
              {loggedIn ? (
                <Link to="/predict">
                  <button className="inline-flex items-center gap-2 bg-emerald-500 hover:bg-emerald-400 text-white font-bold px-10 py-4 rounded-2xl shadow-xl transition text-base">
                    Predict Now <ArrowRight size={18} />
                  </button>
                </Link>
              ) : (
                <div className="flex flex-wrap gap-4 justify-center">
                  <Link to="/register">
                    <button className="inline-flex items-center gap-2 bg-emerald-500 hover:bg-emerald-400 text-white font-bold px-10 py-4 rounded-2xl shadow-xl transition text-base">
                      Create Account <ArrowRight size={18} />
                    </button>
                  </Link>
                  <Link to="/login">
                    <button className="inline-flex items-center gap-2 border border-white/10 hover:border-white/20 text-gray-300 hover:text-white font-semibold px-10 py-4 rounded-2xl transition text-base">
                      Sign In
                    </button>
                  </Link>
                </div>
              )}
              <p className="text-xs text-gray-600 mt-6">Built for Maharashtra Farmers · Final Year Project · PDEA COE Pune</p>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer id="contact" className="border-t border-white/5 bg-gray-950">
        <div className="max-w-7xl mx-auto px-6 py-14">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-10 mb-10">

            {/* Brand */}
            <div className="md:col-span-1">
              <div className="flex items-center gap-2.5 font-bold text-lg text-white mb-3">
                <div className="p-1.5 rounded-lg bg-emerald-500"><Sprout size={18} /></div>
                Smart<span className="text-emerald-400">Agri</span>
              </div>
              <p className="text-sm text-gray-500 leading-relaxed max-w-xs">
                AI-powered crop yield prediction and smart farming platform built specifically
                for Maharashtra farmers.
              </p>
              {!loggedIn && (
                <div className="flex gap-3 mt-5">
                  <Link to="/login" className="text-xs border border-white/10 text-gray-400 hover:text-white px-4 py-2 rounded-lg hover:border-white/20 transition">
                    Sign In
                  </Link>
                  <Link to="/register" className="text-xs bg-emerald-500 hover:bg-emerald-400 text-white px-4 py-2 rounded-lg font-medium transition">
                    Register
                  </Link>
                </div>
              )}
            </div>

            {/* Platform — NOT clickable, login required notice */}
            <div>
              <h4 className="text-sm font-semibold text-white mb-4">Platform</h4>
              <ul className="space-y-2.5 text-sm">
                {[
                  'Crop Prediction',
                  'Weather Forecast',
                  'AI Recommendations',
                  'Disease Detection',
                  'Analytics Dashboard',
                  'Prediction History',
                ].map(label => (
                  <li key={label} className="flex items-center gap-2 text-gray-500">
                    <CheckCircle2 size={12} className="text-emerald-500 flex-shrink-0" />
                    {label}
                  </li>
                ))}
              </ul>
              {!loggedIn && (
                <p className="text-xs text-gray-600 mt-3">
                  🔒 Login required to access modules
                </p>
              )}
            </div>

            {/* Contact */}
            <div>
              <h4 className="text-sm font-semibold text-white mb-4">Contact</h4>
              <ul className="space-y-3 text-sm">
                <li className="flex items-center gap-2 text-gray-500">
                  <Mail size={14} className="text-emerald-500 flex-shrink-0" />
                  rohanpawar2510@gmail.com
                </li>
                <li className="flex items-center gap-2 text-gray-500">
                  <MapPin size={14} className="text-emerald-500 flex-shrink-0" />
                  PDEA COE, Pune, Maharashtra
                </li>
                <li className="flex items-center gap-2 text-gray-500">
                  <Github size={14} className="text-emerald-500 flex-shrink-0" />
                  <a href="https://github.com/rohanpawar2510/Crop-yield-prediction"
                    target="_blank" rel="noreferrer"
                    className="hover:text-emerald-400 transition-colors">
                    GitHub Repository
                  </a>
                </li>
              </ul>
            </div>
          </div>

          <div className="border-t border-white/5 pt-6 flex flex-col sm:flex-row items-center justify-between gap-3">
            <p className="text-xs text-gray-600">© {new Date().getFullYear()} SmartAgri</p>
            
          </div>
        </div>
      </footer>
    </div>
  );
}