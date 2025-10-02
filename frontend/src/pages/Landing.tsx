import { Link } from 'react-router-dom';
import { Heart, Search, Shield, Zap } from 'lucide-react';

export function Landing() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-gray-50">
      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16">
        <div className="text-center">
          <div className="flex justify-center mb-6">
            <Heart className="w-16 h-16 text-primary-blue" />
          </div>
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            Find Hope in Clinical Trials
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-8">
            MedMatch AI uses advanced artificial intelligence to connect cancer patients with potentially
            life-saving clinical trials. Fast, accurate, and compassionate matching when time matters most.
          </p>
          <div className="flex justify-center space-x-4">
            <Link
              to="/signup"
              className="px-8 py-4 bg-primary-blue text-white text-lg font-semibold rounded-lg hover:bg-blue-600 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-blue focus:ring-offset-2"
            >
              Get Started Free
            </Link>
            <Link
              to="/login"
              className="px-8 py-4 border-2 border-gray-300 text-gray-700 text-lg font-semibold rounded-lg hover:border-gray-400 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-blue focus:ring-offset-2"
            >
              Sign In
            </Link>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
          Why Choose MedMatch AI
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="bg-white p-6 rounded-lg border border-gray-200">
            <div className="w-12 h-12 bg-primary-blue bg-opacity-10 rounded-lg flex items-center justify-center mb-4">
              <Zap className="w-6 h-6 text-primary-blue" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">AI-Powered Matching</h3>
            <p className="text-gray-600">
              Our advanced AI analyzes thousands of trials in seconds to find the best matches for your specific condition and biomarkers.
            </p>
          </div>

          <div className="bg-white p-6 rounded-lg border border-gray-200">
            <div className="w-12 h-12 bg-secondary-green bg-opacity-10 rounded-lg flex items-center justify-center mb-4">
              <Search className="w-6 h-6 text-secondary-green" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Easy to Use</h3>
            <p className="text-gray-600">
              Simply describe the patient's condition in plain language, or use our structured form. No medical jargon required.
            </p>
          </div>

          <div className="bg-white p-6 rounded-lg border border-gray-200">
            <div className="w-12 h-12 bg-primary-teal bg-opacity-10 rounded-lg flex items-center justify-center mb-4">
              <Shield className="w-6 h-6 text-primary-teal" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Private & Secure</h3>
            <p className="text-gray-600">
              Your medical information is encrypted and secure. We never share your data without your explicit permission.
            </p>
          </div>
        </div>
      </div>

      {/* How It Works Section */}
      <div className="bg-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
            How It Works
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-primary-blue text-white rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-4">
                1
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Enter Patient Information</h3>
              <p className="text-gray-600">
                Describe the patient's condition, treatment history, and location in your own words or using our guided form.
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-primary-blue text-white rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-4">
                2
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">AI Finds Matches</h3>
              <p className="text-gray-600">
                Our AI instantly analyzes thousands of clinical trials and ranks them by compatibility with your criteria.
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-primary-blue text-white rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-4">
                3
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Connect with Trials</h3>
              <p className="text-gray-600">
                Review detailed results with plain-language explanations and contact trial coordinators directly.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="bg-primary-blue rounded-2xl p-12 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to Find Matching Trials?
          </h2>
          <p className="text-xl text-blue-100 mb-8 max-w-2xl mx-auto">
            Join thousands of patients and caregivers finding hope through clinical trials.
          </p>
          <Link
            to="/signup"
            className="inline-block px-8 py-4 bg-white text-primary-blue text-lg font-semibold rounded-lg hover:bg-gray-100 transition-colors focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-primary-blue"
          >
            Get Started Now
          </Link>
        </div>
      </div>
    </div>
  );
}
