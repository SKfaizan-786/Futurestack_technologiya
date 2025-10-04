import { useState } from 'react';
import { TrialCard } from './TrialCard';
import type { TrialMatch } from '../../types';

interface TrialListProps {
  trials: TrialMatch[];
  savedTrialIds?: string[];
  onSave?: (trial: TrialMatch) => void;
  onRemove?: (trialId: string) => void;
}

export function TrialList({ trials, savedTrialIds = [], onSave, onRemove }: TrialListProps) {
  const [sortBy, setSortBy] = useState<'match' | 'distance'>('match');

  // Defensive check for trial data
  const validTrials = trials.filter(trial => 
    trial && 
    typeof trial === 'object' && 
    trial.matchScore !== undefined && 
    trial.location !== undefined &&
    trial.location.distance !== undefined
  );

  const sortedTrials = [...validTrials].sort((a, b) => {
    if (sortBy === 'match') {
      return (b.matchScore || 0) - (a.matchScore || 0);
    }
    return (a.location?.distance || 0) - (b.location?.distance || 0);
  });

  if (validTrials.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">No trials found matching your criteria.</p>
        <p className="text-sm text-gray-400 mt-2">Try adjusting your search parameters.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <p className="text-sm text-gray-600">
          Found <span className="font-semibold text-gray-900">{validTrials.length}</span> matching trials
        </p>
        <div className="flex items-center space-x-2">
          <label htmlFor="sort" className="text-sm text-gray-600">
            Sort by:
          </label>
          <select
            id="sort"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as 'match' | 'distance')}
            className="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-blue focus:border-transparent"
          >
            <option value="match">Best Match</option>
            <option value="distance">Nearest Location</option>
          </select>
        </div>
      </div>

      <div className="space-y-4">
        {sortedTrials.map((trial) => (
          <TrialCard
            key={trial.id}
            trial={trial}
            isSaved={savedTrialIds.includes(trial.nctId)}
            onSave={() => onSave?.(trial)}
            onRemove={() => onRemove?.(trial.nctId)}
          />
        ))}
      </div>
    </div>
  );
}
