import { Link } from 'react-router-dom';
import { History, ChevronRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function PredictionHistoryBanner() {
  const { loggedIn } = useAuth();

  if (!loggedIn) {
    return (
      <div className="flex items-center gap-3 p-3 bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 rounded-xl text-sm">
        <span className="text-blue-600 dark:text-blue-400">💡 Sign in to save predictions to your history</span>
        <Link to="/login" className="ml-auto text-blue-600 dark:text-blue-400 font-medium hover:underline flex items-center gap-1">
          Sign in <ChevronRight size={14} />
        </Link>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3 p-3 bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800 rounded-xl text-sm">
      <History size={16} className="text-green-600 dark:text-green-400 flex-shrink-0" />
      <span className="text-green-700 dark:text-green-300">Prediction saved to your history</span>
      <Link to="/history" className="ml-auto text-green-600 dark:text-green-400 font-medium hover:underline flex items-center gap-1 flex-shrink-0">
        View History <ChevronRight size={14} />
      </Link>
    </div>
  );
}