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
    // Transform frontend PatientData to backend format
    const transformedPatientData = this.transformPatientData(patientData);
    
    return this.request<MatchResponse>('/api/v1/match', {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: JSON.stringify({
        patient_data: transformedPatientData,
        max_results: 3,
        min_confidence: 0.5,
        enable_advanced_reasoning: true
      }),
    });
  }

  // Transform frontend PatientData format to backend format
  private transformPatientData(frontendData: any): any {
    // If this looks like natural language data, return as-is
    if (frontendData.medical_query || frontendData.clinical_notes) {
      return frontendData;
    }

    // Transform structured frontend data to backend format
    const transformed: any = {};

    // Map demographics
    if (frontendData.age || frontendData.gender || frontendData.location) {
      transformed.demographics = {};
      if (frontendData.age) transformed.demographics.age = frontendData.age;
      if (frontendData.gender) transformed.demographics.gender = frontendData.gender;
      if (frontendData.location) {
        transformed.demographics.location = frontendData.location;
      }
    }

    // Map medical history from diagnosis and other medical info
    if (frontendData.diagnosis || frontendData.comorbidities || frontendData.biomarkers) {
      transformed.medical_history = {};
      if (frontendData.diagnosis) {
        transformed.medical_history.diagnosis = frontendData.diagnosis;
      }
      if (frontendData.biomarkers) {
        transformed.medical_history.biomarkers = frontendData.biomarkers;
      }
      if (frontendData.comorbidities) {
        transformed.medical_history.comorbidities = frontendData.comorbidities;
      }
    }

    // Map current medications
    if (frontendData.treatments?.current) {
      transformed.current_medications = frontendData.treatments.current.map((med: any) => 
        typeof med === 'string' ? med : med.name
      );
    }

    // Map allergies
    if (frontendData.allergies) {
      transformed.allergies = frontendData.allergies;
    }

    // Add treatment history to medical history
    if (frontendData.treatments) {
      if (!transformed.medical_history) {
        transformed.medical_history = {};
      }
      transformed.medical_history.treatment_history = {
        current: frontendData.treatments.current,
        previous: frontendData.treatments.previous,
        response: frontendData.treatments.response
      };
    }

    return transformed;
  }

  // Process natural language input - convert to backend format
  async processNaturalLanguage(text: string, token?: string) {
    // Create backend-compatible patient data object from natural language
    const patientData = {
      medical_query: text,  // Backend expects this field name
      clinical_notes: text, // Also add as clinical notes for validation
      age: null,
      gender: null,
      location: {},
      diagnosis: {},
      treatments: { current: [], previous: [] },
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

  // Saved trials methods
  async getSavedTrials(token?: string): Promise<any[]> {
    return this.request('/api/v1/saved-trials', {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
  }

  async saveTrial(trialData: any, token?: string): Promise<{ message: string; trial_id: string; saved_id: string }> {
    return this.request('/api/v1/saved-trials', {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: JSON.stringify(trialData),
    });
  }

  async removeTrial(trialId: string, token?: string): Promise<{ message: string }> {
    return this.request(`/api/v1/saved-trials/${trialId}`, {
      method: 'DELETE',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
  }

  async updateTrialNotes(trialId: string, notes: string, token?: string): Promise<{ message: string }> {
    return this.request(`/api/v1/saved-trials/${trialId}/notes`, {
      method: 'PUT',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: JSON.stringify({ notes }),
    });
  }
}

export const apiClient = new ApiClient(API_URL);
