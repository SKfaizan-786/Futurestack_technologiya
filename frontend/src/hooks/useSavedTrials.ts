import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { savedTrialsService, type SavedTrial } from '../services/savedTrials';
import type { TrialMatch } from '../types';

export function useSavedTrials() {
  const queryClient = useQueryClient();

  // Get saved trials
  const { data: savedTrials, isLoading } = useQuery({
    queryKey: ['savedTrials'],
    queryFn: async () => {
      return savedTrialsService.getSavedTrials();
    },
  });

  // Save trial
  const saveTrial = useMutation({
    mutationFn: async ({ trial, notes }: { trial: TrialMatch; notes?: string }) => {
      return savedTrialsService.saveTrial({
        trial_id: trial.nctId,
        trial_data: trial,
        notes,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['savedTrials'] });
    },
  });

  // Remove saved trial
  const removeTrial = useMutation({
    mutationFn: async (trialId: string) => {
      return savedTrialsService.removeTrial(trialId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['savedTrials'] });
    },
  });

  // Update notes
  const updateNotes = useMutation({
    mutationFn: async ({ trialId, notes }: { trialId: string; notes: string }) => {
      return savedTrialsService.updateNotes(trialId, { notes });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['savedTrials'] });
    },
  });

  return {
    savedTrials: savedTrials || [],
    isLoading,
    saveTrial: saveTrial.mutateAsync,
    removeTrial: removeTrial.mutateAsync,
    updateNotes: updateNotes.mutateAsync,
  };
}
