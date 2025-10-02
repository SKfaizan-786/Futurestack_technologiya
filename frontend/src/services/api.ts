import type { PatientData, MatchResponse } from '../types';

/// <reference types="vite/client" />

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiClient {
  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;

    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Unknown error' }));
      throw new Error(error.message || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  // Health check
  async healthCheck() {
    return this.request<{ status: string }>('/api/v1/health');
  }

  // Match trials
  async matchTrials(patientData: any, token?: string) {
    return this.request<MatchResponse>('/api/v1/match', {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: JSON.stringify({
        patient_data: patientData,
        max_results: 3,
        min_confidence: 0.7,
        enable_advanced_reasoning: true
      }),
    });
  }

  // Process natural language input - convert to backend PatientData format
  async processNaturalLanguage(text: string, token?: string) {
    // Create backend-compatible patient data object from natural language
    const patientData = {
      medical_history: text,
      demographics: {},
      // Add any additional fields the backend expects
    };
    return Promise.resolve(patientData);
  }

  // Get trial details
  async getTrialDetails(nctId: string, token?: string) {
    return this.request(`/api/v1/trials/${nctId}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
  }
}

export const apiClient = new ApiClient(API_URL);
