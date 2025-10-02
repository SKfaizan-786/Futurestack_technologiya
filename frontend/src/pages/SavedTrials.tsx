import { TrialCard } from '../components/trials/TrialCard';
import { useSavedTrials } from '../hooks/useSavedTrials';
import { LoadingState } from '../components/ui/LoadingState';

export function SavedTrials() {
  const { savedTrials, isLoading, removeTrial } = useSavedTrials();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <LoadingState message="Loading saved trials..." />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Saved Clinical Trials</h1>
          <p className="text-gray-600">
            Trials you've bookmarked for future reference
          </p>
        </div>

        {savedTrials.length === 0 ? (
          <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
            <p className="text-gray-500 mb-4">You haven't saved any trials yet.</p>
            <a
              href="/search"
              className="inline-block px-6 py-2 bg-primary-blue text-white font-medium rounded-lg hover:bg-blue-600 transition-colors"
            >
              Search for Trials
            </a>
          </div>
        ) : (
          <div className="space-y-4">
            {savedTrials.map((savedTrial) => (
              <div key={savedTrial.id} className="relative">
                <TrialCard
                  trial={savedTrial.trial_data}
                  isSaved={true}
                  onRemove={async () => {
                    try {
                      await removeTrial(savedTrial.trial_id);
                    } catch (error) {
                      alert('Failed to remove trial. Please try again.');
                    }
                  }}
                />
                {savedTrial.notes && (
                  <div className="mt-2 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <p className="text-sm text-gray-700">
                      <strong>Notes:</strong> {savedTrial.notes}
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
