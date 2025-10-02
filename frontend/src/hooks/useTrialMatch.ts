import { useMutation, useQuery } from '@tanstack/react-query';
import { apiClient } from '../services/api';
import { supabase } from '../services/supabase';
import type { PatientData, TrialMatch, SearchHistory } from '../types';

export function useTrialMatch() {
  // Match trials mutation
  const matchMutation = useMutation({
    mutationFn: async (patientData: PatientData) => {
      const { data: { session } } = await supabase.auth.getSession();
      const token = session?.access_token;
      return apiClient.matchTrials(patientData, token);
    },
  });

  // Process natural language mutation
  const processNaturalLanguage = useMutation({
    mutationFn: async (text: string) => {
      const { data: { session } } = await supabase.auth.getSession();
      const token = session?.access_token;
      return apiClient.processNaturalLanguage(text, token);
    },
  });

  // Save search to history
  const saveSearch = async (patientData: PatientData, results: TrialMatch[]) => {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) throw new Error('User not authenticated');

    const { error } = await supabase
      .from('search_history')
      .insert({
        user_id: user.id,
        patient_data: patientData,
        search_results: results,
      });

    if (error) throw error;
  };

  // Get search history
  const { data: searchHistory, refetch: refetchHistory } = useQuery({
    queryKey: ['searchHistory'],
    queryFn: async () => {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return [];

      const { data, error } = await supabase
        .from('search_history')
        .select('*')
        .eq('user_id', user.id)
        .order('created_at', { ascending: false });

      if (error) throw error;
      return data as SearchHistory[];
    },
  });

  return {
    matchTrials: matchMutation.mutateAsync,
    isMatching: matchMutation.isPending,
    matchError: matchMutation.error,
    processNaturalLanguage: processNaturalLanguage.mutateAsync,
    isProcessing: processNaturalLanguage.isPending,
    saveSearch,
    searchHistory: searchHistory || [],
    refetchHistory,
  };
}
