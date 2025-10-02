import { MapPin, Phone, Mail, Bookmark, BookmarkCheck } from 'lucide-react';
import { useState } from 'react';
import type { TrialMatch } from '../../types';

interface TrialCardProps {
  trial: TrialMatch;
  isSaved?: boolean;
  onSave?: () => void;
  onRemove?: () => void;
}

export function TrialCard({ trial, isSaved = false, onSave, onRemove }: TrialCardProps) {
  const [expanded, setExpanded] = useState(false);

  const getMatchColor = (score: number) => {
    if (score >= 80) return 'bg-secondary-green text-white';
    if (score >= 60) return 'bg-secondary-cyan text-gray-900';
    return 'bg-gray-300 text-gray-900';
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-6 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <div className="flex items-start justify-between">
            <h3 className="text-lg font-semibold text-gray-900 pr-4">{trial.title}</h3>
            <span className={`${getMatchColor(trial.matchScore)} px-3 py-1 rounded-full text-sm font-medium whitespace-nowrap`}>
              {trial.matchScore}% Match
            </span>
          </div>
          <p className="text-sm text-gray-500 mt-1">NCT ID: {trial.nctId}</p>
        </div>
      </div>

      <div className="space-y-3">
        <div className="flex items-center text-gray-600">
          <MapPin className="w-4 h-4 mr-2 flex-shrink-0" />
          <span className="text-sm">
            {trial.location.facility}, {trial.location.city}, {trial.location.state} • {trial.location.distance} miles away
          </span>
        </div>

        <div className="bg-gray-50 p-4 rounded-lg">
          <p className="text-sm text-gray-700">
            <strong className="text-gray-900">Why this matches:</strong> {trial.explanation}
          </p>
        </div>

        {expanded && (
          <div className="space-y-3 pt-3 border-t border-gray-200">
            <div>
              <h4 className="text-sm font-semibold text-gray-900 mb-2">Eligibility Criteria</h4>
              <ul className="list-disc list-inside space-y-1">
                {trial.eligibility.slice(0, 5).map((criteria, index) => (
                  <li key={index} className="text-sm text-gray-600">
                    {criteria}
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <h4 className="text-sm font-semibold text-gray-900 mb-2">Trial Information</h4>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span className="text-gray-500">Phase:</span>
                  <span className="ml-2 text-gray-900">{trial.phase}</span>
                </div>
                <div>
                  <span className="text-gray-500">Status:</span>
                  <span className="ml-2 text-gray-900">{trial.status}</span>
                </div>
              </div>
            </div>

            <div>
              <h4 className="text-sm font-semibold text-gray-900 mb-2">Contact Information</h4>
              <div className="space-y-2">
                <div className="flex items-center text-gray-600">
                  <Phone className="w-4 h-4 mr-2" />
                  <a href={`tel:${trial.contact.phone}`} className="text-sm hover:text-primary-blue">
                    {trial.contact.phone}
                  </a>
                </div>
                <div className="flex items-center text-gray-600">
                  <Mail className="w-4 h-4 mr-2" />
                  <a href={`mailto:${trial.contact.email}`} className="text-sm hover:text-primary-blue">
                    {trial.contact.email}
                  </a>
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="flex gap-3 pt-2">
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex-1 py-2 px-4 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-blue focus:ring-offset-2 transition-colors"
          >
            {expanded ? 'Show Less' : 'View Details'}
          </button>

          <a
            href={`mailto:${trial.contact.email}?subject=Inquiry about ${trial.nctId}`}
            className="flex-1 py-2 px-4 bg-primary-blue text-white text-sm font-medium rounded-lg text-center hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-primary-blue focus:ring-offset-2 transition-colors"
          >
            Contact Coordinator
          </a>

          {!isSaved && onSave && (
            <button
              onClick={onSave}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-blue focus:ring-offset-2 transition-colors"
              aria-label="Save trial"
            >
              <Bookmark className="w-4 h-4 text-gray-600" />
            </button>
          )}

          {isSaved && onRemove && (
            <button
              onClick={onRemove}
              className="px-4 py-2 border border-primary-blue bg-primary-blue bg-opacity-10 rounded-lg hover:bg-opacity-20 focus:outline-none focus:ring-2 focus:ring-primary-blue focus:ring-offset-2 transition-colors"
              aria-label="Remove saved trial"
            >
              <BookmarkCheck className="w-4 h-4 text-primary-blue" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
