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
      // First, process the natural language input to extract patient data
      const patientData = await processNaturalLanguage(text);

      // Then match trials with the extracted patient data
      const response = await matchTrials(patientData);

      // Save search to history
      await saveSearch(patientData, response.matches);

      // Navigate to results page with the data
      navigate('/results', { state: { trials: response.matches, patientData } });
    } catch (error: any) {
      console.error('Error matching trials:', error);
      alert(error.message || 'Failed to find matching trials. Please try again.');
    }
  };

  const handleStructuredFormSubmit = async (patientData: PatientData) => {
    try {
      const response = await matchTrials(patientData);

      // Save search to history
      await saveSearch(patientData, response.matches);

      // Navigate to results page with the data
      navigate('/results', { state: { trials: response.matches, patientData } });
    } catch (error: any) {
      console.error('Error matching trials:', error);
      alert(error.message || 'Failed to find matching trials. Please try again.');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Find Clinical Trials</h1>
          <p className="text-gray-600">
            Enter patient information to find matching clinical trials
          </p>
        </div>

        {/* Mode Switcher */}
        <div className="flex justify-center mb-8">
          <div className="inline-flex rounded-lg border border-gray-300 p-1 bg-white">
            <button
              onClick={() => setMode('natural')}
              className={`px-6 py-2 rounded-md text-sm font-medium transition-colors ${
                mode === 'natural'
                  ? 'bg-primary-blue text-white'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Natural Language
            </button>
            <button
              onClick={() => setMode('structured')}
              className={`px-6 py-2 rounded-md text-sm font-medium transition-colors ${
                mode === 'structured'
                  ? 'bg-primary-blue text-white'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Structured Form
            </button>
          </div>
        </div>

        {/* Input Forms */}
        <div className="flex justify-center">
          {mode === 'natural' ? (
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
