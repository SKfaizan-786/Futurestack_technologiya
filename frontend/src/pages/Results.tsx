import { useLocation, useNavigate } from 'react-router-dom';
import { TrialList } from '../components/trials/TrialList';
import { useSavedTrials } from '../hooks/useSavedTrials';
import type { TrialMatch, PatientData } from '../types';
import { ArrowLeft } from 'lucide-react';

export function Results() {
  const location = useLocation();
  const navigate = useNavigate();
  const { savedTrials, saveTrial, removeTrial } = useSavedTrials();

  const trials = (location.state?.trials as TrialMatch[]) || [];
  const patientData = location.state?.patientData as PatientData;

  const savedTrialIds = savedTrials.map(st => st.trial_id);

  // Debug logging
  console.log('Results component - trials:', trials);
  console.log('Results component - patientData:', patientData);

  if (!trials || trials.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600 mb-4">No results to display.</p>
          <button
            onClick={() => navigate('/search')}
            className="px-6 py-2 bg-primary-blue text-white font-medium rounded-lg hover:bg-blue-600 transition-colors"
          >
            Start New Search
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <button
          onClick={() => navigate('/search')}
          className="flex items-center text-gray-600 hover:text-gray-900 mb-6 transition-colors"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Search
        </button>

        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Clinical Trial Matches</h1>
          {patientData && patientData.diagnosis && (
            <p className="text-gray-600">
              Results for: {patientData.diagnosis.cancerType || 'Cancer'}, Stage {patientData.diagnosis.stage || 'Unknown'}
              {patientData.location && (
                <>
                  {' '} • {patientData.location.city || 'Unknown'}, {patientData.location.state || 'Unknown'}
                </>
              )}
            </p>
          )}
          {patientData && (patientData as any).medical_query && (
            <p className="text-gray-600">
              Query: "{(patientData as any).medical_query}"
            </p>
          )}
        </div>

        <TrialList
          trials={trials}
          savedTrialIds={savedTrialIds}
          onSave={async (trial) => {
            try {
              await saveTrial({ trial });
              alert('Trial saved successfully!');
            } catch (error) {
              alert('Failed to save trial. Please try again.');
            }
          }}
          onRemove={async (trialId) => {
            try {
              await removeTrial(trialId);
              alert('Trial removed from saved list.');
            } catch (error) {
              alert('Failed to remove trial. Please try again.');
            }
          }}
        />
      </div>
    </div>
  );
}
