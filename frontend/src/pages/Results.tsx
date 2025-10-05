import { useLocation, useNavigate } from 'react-router-dom';
import { useSavedTrials } from '../hooks/useSavedTrials';
import type { TrialMatch, PatientData } from '../types';
import { CheckCircle, User, MapPin, Calendar, Clock, FileText, Bell, BookOpen, Download, Search, Phone, Mail } from 'lucide-react';
import { useState } from 'react';

interface TrialCardProps {
  trial: TrialMatch;
  index: number;
  getBadgeText: (score: number) => string;
  getMatchColor: (score: number) => string;
  formatExplanation: (text: string) => React.ReactNode[];
  onSave: () => void;
  isSaved: boolean;
}

function TrialCard({ trial, index, getBadgeText, getMatchColor, formatExplanation, onSave, isSaved }: TrialCardProps) {
  const [expanded, setExpanded] = useState(false);

  // Generate mock institution name
  const institutions = [
    'Johns Hopkins University',
    'Mayo Clinic',
    'MD Anderson Cancer Center',
    'Memorial Sloan Kettering',
    'Dana-Farber Cancer Institute',
    'Cleveland Clinic',
    'Stanford University Medical Center',
    'University of Pennsylvania'
  ];
  
  const institutionName = institutions[index % institutions.length];

  // Generate mock detailed data
  const eligibilityCriteria = [
    'Histologically or cytologically confirmed diagnosis',
    'Age 18 years or older',
    'ECOG performance status 0-2',
    'Adequate hematologic function',
    'Adequate hepatic function',
    'Life expectancy of at least 12 weeks',
    'Signed informed consent'
  ];

  const contactPhone = '(713) 555-9442';
  const contactEmail = `trials.nct${trial.nctId}@clinicalcenter.org`;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-start gap-4">
        {/* Number badge */}
        <div className="flex-shrink-0">
          <div className="w-8 h-8 bg-[#1e68d1] text-white rounded-full flex items-center justify-center font-bold text-lg">
            {index + 1}
          </div>
          
        </div>
        
        <div className="flex-1">
          {/* Trial header */}
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <h3 className="text-xl font-bold text-gray-900 mb-2">{trial.title}</h3>
              <div className="flex items-center gap-4 text-sm text-gray-600">
                <span>NCT{trial.nctId}</span>
                <span>•</span>
                <span>{trial.phase}</span>
                <span>•</span>
                <span>{institutionName}</span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className={`${getBadgeText(trial.matchScore) === 'Excellent Match' ? 'bg-green-100 text-green-800' : getBadgeText(trial.matchScore) === 'Good Match' ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'} px-3 py-1 rounded-full text-sm font-medium`}>
                {getBadgeText(trial.matchScore)}
              </span>
            </div>
          </div>

          {/* Match confidence */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">Match Confidence</span>
              <span className="text-sm font-bold text-gray-900">{trial.matchScore}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className={`h-2 rounded-full ${getMatchColor(trial.matchScore)}`}
                style={{ width: `${trial.matchScore}%` }}
              ></div>
            </div>
          </div>

          {/* Why this trial matches */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <h4 className="font-semibold text-gray-900 mb-2">Why this trial:</h4>
            <div className="text-sm text-gray-700 leading-relaxed">
              {formatExplanation(trial.explanation)}
            </div>
          </div>

          {/* Expanded details */}
          {expanded && (
            <div className="mb-6 p-6 border border-gray-200 rounded-lg bg-gray-50">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                {/* Eligibility Criteria */}
                <div>
                  <h4 className="text-lg font-semibold text-gray-900 mb-4">Eligibility Criteria</h4>
                  <ul className="space-y-2">
                    {eligibilityCriteria.map((criteria, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-sm text-gray-700">
                        <span className="text-green-500 mt-1 text-xs">•</span>
                        <span>{criteria}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Trial Information */}
                <div>
                  <h4 className="text-lg font-semibold text-gray-900 mb-4">Trial Information</h4>
                  <div className="space-y-2 text-sm">
                    <div>
                      <span className="text-gray-600">Phase: </span>
                      <span className="font-medium text-gray-900">{trial.phase}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Status: </span>
                      <span className="font-medium text-gray-900">{trial.status || 'RECRUITING'}</span>
                    </div>
                  </div>
                </div>

                {/* Contact Information */}
                <div>
                  <h4 className="text-lg font-semibold text-gray-900 mb-4">Contact Information</h4>
                  <div className="space-y-3">
                    <div className="flex items-center gap-2 text-sm">
                      <Phone className="w-4 h-4 text-gray-400 flex-shrink-0" />
                      <a href={`tel:${contactPhone}`} className="text-blue-600 hover:text-blue-800">
                        {contactPhone}
                      </a>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <Mail className="w-4 h-4 text-gray-400 flex-shrink-0" />
                      <a href={`mailto:${contactEmail}`} className="text-blue-600 hover:text-blue-800 break-all">
                        {contactEmail}
                      </a>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Action buttons */}
          <div className="flex gap-3">
            <button 
              onClick={() => setExpanded(!expanded)}
              className="flex-1 bg-gradient-to-r from-blue-600 to-cyan-500 text-white px-4 py-1 rounded-lg hover:from-blue-700 hover:to-cyan-600 transition-all duration-200 flex items-center justify-center"
            >
              {expanded ? 'Hide Details' : 'View Full Details'}
            </button>
            <button 
              onClick={onSave}
              // Conditional styling based on isSaved
              className={`px-4 py-1 border rounded-lg transition-colors flex items-center justify-center ${
                isSaved 
                  ? 'border-green-300 bg-green-50 text-green-700 cursor-default' 
                  : 'border-gray-300 hover:bg-gray-50'
              }`}
              // Disable button if already saved
              disabled={isSaved} 
            >
              <span className="flex items-center">
                <BookOpen className="w-4 h-4 mr-2" />
                {/* Conditional text based on isSaved */}
                {isSaved ? 'Saved Trial' : 'Save Trial'} 
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export function Results() {
  const location = useLocation();
  const navigate = useNavigate();
  const { savedTrials, saveTrial, removeTrial } = useSavedTrials();
  const [trialSaveStates, setTrialSaveStates] = useState<{[key: string]: boolean}>({});

  const trials = (location.state?.trials as TrialMatch[]) || [];
  const patientData = location.state?.patientData as PatientData;
  const originalQuery = location.state?.originalQuery as string;

  // Extract meaningful data from the query or patient data
  const extractProfileData = () => {
    const query = originalQuery || '';
    
    // Extract age
    const ageMatch = query.match(/(\d+)\s*year(?:s)?\s*old/i) || 
                       query.match(/age[:\s]*(\d+)/i);
    const age = ageMatch ? ageMatch[1] : (patientData?.age ? patientData.age.toString() : null);
    
    // Extract gender  
    const genderMatch = query.match(/\b(male|female|man|woman)\b/i);
    const gender = genderMatch ? genderMatch[1].toLowerCase() : (patientData?.gender || null);
    
    // Extract main cancer type (simplified and properly capitalized)
    let cancerType = patientData?.diagnosis?.cancerType || '';
    if (query) {
      // Look for common cancer patterns
      const cancerPatterns = [
        /\b(lung|breast|colon|colorectal|prostate|pancreatic|liver|kidney|brain|ovarian|cervical|skin|melanoma|leukemia|lymphoma)\s*cancer/i,
        /\b(sarcoma|carcinoma|adenocarcinoma|squamous cell|basal cell)/i,
        /\bnon[\-\s]?small\s*cell\s*lung\s*cancer/i,
        /\bsmall\s*cell\s*lung\s*cancer/i
      ];
      
      for (const pattern of cancerPatterns) {
        const match = query.match(pattern);
        if (match) {
          // Properly capitalize the cancer type
          cancerType = match[0].toLowerCase()
            .split(' ')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
          break;
        }
      }
      
      // If no specific cancer found, try broader terms
      if (!cancerType) {
        const broadMatch = query.match(/\b(cancer|tumor|carcinoma|sarcoma|lymphoma|leukemia|melanoma)\b/i);
        if (broadMatch) {
          cancerType = broadMatch[0].charAt(0).toUpperCase() + broadMatch[0].slice(1).toLowerCase() + ' (unspecified)';
        }
      }
    }
    
    // Extract location with better patterns
    let location = '';
    if (patientData?.location?.city && patientData?.location?.state && 
        patientData.location.city !== 'Unknown' && patientData.location.state !== 'Unknown') {
      location = `${patientData.location.city}, ${patientData.location.state}`;
    } else if (query) {
      // Look for city patterns in query with better regex
      const cityPatterns = [
        /\blives\s+in\s+([A-Za-z\s]+?)\s+([A-Z]{2})\b/i,  // "lives in Boston MA"
        /\bin\s+([A-Za-z\s]+?)\s+([A-Z]{2})\b/i,          // "in Boston MA"
        /\b([A-Za-z]+),\s*([A-Z]{2})\b/,                 // "Boston, MA"
        /\blives\s+in\s+([A-Za-z\s]+)/i,                  // "lives in Boston"
        /\bfrom\s+([A-Za-z\s]+?)\s+([A-Z]{2})\b/i,        // "from Boston MA"
      ];
      
      for (const pattern of cityPatterns) {
        const match = query.match(pattern);
        if (match) {
          if (match[2]) {
            // Has state abbreviation
            location = `${match[1].trim()}, ${match[2]}`;
          } else {
            // Just city
            location = match[1].trim();
          }
          break;
        }
      }
      
      // If still no location found, try simpler patterns
      if (!location) {
        const simpleLocationMatch = query.match(/\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(MA|NY|CA|FL|TX|IL|PA|OH|GA|NC|MI|NJ|VA|WA|AZ|IN|TN|MO|MD|WI|MN|CO|AL|SC|LA|KY|OR|OK|CT|IA|MS|AR|KS|UT|NV|NM|WV|NE|ID|HI|NH|ME|MT|RI|DE|SD|ND|AK|VT|WY|DC)\b/);
        if (simpleLocationMatch) {
          location = `${simpleLocationMatch[1]}, ${simpleLocationMatch[2]}`;
        }
      }
    }
    
    // Extract stage
    const stage = patientData?.diagnosis?.stage || 
                  (query.match(/stage\s*(\d+|I{1,4}|IV)/i)?.[1]) || null;
    
    return {
      age,
      gender,
      cancerType: cancerType || 'Not specified',
      stage,
      location: location || 'Not specified'
    };
  };

  const profileData = extractProfileData();

  // Debug logging
  console.log('Results component - trials:', trials);
  console.log('Results component - patientData:', patientData);

  if (!trials || trials.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600 mb-4">No results to display.</p>
          <button
            onClick={() => navigate('/search')}
            className="px-6 py-2 bg-[#1e68d1] text-white font-medium rounded-lg hover:bg-blue-600 transition-colors"
          >
            Start New Search
          </button>
        </div>
        
      </div>
    );
  }

  const formatExplanation = (explanation: string) => {
    // Split into paragraphs and format headings
    const sections = explanation.split('**');
    const formatted = [];
    
    for (let i = 0; i < sections.length; i++) {
      if (i % 2 === 1) {
        // This is a heading
        formatted.push(<strong key={i} className="font-bold text-gray-900">{sections[i]}</strong>);
      } else {
        // This is regular text
        const text = sections[i];
        if (text.trim()) {
          formatted.push(<span key={i}>{text}</span>);
        }
      }
    }
    
    return formatted;
  };

  const generatePDF = () => {
    // Create PDF content
    const content = `
      Clinical Trial Match Results
      Generated on ${new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
      
      Patient Profile:
      - Age: ${profileData.age ? `${profileData.age} years` : 'Not specified'}
      - Diagnosis: ${profileData.cancerType}
      - Stage: ${profileData.stage ? `Stage ${profileData.stage}` : 'Not specified'}
      - Location: ${profileData.location}
      
      Matching Trials (${trials.length} found):
      
      ${trials.map((trial, index) => `
      ${index + 1}. ${trial.title}
      NCT${trial.nctId} | ${trial.phase}
      Match Score: ${trial.matchScore}%
      
      Why this trial matches:
      ${trial.explanation.replace(/\*\*/g, '')}
      
      `).join('\n')}
    `;

    // Create blob and download
    const blob = new Blob([content], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `clinical-trial-results-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header Section */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="text-center">
            <div className="flex justify-center mb-6">
              <CheckCircle className="w-16 h-16 text-green-500" />
              
            </div>
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              We Found {trials.length} Matching Clinical Trial{trials.length > 1 ? 's' : ''}
            </h1>
            <p className="text-gray-600 text-lg mb-6">
              Based on your medical profile, here are the top trials you may be<br />
              eligible for.
            </p>
            
            {/* Statistics Box */}
            <div className="inline-flex items-center bg-gray-50 border border-gray-200 rounded-lg px-6 py-3 space-x-6 text-sm text-gray-600">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4" />
                <span>{trials.length} trials analyzed</span>
              </div>
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4" />
                <span>Matched in 124.7ms</span>
              </div>
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4" />
                <span>Generated on {new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-none mx-auto px-[10%] py-8">
        {/* Your Profile Section */}
        <div className="bg-gradient-to-r from-blue-50 to-blue-50 border border-blue-100 rounded-lg shadow-sm p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-6">Your Profile</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                <User className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Age</p>
                <p className="font-medium text-gray-900">
                  {profileData.age ? `${profileData.age} years` : 'Not specified'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center flex-shrink-0">
                <FileText className="w-5 h-5 text-red-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Diagnosis</p>
                <p className="font-medium text-gray-900 text-sm">
                  {profileData.cancerType}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-yellow-100 rounded-full flex items-center justify-center flex-shrink-0">
                <Calendar className="w-5 h-5 text-yellow-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Stage</p>
                <p className="font-medium text-gray-900">
                  {profileData.stage ? `Stage ${profileData.stage}` : 'Not specified'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0">
                <MapPin className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Location</p>
                <p className="font-medium text-gray-900 text-sm">
                  {profileData.location}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Trial Results */}
        <div className="space-y-6 mb-12">
          {trials.map((trial, index) => {
            const getMatchColor = (score: number) => {
              if (score >= 90) return 'bg-green-500';
              if (score >= 80) return 'bg-green-400';
              if (score >= 70) return 'bg-yellow-400';
              return 'bg-gray-400';
            };

            const getBadgeText = (score: number) => {
              if (score >= 90) return 'Excellent Match';
              if (score >= 80) return 'Good Match';
              return 'Potential Match';
            };

            const isSaved = trialSaveStates[trial.id] || false;

            return (
              <TrialCard
                key={trial.id}
                trial={trial}
                index={index}
                getBadgeText={getBadgeText}
                getMatchColor={getMatchColor}
                formatExplanation={formatExplanation}
                isSaved={isSaved}
                onSave={async () => {
                  // NEW LOGIC: Check if already saved
                  if (isSaved) {
                    alert('This trial is already saved!');
                    return;
                  }

                  // Proceed with saving if not saved
                  try {
                    await saveTrial({ trial });
                    setTrialSaveStates(prev => ({ ...prev, [trial.id]: true }));
                    alert('Trial saved successfully!');
                  } catch (error) {
                    alert('Failed to save trial. Please try again.');
                  }
                }}
              />
            );
          })}
        </div>

        {/* Action buttons - FINAL FIX applied here */}
        {/* Action buttons - FINAL FIX for Horizontal Alignment (Side-by-Side) */}
        <div className="flex justify-center gap-4 mb-12">
          <button 
            onClick={generatePDF}
            className="flex items-center justify-center px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <span className="flex items-center gap-2 whitespace-nowrap">
              <Download className="w-4 h-4" />
              Export Results to PDF
            </span>
          </button>
          <button 
            onClick={() => navigate('/search')}
            className="flex items-center justify-center px-6 py-3 bg-[#1e68d1] text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            <span className="flex items-center gap-2 whitespace-nowrap">
              <Search className="w-4 h-4" />
              Try Another Search
            </span>
          </button>
        </div>

        {/* What's Next Section */}
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-12">What's Next?</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <FileText className="w-8 h-8 text-blue-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Contact Trial Sites</h3>
              <p className="text-gray-600 text-sm mb-4">
                Reach out to the trial coordinators to discuss enrollment and next steps.
              </p>
              <button className="text-blue-600 text-sm font-medium hover:text-blue-700">View Contact Info</button>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Bell className="w-8 h-8 text-green-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Get Trial Alerts</h3>
              <p className="text-gray-600 text-sm mb-4">
                Receive notifications when new trials matching your profile become available.
              </p>
              <button className="text-green-600 text-sm font-medium hover:text-green-700">Set Up Alerts</button>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <BookOpen className="w-8 h-8 text-purple-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Learn About Trials</h3>
              <p className="text-gray-600 text-sm mb-4">
                Understand what to expect during a clinical trial and your rights as a participant.
              </p>
              <button className="text-purple-600 text-sm font-medium hover:text-purple-700">View Resources</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}