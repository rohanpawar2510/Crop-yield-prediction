import { Link, useLocation } from 'react-router-dom';
import { Sprout, Menu, X } from 'lucide-react';
import DarkModeToggle from './DarkModeToggle';
import UserMenu from './UserMenu';

export default function Navbar({ sidebarOpen, setSidebarOpen }) {
  const location = useLocation();

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-white/80 dark:bg-gray-900/80 backdrop-blur-lg border-b border-gray-200 dark:border-gray-700">
      <div className="flex items-center justify-between px-4 h-16">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 rounded-xl text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors lg:hidden"
          >
            {sidebarOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
          <Link to="/" className="flex items-center gap-2 font-bold text-lg text-gray-900 dark:text-white">
            <div className="p-1.5 rounded-lg bg-primary text-white">
              <Sprout size={20} />
            </div>
            <span className="hidden sm:inline">Smart Agriculture</span>
          </Link>
        </div>
        <DarkModeToggle />
        <UserMenu />
      </div>
    </header>
  );
}
