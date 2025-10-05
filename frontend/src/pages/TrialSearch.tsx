import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { NaturalLanguageInput } from '../components/forms/NaturalLanguageInput';
import { StructuredForm } from '../components/forms/StructuredForm';
import { useTrialMatch } from '../hooks/useTrialMatch';
import type { PatientData, TrialMatch } from '../types';

export function TrialSearch() {
  const navigate = useNavigate();
  const [mode, setMode] = useState<'natural' | 'structured'>('natural');
  const { matchTrials, processNaturalLanguage, isMatching, isProcessing, saveSearch } = useTrialMatch();

  const handleNaturalLanguageSubmit = async (text: string) => {
    try {
      const naturalLanguageData = {
        age: 0,
        gender: 'other' as const,
        location: { city: '', state: '', zipCode: '' },
        diagnosis: { cancerType: text, stage: '1' as const },
        treatments: { current: [], previous: [] },
        naturalLanguageQuery: text
      };

      const response = await matchTrials(naturalLanguageData as any);

      const patientDataForHistory: PatientData = {
        age: 0,
        gender: 'other',
        location: { city: 'Unknown', state: 'Unknown', zipCode: 'Unknown' },
        diagnosis: { cancerType: text, stage: '1' },
        treatments: { current: [], previous: [] }
      };

      await saveSearch(patientDataForHistory, response.matches);

      navigate('/results', { state: { trials: response.matches, patientData: patientDataForHistory, originalQuery: text } });
    } catch (error: any) {
      console.error('Error matching trials:', error);
      alert(error.message || 'Failed to find matching trials. Please try again.');
    }
  };

  const handleStructuredFormSubmit = async (patientData: PatientData) => {
    try {
      const response = await matchTrials(patientData);

      await saveSearch(patientData, response.matches);

      navigate('/results', { state: { trials: response.matches, patientData } });
    } catch (error: any) {
      console.error('Error matching trials:', error);
      alert(error.message || 'Failed to find matching trials. Please try again.');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center mb-10">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Find Your Clinical Trial Match</h1>
          <p className="text-gray-600 text-lg">Share your medical information, and our AI will find the top 3 clinical trials you're eligible for—in under 100ms.</p>
          <div className="flex justify-center mt-6 space-x-4 text-gray-500">
            <span className="flex items-center gap-2">
              <span className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">1</span>
              <span>Enter Info</span>
            </span>
            <span className="border-l border-gray-300 h-6"></span>
            <span className="flex items-center gap-2">
              <span className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">2</span>
              <span>AI Matches</span>
            </span>
            <span className="border-l border-gray-300 h-6"></span>
            <span className="flex items-center gap-2">
              <span className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">3</span>
              <span>Get Results</span>
            </span>
          </div>
        </div>

        <div className="flex justify-center mb-8 space-x-4">
          <button
            onClick={() => setMode('structured')}
            className={`px-6 py-3 rounded-lg text-sm font-medium transition-colors flex items-center gap-2 ${
              mode === 'structured' ? 'bg-[#1e68d1] text-white' : 'text-gray-700 bg-gray-100 hover:bg-gray-200'
            }`}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5h6m-6 0a3 3 0 01-3-3m3 3a3 3 0 003 3m-3-3v12m0 0a3 3 0 01-3 3m3-3a3 3 0 003-3m-6 0h6m-6 0a1 1 0 01-1-1m1 1a1 1 0 011 1m-1-1v-2m0 6v-2m6 0h-6m6 0a1 1 0 011 1m-1-1a1 1 0 00-1-1m1 1v2m0-6v2" />
            </svg>
            Structured Form
          </button>
          <button
            onClick={() => setMode('natural')}
            className={`px-6 py-3 rounded-lg text-sm font-medium transition-colors flex items-center gap-2 ${
              mode === 'natural' ? 'bg-[#1e68d1] text-white' : 'text-gray-700 bg-gray-100 hover:bg-gray-200'
            }`}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M9 16c-7 0-9-4-9-4s2-4 9-4m9 4c0 0-2 4-9 4m9-4v12m-9 0v-12" />
            </svg>
            Describe My Condition
          </button>
        </div>

        {/* Instructional text outside the form box */}
        <div className="text-center mb-6">
          <p className="text-gray-600 text-sm">
            <strong>New to clinical trials?</strong> Use "Describe My Condition" to tell us in your own words.<br />
            <strong>Have medical records?</strong> Use the structured form for precise matching.
          </p>
        </div>

        <div className="bg-white shadow-lg rounded-lg p-6">{mode === 'natural' ? (
            <NaturalLanguageInput
              onSubmit={handleNaturalLanguageSubmit}
              isProcessing={isProcessing || isMatching}
            />
          ) : (
            <StructuredForm
              onSubmit={handleStructuredFormSubmit}
              isProcessing={isMatching}
            />
          )}
        </div>
      </div>
    </div>
  );
}