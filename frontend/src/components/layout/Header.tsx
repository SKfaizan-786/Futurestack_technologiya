import { Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { Heart, LogOut, User } from 'lucide-react';

export function Header() {
  const { user, signOut } = useAuth();

  return (
    <header className="bg-white border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <Link to="/" className="flex items-center space-x-2">
            <Heart className="w-8 h-8 text-primary-blue" />
            <span className="text-xl font-bold text-gray-900">MedMatch AI</span>
          </Link>

          <nav className="flex items-center space-x-6">
            {user ? (
              <>
                <Link
                  to="/dashboard"
                  className="text-gray-600 hover:text-gray-900 font-medium transition-colors"
                >
                  Dashboard
                </Link>
                <Link
                  to="/search"
                  className="text-gray-600 hover:text-gray-900 font-medium transition-colors"
                >
                  Search Trials
                </Link>
                <Link
                  to="/saved"
                  className="text-gray-600 hover:text-gray-900 font-medium transition-colors"
                >
                  Saved Trials
                </Link>
                <Link
                  to="/profile"
                  className="text-gray-600 hover:text-gray-900 flex items-center space-x-1"
                >
                  <User className="w-4 h-4" />
                  <span>Profile</span>
                </Link>
                <button
                  onClick={() => signOut()}
                  className="text-gray-600 hover:text-gray-900 flex items-center space-x-1"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Sign Out</span>
                </button>
              </>
            ) : (
              <>
                <Link
                  to="/login"
                  className="text-gray-600 hover:text-gray-900 font-medium transition-colors"
                >
                  Sign In
                </Link>
                <Link
                  to="/signup"
                  className="px-4 py-2 bg-primary-blue text-white font-medium rounded-lg hover:bg-blue-600 transition-colors"
                >
                  Get Started
                </Link>
              </>
            )}
          </nav>
        </div>
      </div>
    </header>
  );
}
