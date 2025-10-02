import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import type { PatientData } from '../../types';

const structuredFormSchema = z.object({
  age: z.number().min(1).max(150),
  gender: z.enum(['male', 'female', 'other']),
  city: z.string().min(1, 'City is required'),
  state: z.string().min(2).max(2, 'Use 2-letter state code'),
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

export function StructuredForm({ onSubmit, isProcessing }: StructuredFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<StructuredFormData>({
    resolver: zodResolver(structuredFormSchema),
  });

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
        current: data.currentMedications?.split(',').map(m => ({ name: m.trim() })) || [],
        previous: data.previousMedications?.split(',').map(m => ({ name: m.trim() })) || [],
        response: data.treatmentResponse,
      },
      allergies: data.allergies?.split(',').map(a => a.trim()) || [],
      comorbidities: data.comorbidities?.split(',').map(c => c.trim()) || [],
    };

    await onSubmit(patientData);
  };

  return (
    <div className="w-full max-w-4xl">
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Patient Information Form</h3>
        <p className="text-sm text-gray-600">
          Fill out the detailed form below. All fields marked with * are required.
        </p>
      </div>

      <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
        {/* Demographics */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h4 className="text-md font-semibold text-gray-900 mb-4">Demographics</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label htmlFor="age" className="block text-sm font-medium text-gray-700 mb-1">
                Age <span className="text-red-500">*</span>
              </label>
              <input
                id="age"
                type="number"
                {...register('age', { valueAsNumber: true })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-blue focus:border-transparent"
              />
              {errors.age && <p className="mt-1 text-sm text-red-600">{errors.age.message}</p>}
            </div>

            <div>
              <label htmlFor="gender" className="block text-sm font-medium text-gray-700 mb-1">
                Gender <span className="text-red-500">*</span>
              </label>
              <select
                id="gender"
                {...register('gender')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-blue focus:border-transparent"
              >
                <option value="">Select...</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
              {errors.gender && <p className="mt-1 text-sm text-red-600">{errors.gender.message}</p>}
            </div>
          </div>
        </div>

        {/* Location */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h4 className="text-md font-semibold text-gray-900 mb-4">Location</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label htmlFor="city" className="block text-sm font-medium text-gray-700 mb-1">
                City <span className="text-red-500">*</span>
              </label>
              <input
                id="city"
                type="text"
                {...register('city')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-blue focus:border-transparent"
              />
              {errors.city && <p className="mt-1 text-sm text-red-600">{errors.city.message}</p>}
            </div>

            <div>
              <label htmlFor="state" className="block text-sm font-medium text-gray-700 mb-1">
                State <span className="text-red-500">*</span>
              </label>
              <input
                id="state"
                type="text"
                placeholder="MA"
                maxLength={2}
                {...register('state')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-blue focus:border-transparent uppercase"
              />
              {errors.state && <p className="mt-1 text-sm text-red-600">{errors.state.message}</p>}
            </div>

            <div>
              <label htmlFor="zipCode" className="block text-sm font-medium text-gray-700 mb-1">
                ZIP Code <span className="text-red-500">*</span>
              </label>
              <input
                id="zipCode"
                type="text"
                {...register('zipCode')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-blue focus:border-transparent"
              />
              {errors.zipCode && <p className="mt-1 text-sm text-red-600">{errors.zipCode.message}</p>}
            </div>
          </div>
        </div>

        {/* Diagnosis */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h4 className="text-md font-semibold text-gray-900 mb-4">Diagnosis</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="cancerType" className="block text-sm font-medium text-gray-700 mb-1">
                Cancer Type <span className="text-red-500">*</span>
              </label>
              <input
                id="cancerType"
                type="text"
                placeholder="e.g., Non-Small Cell Lung Cancer"
                {...register('cancerType')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-blue focus:border-transparent"
              />
              {errors.cancerType && <p className="mt-1 text-sm text-red-600">{errors.cancerType.message}</p>}
            </div>

            <div>
              <label htmlFor="stage" className="block text-sm font-medium text-gray-700 mb-1">
                Stage <span className="text-red-500">*</span>
              </label>
              <select
                id="stage"
                {...register('stage')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-blue focus:border-transparent"
              >
                <option value="">Select...</option>
                <option value="1">Stage 1</option>
                <option value="2">Stage 2</option>
                <option value="3">Stage 3</option>
                <option value="4">Stage 4</option>
              </select>
              {errors.stage && <p className="mt-1 text-sm text-red-600">{errors.stage.message}</p>}
            </div>

            <div className="md:col-span-2">
              <label htmlFor="subtype" className="block text-sm font-medium text-gray-700 mb-1">
                Subtype (optional)
              </label>
              <input
                id="subtype"
                type="text"
                placeholder="e.g., Adenocarcinoma"
                {...register('subtype')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-blue focus:border-transparent"
              />
            </div>
          </div>
        </div>

        {/* Biomarkers */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h4 className="text-md font-semibold text-gray-900 mb-4">Biomarkers</h4>
          <div className="space-y-3">
            <div className="flex items-center">
              <input
                id="egfr"
                type="checkbox"
                {...register('egfr')}
                className="h-4 w-4 text-primary-blue focus:ring-primary-blue border-gray-300 rounded"
              />
              <label htmlFor="egfr" className="ml-2 text-sm text-gray-700">
                EGFR Positive
              </label>
            </div>
            <div className="flex items-center">
              <input
                id="alk"
                type="checkbox"
                {...register('alk')}
                className="h-4 w-4 text-primary-blue focus:ring-primary-blue border-gray-300 rounded"
              />
              <label htmlFor="alk" className="ml-2 text-sm text-gray-700">
                ALK Positive
              </label>
            </div>
            <div className="flex items-center">
              <input
                id="pdl1"
                type="checkbox"
                {...register('pdl1')}
                className="h-4 w-4 text-primary-blue focus:ring-primary-blue border-gray-300 rounded"
              />
              <label htmlFor="pdl1" className="ml-2 text-sm text-gray-700">
                PD-L1 Positive
              </label>
            </div>
          </div>
        </div>

        {/* Treatment History */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h4 className="text-md font-semibold text-gray-900 mb-4">Treatment History</h4>
          <div className="space-y-4">
            <div>
              <label htmlFor="currentMedications" className="block text-sm font-medium text-gray-700 mb-1">
                Current Medications (comma-separated)
              </label>
              <input
                id="currentMedications"
                type="text"
                placeholder="e.g., Erlotinib, Carboplatin"
                {...register('currentMedications')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-blue focus:border-transparent"
              />
            </div>

            <div>
              <label htmlFor="previousMedications" className="block text-sm font-medium text-gray-700 mb-1">
                Previous Medications (comma-separated)
              </label>
              <input
                id="previousMedications"
                type="text"
                placeholder="e.g., Cisplatin, Pemetrexed"
                {...register('previousMedications')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-blue focus:border-transparent"
              />
            </div>

            <div>
              <label htmlFor="treatmentResponse" className="block text-sm font-medium text-gray-700 mb-1">
                Response to Previous Treatment
              </label>
              <select
                id="treatmentResponse"
                {...register('treatmentResponse')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-blue focus:border-transparent"
              >
                <option value="">Select...</option>
                <option value="complete">Complete Response</option>
                <option value="partial">Partial Response</option>
                <option value="stable">Stable Disease</option>
                <option value="progressive">Progressive Disease</option>
              </select>
            </div>
          </div>
        </div>

        {/* Other Medical Information */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h4 className="text-md font-semibold text-gray-900 mb-4">Other Medical Information</h4>
          <div className="space-y-4">
            <div>
              <label htmlFor="allergies" className="block text-sm font-medium text-gray-700 mb-1">
                Allergies (comma-separated)
              </label>
              <input
                id="allergies"
                type="text"
                placeholder="e.g., Penicillin, Sulfa drugs"
                {...register('allergies')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-blue focus:border-transparent"
              />
            </div>

            <div>
              <label htmlFor="comorbidities" className="block text-sm font-medium text-gray-700 mb-1">
                Other Conditions (comma-separated)
              </label>
              <input
                id="comorbidities"
                type="text"
                placeholder="e.g., Diabetes, Hypertension"
                {...register('comorbidities')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-blue focus:border-transparent"
              />
            </div>
          </div>
        </div>

        <button
          type="submit"
          disabled={isProcessing}
          className="w-full py-3 px-6 bg-primary-blue text-white font-medium rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-primary-blue focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isProcessing ? 'Finding Matching Trials...' : 'Find Matching Trials'}
        </button>
      </form>
    </div>
  );
}
