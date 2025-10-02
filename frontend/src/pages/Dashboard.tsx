import { Link } from 'react-router-dom';
import { Search, BookmarkCheck, Clock } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useTrialMatch } from '../hooks/useTrialMatch';

export function Dashboard() {
  const { user } = useAuth();
  const { searchHistory } = useTrialMatch();

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Welcome back{user?.user_metadata?.full_name ? `, ${user.user_metadata.full_name}` : ''}
          </h1>
          <p className="mt-2 text-gray-600">
            Find clinical trials that match your needs
          </p>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <Link
            to="/search"
            className="bg-white p-6 rounded-lg border border-gray-200 hover:shadow-md transition-shadow"
          >
            <div className="w-12 h-12 bg-primary-blue bg-opacity-10 rounded-lg flex items-center justify-center mb-4">
              <Search className="w-6 h-6 text-primary-blue" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Search for Trials</h3>
            <p className="text-sm text-gray-600">
              Find clinical trials that match patient criteria
            </p>
          </Link>

          <Link
            to="/saved"
            className="bg-white p-6 rounded-lg border border-gray-200 hover:shadow-md transition-shadow"
          >
            <div className="w-12 h-12 bg-secondary-green bg-opacity-10 rounded-lg flex items-center justify-center mb-4">
              <BookmarkCheck className="w-6 h-6 text-secondary-green" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Saved Trials</h3>
            <p className="text-sm text-gray-600">
              View and manage your saved clinical trials
            </p>
          </Link>

          <Link
            to="/history"
            className="bg-white p-6 rounded-lg border border-gray-200 hover:shadow-md transition-shadow"
          >
            <div className="w-12 h-12 bg-primary-teal bg-opacity-10 rounded-lg flex items-center justify-center mb-4">
              <Clock className="w-6 h-6 text-primary-teal" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Search History</h3>
            <p className="text-sm text-gray-600">
              Review your previous trial searches
            </p>
          </Link>
        </div>

        {/* Recent Searches */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Searches</h2>
          {searchHistory.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500 mb-4">You haven't searched for any trials yet.</p>
              <Link
                to="/search"
                className="inline-block px-6 py-2 bg-primary-blue text-white font-medium rounded-lg hover:bg-blue-600 transition-colors"
              >
                Start Your First Search
              </Link>
            </div>
          ) : (
            <div className="space-y-4">
              {searchHistory.slice(0, 5).map((search) => (
                <div
                  key={search.id}
                  className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {search.patient_data.diagnosis.cancerType} - Stage {search.patient_data.diagnosis.stage}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        {new Date(search.created_at).toLocaleDateString()} • {search.search_results.length} matches found
                      </p>
                    </div>
                    <Link
                      to={`/history/${search.id}`}
                      className="text-sm text-primary-blue hover:underline"
                    >
                      View Results
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
