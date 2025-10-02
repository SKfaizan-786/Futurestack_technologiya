// User and Authentication Types
export interface User {
  id: string;
  email: string;
  full_name?: string;
  role: 'patient' | 'caregiver' | 'healthcare_provider';
  created_at: Date;
}

export interface UserProfile {
  id: string;
  full_name: string;
  role: 'patient' | 'caregiver' | 'healthcare_provider';
  created_at: Date;
}

// Patient Data Types
export interface PatientData {
  age: number;
  gender: 'male' | 'female' | 'other';
  location: {
    city: string;
    state: string;
    zipCode: string;
  };
  diagnosis: {
    cancerType: string;
    stage: '1' | '2' | '3' | '4';
    subtype?: string;
  };
  biomarkers?: {
    egfr?: boolean;
    alk?: boolean;
    pdl1?: boolean;
    custom?: string[];
  };
  treatments: {
    current: Medication[];
    previous: Medication[];
    response?: 'complete' | 'partial' | 'stable' | 'progressive';
  };
  allergies?: string[];
  comorbidities?: string[];
}

export interface Medication {
  name: string;
  dosage?: string;
  startDate?: Date;
  endDate?: Date;
}

// Trial Types
export interface TrialMatch {
  id: string;
  nctId: string;
  title: string;
  matchScore: number; // 0-100
  location: {
    facility: string;
    city: string;
    state: string;
    distance: number;
  };
  explanation: string; // AI-generated plain language
  contact: {
    name: string;
    phone: string;
    email: string;
  };
  eligibility: string[];
  phase: string;
  status: string;
  conditions: string[];
}

// Search History
export interface SearchHistory {
  id: string;
  user_id: string;
  patient_data: PatientData;
  search_results: TrialMatch[];
  created_at: Date;
}

// Saved Trials
export interface SavedTrial {
  id: string;
  user_id: string;
  trial_id: string;
  trial_data: TrialMatch;
  notes?: string;
  created_at: Date;
}

// API Response Types
export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

export interface MatchResponse {
  matches: TrialMatch[];
  total: number;
  query_id: string;
}
