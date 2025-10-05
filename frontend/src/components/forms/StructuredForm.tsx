import { useState, useEffect, useRef } from 'react';
import { useForm, FormProvider, useFormContext } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import type { PatientData } from '../../types';

const structuredFormSchema = z.object({
  age: z.number().min(1).max(150),
  gender: z.enum(['male', 'female', 'other']),
  city: z.string().min(1, 'City is required'),
  state: z.string().min(2, 'State code is required').max(50, 'State name too long'),
  zipCode: z.string().min(5).max(10),
  cancerType: z.string().min(1, 'Cancer type is required'),
  stage: z.enum(['1', '2', '3', '4']),
  subtype: z.string().optional(),
  egfr: z.boolean().optional(),
  alk: z.boolean().optional(),
  pdl1: z.boolean().optional(),
  currentMedications: z.string().optional(),
  previousMedications: z.string().optional(),
  treatmentResponse: z.enum(['complete', 'partial', 'stable', 'progressive']).optional(),
  allergies: z.string().optional(),
  comorbidities: z.string().optional(),
});

type StructuredFormData = z.infer<typeof structuredFormSchema>;

interface StructuredFormProps {
  onSubmit: (data: PatientData) => Promise<void>;
  isProcessing: boolean;
}

const stepFields: (keyof StructuredFormData)[][] = [
  ['age', 'gender'], // Step 0
  ['city', 'state', 'zipCode', 'cancerType', 'stage'], // Step 1
  ['currentMedications', 'previousMedications', 'treatmentResponse', 'egfr', 'alk', 'pdl1'], // Step 2
  ['allergies', 'comorbidities'], // Step 3
];

const StepContent: React.FC<{ step: number; stepFields: (keyof StructuredFormData)[][] }> = ({ step, stepFields }) => {
  const { register, watch, setValue, formState: { errors } } = useFormContext<StructuredFormData>();
  const [dropdownStates, setDropdownStates] = useState({
    gender: false,
    stage: false,
    treatmentResponse: false
  });
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownStates({
          gender: false,
          stage: false,
          treatmentResponse: false
        });
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const toggleDropdown = (field: keyof typeof dropdownStates) => {
    setDropdownStates(prev => ({
      ...prev,
      [field]: !prev[field]
    }));
  };

  const selectOption = (field: keyof StructuredFormData, value: string) => {
    setValue(field, value);
    setDropdownStates(prev => ({
      ...prev,
      [field]: false
    }));
  };

  // Clear function to ensure no cross-step contamination
  const getCurrentStepValue = (fieldName: keyof StructuredFormData) => {
    const currentStepFields = stepFields[step];
    if (currentStepFields.includes(fieldName)) {
      return watch(fieldName);
    }
    return '';
  };

  // Effect to clear focus and reset any potential cross-step issues
  useEffect(() => {
    // Reset any focused elements when step changes
    const activeElement = document.activeElement as HTMLElement;
    if (activeElement) {
      activeElement.blur();
    }
  }, [step]);

  const renderStep = (currentStep: number) => {
    switch (currentStep) {
      case 0:
        return (
          <div className="bg-white rounded-lg shadow-md border border-gray-200 p-8">
            <h4 className="text-2xl font-bold text-gray-900 mb-8">Personal Info</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label htmlFor="age" className="block text-sm font-semibold text-gray-700 mb-2">
                  Age <span className="text-red-500">*</span>
                </label>
                <input
                  id="age"
                  type="number"
                  placeholder="Enter age (e.g., 45)"
                  value={watch('age') || ''}
                  onChange={(e) => {
                    const value = e.target.value ? parseInt(e.target.value) : undefined;
                    setValue('age', value as any);
                  }}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#1e68d1] focus:border-transparent shadow-sm transition-all"
                />
                {errors.age && <p className="mt-2 text-sm text-red-600">{errors.age.message}</p>}
              </div>
              <div>
                <label htmlFor="gender" className="block text-sm font-semibold text-gray-700 mb-2">
                  Gender <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <button
                    type="button"
                    onClick={() => toggleDropdown('gender')}
                    className="w-full text-white bg-[#1e68d1] hover:bg-[#1757b8] focus:ring-4 focus:outline-none focus:ring-blue-300 font-medium rounded-lg text-sm px-5 py-2.5 text-center inline-flex items-center justify-between"
                  >
                    {watch('gender') ? (watch('gender') === 'male' ? 'Male' : watch('gender') === 'female' ? 'Female' : 'Other') : 'Select gender'}
                    <svg className={`w-2.5 h-2.5 ml-2 transition-transform ${dropdownStates.gender ? 'rotate-180' : ''}`} aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 10 6">
                      <path stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="m1 1 4 4 4-4"/>
                    </svg>
                  </button>
                  {dropdownStates.gender && (
                    <div className="absolute top-full mt-2 z-10 w-full bg-white divide-y divide-gray-100 rounded-lg shadow border">
                      <ul className="py-2 text-sm text-gray-700">
                        <li>
                          <button
                            type="button"
                            onClick={() => selectOption('gender', 'male')}
                            className="w-full text-left px-4 py-2 hover:bg-gray-100"
                          >
                            Male
                          </button>
                        </li>
                        <li>
                          <button
                            type="button"
                            onClick={() => selectOption('gender', 'female')}
                            className="w-full text-left px-4 py-2 hover:bg-gray-100"
                          >
                            Female
                          </button>
                        </li>
                        <li>
                          <button
                            type="button"
                            onClick={() => selectOption('gender', 'other')}
                            className="w-full text-left px-4 py-2 hover:bg-gray-100"
                          >
                            Other
                          </button>
                        </li>
                      </ul>
                    </div>
                  )}
                </div>
                {errors.gender && <p className="mt-2 text-sm text-red-600">{errors.gender.message}</p>}
              </div>
            </div>
          </div>
        );

      case 1:
        return (
          <div className="bg-white rounded-lg shadow-md border border-gray-200 p-8">
            <h4 className="text-2xl font-bold text-gray-900 mb-8">Location & Diagnosis</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <label htmlFor="city" className="block text-sm font-semibold text-gray-700 mb-2">
                  City <span className="text-red-500">*</span>
                </label>
                <input 
                  id="city" 
                  type="text" 
                  placeholder="Enter your city (e.g., Boston)"
                  value={watch('city') || ''}
                  onChange={(e) => setValue('city', e.target.value.trim())}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#1e68d1] focus:border-transparent shadow-sm transition-all" 
                />
                {errors.city && <p className="mt-2 text-sm text-red-600">{errors.city.message}</p>}
              </div>
              <div>
                <label htmlFor="state" className="block text-sm font-semibold text-gray-700 mb-2">
                  State <span className="text-red-500">*</span>
                </label>
                <input 
                  id="state" 
                  type="text" 
                  placeholder="Enter state (e.g., Massachusetts or MA)"
                  value={watch('state') || ''}
                  onChange={(e) => setValue('state', e.target.value.trim())}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#1e68d1] focus:border-transparent shadow-sm transition-all" 
                />
                {errors.state && <p className="mt-2 text-sm text-red-600">{errors.state.message}</p>}
              </div>
              <div>
                <label htmlFor="zipCode" className="block text-sm font-semibold text-gray-700 mb-2">
                  ZIP Code <span className="text-red-500">*</span>
                </label>
                <input 
                  id="zipCode" 
                  type="text" 
                  placeholder="Enter ZIP code (e.g., 02101)"
                  value={watch('zipCode') || ''}
                  onChange={(e) => setValue('zipCode', e.target.value.trim())}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#1e68d1] focus:border-transparent shadow-sm transition-all" 
                />
                {errors.zipCode && <p className="mt-2 text-sm text-red-600">{errors.zipCode.message}</p>}
              </div>
              <div>
                <label htmlFor="cancerType" className="block text-sm font-semibold text-gray-700 mb-2">
                  Cancer Type <span className="text-red-500">*</span>
                </label>
                <input 
                  id="cancerType" 
                  type="text" 
                  placeholder="e.g., Non-Small Cell Lung Cancer"
                  value={watch('cancerType') || ''}
                  onChange={(e) => setValue('cancerType', e.target.value.trim())}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#1e68d1] focus:border-transparent shadow-sm transition-all" 
                />
                {errors.cancerType && <p className="mt-2 text-sm text-red-600">{errors.cancerType.message}</p>}
              </div>
              <div>
                <label htmlFor="stage" className="block text-sm font-semibold text-gray-700 mb-2">
                  Stage <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <button
                    type="button"
                    onClick={() => toggleDropdown('stage')}
                    className="w-full text-white bg-[#1e68d1] hover:bg-[#1757b8] focus:ring-4 focus:outline-none focus:ring-blue-300 font-medium rounded-lg text-sm px-5 py-2.5 text-center inline-flex items-center justify-between"
                  >
                    {watch('stage') ? `Stage ${watch('stage')}` : 'Select stage'}
                    <svg className={`w-2.5 h-2.5 ml-2 transition-transform ${dropdownStates.stage ? 'rotate-180' : ''}`} aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 10 6">
                      <path stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="m1 1 4 4 4-4"/>
                    </svg>
                  </button>
                  {dropdownStates.stage && (
                    <div className="absolute top-full mt-2 z-10 w-full bg-white divide-y divide-gray-100 rounded-lg shadow border">
                      <ul className="py-2 text-sm text-gray-700">
                        <li>
                          <button
                            type="button"
                            onClick={() => selectOption('stage', '1')}
                            className="w-full text-left px-4 py-2 hover:bg-gray-100"
                          >
                            Stage 1
                          </button>
                        </li>
                        <li>
                          <button
                            type="button"
                            onClick={() => selectOption('stage', '2')}
                            className="w-full text-left px-4 py-2 hover:bg-gray-100"
                          >
                            Stage 2
                          </button>
                        </li>
                        <li>
                          <button
                            type="button"
                            onClick={() => selectOption('stage', '3')}
                            className="w-full text-left px-4 py-2 hover:bg-gray-100"
                          >
                            Stage 3
                          </button>
                        </li>
                        <li>
                          <button
                            type="button"
                            onClick={() => selectOption('stage', '4')}
                            className="w-full text-left px-4 py-2 hover:bg-gray-100"
                          >
                            Stage 4
                          </button>
                        </li>
                      </ul>
                    </div>
                  )}
                </div>
                {errors.stage && <p className="mt-2 text-sm text-red-600">{errors.stage.message}</p>}
              </div>
              <div>
                <label htmlFor="subtype" className="block text-sm font-semibold text-gray-700 mb-2">
                  Subtype (optional)
                </label>
                <input 
                  id="subtype" 
                  type="text" 
                  placeholder="e.g., Adenocarcinoma"
                  value={watch('subtype') || ''}
                  onChange={(e) => setValue('subtype', e.target.value.trim())}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#1e68d1] focus:border-transparent shadow-sm transition-all" 
                />
              </div>
            </div>
          </div>
        );

      case 2:
        return (
          <div className="bg-white rounded-lg shadow-md border border-gray-200 p-8">
            <h4 className="text-2xl font-bold text-gray-900 mb-8">Medical History</h4>
            <div className="space-y-6">
              <div>
                <label htmlFor="currentMedications" className="block text-sm font-semibold text-gray-700 mb-2">Current Medications (comma-separated)</label>
                <input 
                  id="currentMedications" 
                  type="text" 
                  placeholder="e.g., Erlotinib, Carboplatin"
                  value={watch('currentMedications') || ''}
                  onChange={(e) => setValue('currentMedications', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#1e68d1] focus:border-transparent shadow-sm transition-all" 
                />
              </div>
              <div>
                <label htmlFor="previousMedications" className="block text-sm font-semibold text-gray-700 mb-2">Previous Medications (comma-separated)</label>
                <input 
                  id="previousMedications" 
                  type="text" 
                  placeholder="e.g., Cisplatin, Pemetrexed"
                  value={watch('previousMedications') || ''}
                  onChange={(e) => setValue('previousMedications', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#1e68d1] focus:border-transparent shadow-sm transition-all" 
                />
              </div>
              <div>
                <label htmlFor="treatmentResponse" className="block text-sm font-semibold text-gray-700 mb-2">Response to Previous Treatment</label>
                <div className="relative">
                  <button
                    type="button"
                    onClick={() => toggleDropdown('treatmentResponse')}
                    className="w-full text-white bg-[#1e68d1] hover:bg-[#1757b8] focus:ring-4 focus:outline-none focus:ring-blue-300 font-medium rounded-lg text-sm px-5 py-2.5 text-center inline-flex items-center justify-between"
                  >
                    {watch('treatmentResponse') ? (
                      watch('treatmentResponse') === 'complete' ? 'Complete Response' :
                      watch('treatmentResponse') === 'partial' ? 'Partial Response' :
                      watch('treatmentResponse') === 'stable' ? 'Stable Disease' :
                      'Progressive Disease'
                    ) : 'Select response'}
                    <svg className={`w-2.5 h-2.5 ml-2 transition-transform ${dropdownStates.treatmentResponse ? 'rotate-180' : ''}`} aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 10 6">
                      <path stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="m1 1 4 4 4-4"/>
                    </svg>
                  </button>
                  {dropdownStates.treatmentResponse && (
                    <div className="absolute top-full mt-2 z-10 w-full bg-white divide-y divide-gray-100 rounded-lg shadow border">
                      <ul className="py-2 text-sm text-gray-700">
                        <li>
                          <button
                            type="button"
                            onClick={() => selectOption('treatmentResponse', 'complete')}
                            className="w-full text-left px-4 py-2 hover:bg-gray-100"
                          >
                            Complete Response
                          </button>
                        </li>
                        <li>
                          <button
                            type="button"
                            onClick={() => selectOption('treatmentResponse', 'partial')}
                            className="w-full text-left px-4 py-2 hover:bg-gray-100"
                          >
                            Partial Response
                          </button>
                        </li>
                        <li>
                          <button
                            type="button"
                            onClick={() => selectOption('treatmentResponse', 'stable')}
                            className="w-full text-left px-4 py-2 hover:bg-gray-100"
                          >
                            Stable Disease
                          </button>
                        </li>
                        <li>
                          <button
                            type="button"
                            onClick={() => selectOption('treatmentResponse', 'progressive')}
                            className="w-full text-left px-4 py-2 hover:bg-gray-100"
                          >
                            Progressive Disease
                          </button>
                        </li>
                      </ul>
                    </div>
                  )}
                </div>
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Biomarkers</label>
                <div className="space-y-4">
                  <div className="flex items-center">
                    <input 
                      id="egfr" 
                      type="checkbox" 
                      checked={watch('egfr') || false}
                      onChange={(e) => setValue('egfr', e.target.checked)}
                      className="h-5 w-5 text-[#1e68d1] focus:ring-[#1e68d1] border-gray-300 rounded" 
                    />
                    <label htmlFor="egfr" className="ml-3 text-sm text-gray-700">EGFR Positive</label>
                  </div>
                  <div className="flex items-center">
                    <input 
                      id="alk" 
                      type="checkbox" 
                      checked={watch('alk') || false}
                      onChange={(e) => setValue('alk', e.target.checked)}
                      className="h-5 w-5 text-[#1e68d1] focus:ring-[#1e68d1] border-gray-300 rounded" 
                    />
                    <label htmlFor="alk" className="ml-3 text-sm text-gray-700">ALK Positive</label>
                  </div>
                  <div className="flex items-center">
                    <input 
                      id="pdl1" 
                      type="checkbox" 
                      checked={watch('pdl1') || false}
                      onChange={(e) => setValue('pdl1', e.target.checked)}
                      className="h-5 w-5 text-[#1e68d1] focus:ring-[#1e68d1] border-gray-300 rounded" 
                    />
                    <label htmlFor="pdl1" className="ml-3 text-sm text-gray-700">PD-L1 Positive</label>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="bg-white rounded-lg shadow-md border border-gray-200 p-8">
            <h4 className="text-2xl font-bold text-gray-900 mb-8">Additional Info</h4>
            <div className="space-y-6">
              <div>
                <label htmlFor="allergies" className="block text-sm font-semibold text-gray-700 mb-2">Allergies (comma-separated)</label>
                <input 
                  id="allergies" 
                  type="text" 
                  placeholder="e.g., Penicillin, Sulfa drugs"
                  value={watch('allergies') || ''}
                  onChange={(e) => setValue('allergies', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#1e68d1] focus:border-transparent shadow-sm transition-all" 
                />
              </div>
              <div>
                <label htmlFor="comorbidities" className="block text-sm font-semibold text-gray-700 mb-2">Other Conditions (comma-separated)</label>
                <input 
                  id="comorbidities" 
                  type="text" 
                  placeholder="e.g., Diabetes, Hypertension"
                  value={watch('comorbidities') || ''}
                  onChange={(e) => setValue('comorbidities', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#1e68d1] focus:border-transparent shadow-sm transition-all" 
                />
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div ref={dropdownRef}>
      {renderStep(step)}
    </div>
  );
};

export function StructuredForm({ onSubmit, isProcessing }: StructuredFormProps) {
  const methods = useForm<StructuredFormData>({
    resolver: zodResolver(structuredFormSchema),
    mode: 'onChange',
  });

  const [step, setStep] = useState(0);
  const steps = ['Personal Info', 'Location & Diagnosis', 'Medical History', 'Additional Info'];

  // Calculate progress based on completed fields
  const calculateProgress = () => {
    const formData = methods.watch();
    let completedFields = 0;
    let totalRequiredFields = 0;

    // Count completed fields up to current step
    for (let i = 0; i <= step; i++) {
      const currentStepFields = stepFields[i];
      
      currentStepFields.forEach(fieldName => {
        const value = formData[fieldName];
        // Count required fields (age, gender, city, state, zipCode, cancerType, stage are required)
        const requiredFields = ['age', 'gender', 'city', 'state', 'zipCode', 'cancerType', 'stage'];
        
        if (requiredFields.includes(fieldName)) {
          totalRequiredFields++;
          if (value !== undefined && value !== null && value !== '') {
            completedFields++;
          }
        } else {
          // Optional fields - count them but with less weight
          totalRequiredFields += 0.5;
          if (value !== undefined && value !== null && value !== '') {
            completedFields += 0.5;
          }
        }
      });
    }

    // Calculate percentage: base on step completion + field completion within step
    const baseProgress = (step / steps.length) * 100;
    const currentStepProgress = stepFields[step] ? 
      (completedFields / Math.max(totalRequiredFields, 1)) * (100 / steps.length) : 0;
    
    return Math.min(Math.round(baseProgress + currentStepProgress), 100);
  };

  const progressPercentage = calculateProgress();

  useEffect(() => {
    const subscription = methods.watch((value) => {
      // Save form data to local state or context if needed, but don't display
    });
    return () => subscription.unsubscribe();
  }, [methods.watch]);

  const next = async () => {
    const fields = stepFields[step];
    const valid = await methods.trigger(fields);
    if (valid) {
      const newStep = Math.min(step + 1, steps.length - 1);
      setStep(newStep);
    }
  };

  const back = () => setStep((s: number) => Math.max(s - 1, 0));

  const handleFormSubmit = async (data: StructuredFormData) => {
    const patientData: PatientData = {
      age: data.age,
      gender: data.gender,
      location: {
        city: data.city,
        state: data.state,
        zipCode: data.zipCode,
      },
      diagnosis: {
        cancerType: data.cancerType,
        stage: data.stage,
        subtype: data.subtype,
      },
      biomarkers: {
        egfr: data.egfr,
        alk: data.alk,
        pdl1: data.pdl1,
      },
      treatments: {
        current: data.currentMedications?.split(',').map((m) => ({ name: m.trim() })) || [],
        previous: data.previousMedications?.split(',').map((m) => ({ name: m.trim() })) || [],
        response: data.treatmentResponse,
      },
      allergies: data.allergies?.split(',').map((a) => a.trim()) || [],
      comorbidities: data.comorbidities?.split(',').map((c) => c.trim()) || [],
    };

    await onSubmit(patientData);
  };

  return (
    <FormProvider {...methods}>
      <div className="w-full">
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-gray-600">Step {step + 1} of {steps.length}: {steps[step]}</p>
            <p className="text-sm text-gray-600">{progressPercentage}% Complete</p>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div className="bg-[#1e68d1] h-2.5 rounded-full transition-all duration-300" style={{ width: `${progressPercentage}%` }}></div>
          </div>
        </div>

        <form 
          onSubmit={(e) => {
            e.preventDefault();
            if (step === steps.length - 1) {
              methods.handleSubmit(handleFormSubmit)(e);
            }
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault();
              if (step < steps.length - 1) {
                next();
              }
              // Do nothing on final step - user must click the button
            }
          }}
          className="space-y-6"
        >
          <StepContent step={step} stepFields={stepFields} />

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button type="button" onClick={back} disabled={step === 0} className="px-6 py-3 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-100 disabled:opacity-50 transition-all">
                Back
              </button>
              {step < steps.length - 1 ? (
                <button type="button" onClick={next} className="px-6 py-3 rounded-lg bg-[#1e68d1] text-white hover:bg-[#1757b8] transition-all">
                  Next
                </button>
              ) : (
                <button 
                  type="button"
                  onClick={() => methods.handleSubmit(handleFormSubmit)()}
                  disabled={isProcessing} 
                  className="px-6 py-3 rounded-lg bg-gradient-to-br from-[#1e68d1] to-[#0b4fa1] text-white hover:from-[#1757b8] hover:to-[#083f83] disabled:opacity-50 transition-all"
                >
                  {isProcessing ? 'Finding Matching Trials...' : 'Find My Matching Trials'}
                </button>
              )}
            </div>
          </div>
        </form>
      </div>
    </FormProvider>
  );
}