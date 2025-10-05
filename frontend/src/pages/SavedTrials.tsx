import { useSavedTrials } from '../hooks/useSavedTrials';
import { LoadingState } from '../components/ui/LoadingState';
import { CheckCircle, FileText, Clock, Calendar, BookOpen, User, MapPin, Phone, Mail } from 'lucide-react';
import { useState } from 'react';

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
      {/* Header Section */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="text-center">
            <div className="flex justify-center mb-6">
              <BookOpen className="w-16 h-16 text-blue-500" />
            </div>
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              Your Saved Trials
            </h1>
            <p className="text-gray-600 text-lg mb-6">
              Clinical trials you've bookmarked for future reference and
              <br />
              easy access.
            </p>

            {/* Statistics Box */}
            <div className="inline-flex items-center bg-gray-50 border border-gray-200 rounded-lg px-6 py-3 space-x-6 text-sm text-gray-600">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4" />
                <span>
                  {savedTrials.length} saved trial
                  {savedTrials.length !== 1 ? 's' : ''}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4" />
                <span>Always accessible</span>
              </div>
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4" />
                <span>
                  Last updated{' '}
                  {new Date().toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                  })}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-none mx-auto px-[10%] py-8">
        {savedTrials.length === 0 ? (
          <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
            <BookOpen className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              No Saved Trials Yet
            </h3>
            <p className="text-gray-500 mb-6">
              Start by searching for clinical trials and save the ones that
              interest you.
            </p>
            <a
              href="/search"
              className="inline-block px-6 py-3 bg-[#1e68d1] text-white font-medium rounded-lg hover:bg-blue-600 transition-colors"
            >
              Search for Trials
            </a>
          </div>
        ) : (
          <>
            {/* Trial Results */}
            <div className="space-y-6 mb-12">
              {savedTrials.map((savedTrial, index) => {
                const trial = savedTrial.trial_data;
                const [expanded, setExpanded] = useState(false);
                
                // Generate mock institution name (same as Results.tsx)
                const institutions = [
                  'Johns Hopkins University',
                  'Mayo Clinic',
                  'MD Anderson Cancer Center',
                  'Memorial Sloan Kettering',
                  'Dana-Farber Cancer Institute',
                  'Cleveland Clinic',
                  'Stanford University Medical Center',
                  'University of Pennsylvania'
                ];
                
                const institutionName = institutions[index % institutions.length];

                // Generate mock detailed data
                const eligibilityCriteria = [
                  'Histologically or cytologically confirmed diagnosis',
                  'Age 18 years or older',
                  'ECOG performance status 0-2',
                  'Adequate hematologic function',
                  'Adequate hepatic function',
                  'Life expectancy of at least 12 weeks',
                  'Signed informed consent'
                ];

                const contactPhone = '(713) 555-9442';
                const contactEmail = `trials.nct${trial.nctId}@clinicalcenter.org`;
                
                const getMatchColor = (score: number) => {
                  if (score >= 90) return 'bg-green-500';
                  if (score >= 80) return 'bg-green-400';
                  if (score >= 70) return 'bg-yellow-400';
                  return 'bg-gray-400';
                };

                const getBadgeText = (score: number) => {
                  if (score >= 90) return 'Excellent Match';
                  if (score >= 80) return 'Good Match';
                  return 'Potential Match';
                };

                const formatExplanation = (explanation: string) => {
                  const sections = explanation.split('**');
                  const formatted = [];
                  
                  for (let i = 0; i < sections.length; i++) {
                    if (i % 2 === 1) {
                      formatted.push(<strong key={i} className="font-bold text-gray-900">{sections[i]}</strong>);
                    } else {
                      const text = sections[i];
                      if (text.trim()) {
                        formatted.push(<span key={i}>{text}</span>);
                      }
                    }
                  }
                  
                  return formatted;
                };

                return (
                  <div key={savedTrial.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <div className="flex items-start gap-4">
                      {/* Number badge */}
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 bg-[#1e68d1] text-white rounded-full flex items-center justify-center font-bold text-lg">
                          {index + 1}
                        </div>
                      </div>
                      
                      <div className="flex-1">
                        {/* Trial header */}
                        <div className="flex items-start justify-between mb-4">
                          <div className="flex-1">
                            <h3 className="text-xl font-bold text-gray-900 mb-2">{trial.title}</h3>
                            <div className="flex items-center gap-4 text-sm text-gray-600">
                              <span>NCT{trial.nctId}</span>
                              <span>•</span>
                              <span>{trial.phase}</span>
                              <span>•</span>
                              <span>{institutionName}</span>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">
                              SAVED
                            </span>
                            {trial.matchScore && (
                              <span className={`${getBadgeText(trial.matchScore) === 'Excellent Match' ? 'bg-green-100 text-green-800' : getBadgeText(trial.matchScore) === 'Good Match' ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'} px-3 py-1 rounded-full text-sm font-medium`}>
                                {getBadgeText(trial.matchScore)}
                              </span>
                            )}
                          </div>
                        </div>

                        {/* Match confidence - only show if matchScore exists */}
                        {trial.matchScore && (
                          <div className="mb-6">
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-sm font-medium text-gray-700">Match Confidence</span>
                              <span className="text-sm font-bold text-gray-900">{trial.matchScore}%</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div 
                                className={`h-2 rounded-full ${getMatchColor(trial.matchScore)}`}
                                style={{ width: `${trial.matchScore}%` }}
                              ></div>
                            </div>
                          </div>
                        )}

                        {/* Why this trial matches - only show if explanation exists */}
                        {trial.explanation && (
                          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                            <h4 className="font-semibold text-gray-900 mb-2">Why this trial:</h4>
                            <div className="text-sm text-gray-700 leading-relaxed">
                              {formatExplanation(trial.explanation)}
                            </div>
                          </div>
                        )}

                        {/* Expanded details */}
                        {expanded && (
                          <div className="mb-6 p-6 border border-gray-200 rounded-lg bg-gray-50">
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                              {/* Eligibility Criteria */}
                              <div>
                                <h4 className="text-lg font-semibold text-gray-900 mb-4">Eligibility Criteria</h4>
                                <ul className="space-y-2">
                                  {eligibilityCriteria.map((criteria, idx) => (
                                    <li key={idx} className="flex items-start gap-2 text-sm text-gray-700">
                                      <span className="text-green-500 mt-1 text-xs">•</span>
                                      <span>{criteria}</span>
                                    </li>
                                  ))}
                                </ul>
                              </div>

                              {/* Trial Information */}
                              <div>
                                <h4 className="text-lg font-semibold text-gray-900 mb-4">Trial Information</h4>
                                <div className="space-y-2 text-sm">
                                  <div>
                                    <span className="text-gray-600">Phase: </span>
                                    <span className="font-medium text-gray-900">{trial.phase}</span>
                                  </div>
                                  <div>
                                    <span className="text-gray-600">Status: </span>
                                    <span className="font-medium text-gray-900">{trial.status || 'RECRUITING'}</span>
                                  </div>
                                </div>
                              </div>

                              {/* Contact Information */}
                              <div>
                                <h4 className="text-lg font-semibold text-gray-900 mb-4">Contact Information</h4>
                                <div className="space-y-3">
                                  <div className="flex items-center gap-2 text-sm">
                                    <Phone className="w-4 h-4 text-gray-400 flex-shrink-0" />
                                    <a href={`tel:${contactPhone}`} className="text-blue-600 hover:text-blue-800">
                                      {contactPhone}
                                    </a>
                                  </div>
                                  <div className="flex items-center gap-2 text-sm">
                                    <Mail className="w-4 h-4 text-gray-400 flex-shrink-0" />
                                    <a href={`mailto:${contactEmail}`} className="text-blue-600 hover:text-blue-800 break-all">
                                      {contactEmail}
                                    </a>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>
                        )}

                        {/* Notes section */}
                        {savedTrial.notes && (
                          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
                            <h4 className="font-semibold text-gray-900 mb-2">Your Notes:</h4>
                            <div className="text-sm text-gray-700">
                              {savedTrial.notes}
                            </div>
                          </div>
                        )}

                        {/* Action buttons */}
                        <div className="flex gap-3">
                          <button 
                            onClick={() => setExpanded(!expanded)}
                            className="flex-1 bg-gradient-to-r from-blue-600 to-cyan-500 text-white px-4 py-1 rounded-lg hover:from-blue-700 hover:to-cyan-600 transition-all duration-200 flex items-center justify-center"
                          >
                            {expanded ? 'Hide Details' : 'View Full Details'}
                          </button>
                          <button 
                            onClick={async () => {
                              try {
                                await removeTrial(savedTrial.trial_id);
                                alert('Trial removed successfully!');
                              } catch (error) {
                                alert('Failed to remove trial. Please try again.');
                              }
                            }}
                            className="px-4 py-1 border border-red-300 bg-red-50 text-red-700 rounded-lg hover:bg-red-100 transition-colors flex items-center justify-center"
                          >
                            <span className="flex items-center">
                              <BookOpen className="w-4 h-4 mr-2" />
                              Remove Trial
                            </span>
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
