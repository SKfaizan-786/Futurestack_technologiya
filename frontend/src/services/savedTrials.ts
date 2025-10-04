import { apiClient } from './api';
import { authService } from './auth';
import type { TrialMatch } from '../types';

export interface SavedTrial {
  id: string;
  user_id: string;
  trial_id: string;
  trial_data: TrialMatch;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface SaveTrialRequest {
  trial_id: string;
  trial_data: TrialMatch;
  notes?: string;
}

export interface UpdateNotesRequest {
  notes: string;
}

export const savedTrialsService = {
  async getSavedTrials(): Promise<SavedTrial[]> {
    const session = await authService.getSession();
    const token = session?.access_token;
    return apiClient.getSavedTrials(token);
  },

  async saveTrial(request: SaveTrialRequest): Promise<{ message: string; trial_id: string; saved_id: string }> {
    const session = await authService.getSession();
    const token = session?.access_token;
    return apiClient.saveTrial(request, token);
  },

  async removeTrial(trialId: string): Promise<{ message: string }> {
    const session = await authService.getSession();
    const token = session?.access_token;
    return apiClient.removeTrial(trialId, token);
  },

  async updateNotes(trialId: string, request: UpdateNotesRequest): Promise<{ message: string }> {
    const session = await authService.getSession();
    const token = session?.access_token;
    return apiClient.updateTrialNotes(trialId, request.notes, token);
  },
};