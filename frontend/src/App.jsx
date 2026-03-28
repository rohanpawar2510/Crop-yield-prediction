import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { useState } from 'react';
import { ThemeProvider } from './context/ThemeContext';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import Landing from './pages/Landing';
import Dashboard from './pages/Dashboard';
import Weather from './pages/Weather';
import Predict from './pages/Predict';
import Recommend from './pages/Recommend';
import Disease from './pages/Disease';

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <ThemeProvider>
      <BrowserRouter>
        <div className="min-h-screen bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-white">
          <Navbar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />
          <Sidebar open={sidebarOpen} setOpen={setSidebarOpen} />
          <main className="pt-16 lg:pl-64">
            <div className="p-6 max-w-7xl mx-auto">
              <Routes>
                <Route path="/" element={<Landing />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/weather" element={<Weather />} />
                <Route path="/predict" element={<Predict />} />
                <Route path="/recommend" element={<Recommend />} />
                <Route path="/disease" element={<Disease />} />
              </Routes>
            </div>
          </main>
          <Toaster
            position="top-right"
            toastOptions={{
              className: 'dark:bg-gray-800 dark:text-white',
              duration: 4000,
              style: { borderRadius: '12px' },
            }}
          />
        </div>
      </BrowserRouter>
    </ThemeProvider>
  );
}
