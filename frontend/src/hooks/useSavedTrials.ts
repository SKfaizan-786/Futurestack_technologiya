import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { supabase } from '../services/supabase';
import type { SavedTrial, TrialMatch } from '../types';

export function useSavedTrials() {
  const queryClient = useQueryClient();

  // Get saved trials
  const { data: savedTrials, isLoading } = useQuery({
    queryKey: ['savedTrials'],
    queryFn: async () => {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return [];

      const { data, error } = await supabase
        .from('saved_trials')
        .select('*')
        .eq('user_id', user.id)
        .order('created_at', { ascending: false });

      if (error) throw error;
      return data as SavedTrial[];
    },
  });

  // Save trial
  const saveTrial = useMutation({
    mutationFn: async ({ trial, notes }: { trial: TrialMatch; notes?: string }) => {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error('User not authenticated');

      const { error } = await supabase
        .from('saved_trials')
        .insert({
          user_id: user.id,
          trial_id: trial.nctId,
          trial_data: trial,
          notes,
        });

      if (error) throw error;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['savedTrials'] });
    },
  });

  // Remove saved trial
  const removeTrial = useMutation({
    mutationFn: async (trialId: string) => {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error('User not authenticated');

      const { error } = await supabase
        .from('saved_trials')
        .delete()
        .eq('user_id', user.id)
        .eq('trial_id', trialId);

      if (error) throw error;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['savedTrials'] });
    },
  });

  // Update notes
  const updateNotes = useMutation({
    mutationFn: async ({ trialId, notes }: { trialId: string; notes: string }) => {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error('User not authenticated');

      const { error } = await supabase
        .from('saved_trials')
        .update({ notes })
        .eq('user_id', user.id)
        .eq('trial_id', trialId);

      if (error) throw error;
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
