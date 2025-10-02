import { useState } from 'react';
import { Sparkles } from 'lucide-react';

interface NaturalLanguageInputProps {
  onSubmit: (text: string) => Promise<void>;
  isProcessing: boolean;
}

const exampleInputs = [
  "67 year old female with stage 3 non-small cell lung cancer, EGFR positive, previously treated with erlotinib",
  "52 year old male with metastatic colorectal cancer, failed FOLFOX chemotherapy, lives in Boston MA",
  "Stage 4 breast cancer patient, triple negative, age 45, completed radiation therapy 3 months ago",
];

export function NaturalLanguageInput({ onSubmit, isProcessing }: NaturalLanguageInputProps) {
  const [text, setText] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) return;
    await onSubmit(text);
  };

  return (
    <div className="w-full max-w-4xl">
      <div className="mb-6">
        <div className="flex items-center mb-2">
          <Sparkles className="w-5 h-5 text-primary-blue mr-2" />
          <h3 className="text-lg font-semibold text-gray-900">Describe the Patient</h3>
        </div>
        <p className="text-sm text-gray-600">
          Tell us about the patient's condition in your own words. Our AI will understand and find matching trials.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="patient-description" className="sr-only">
            Patient description
          </label>
          <textarea
            id="patient-description"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Example: 65 year old female with stage 3 lung cancer, EGFR positive, previously treated with chemotherapy..."
            rows={6}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-blue focus:border-transparent resize-none"
            aria-describedby="example-inputs"
            disabled={isProcessing}
          />
        </div>

        <div id="example-inputs" className="bg-gray-50 rounded-lg p-4">
          <p className="text-xs font-medium text-gray-700 mb-2">Example inputs:</p>
          <ul className="space-y-2">
            {exampleInputs.map((example, index) => (
              <li key={index}>
                <button
                  type="button"
                  onClick={() => setText(example)}
                  className="text-xs text-primary-blue hover:text-blue-600 hover:underline text-left"
                  disabled={isProcessing}
                >
                  "{example}"
                </button>
              </li>
            ))}
          </ul>
        </div>

        <button
          type="submit"
          disabled={!text.trim() || isProcessing}
          className="w-full py-3 px-6 bg-primary-blue text-white font-medium rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-primary-blue focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isProcessing ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Processing...
            </span>
          ) : (
            'Find Matching Trials'
          )}
        </button>
      </form>
    </div>
  );
}
