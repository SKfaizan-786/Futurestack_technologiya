import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { Heart, Search, FileText, Zap, Shield, Clock, Users, Star, Activity, Brain, Stethoscope, MapPin, ArrowUp } from 'lucide-react';

export function Landing() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [showTop, setShowTop] = useState(false);

  useEffect(() => {
    const onScroll = () => setShowTop(window.scrollY > 300);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const scrollToTop = () => window.scrollTo({ top: 0, behavior: 'smooth' });

  const handleFindTrial = () => {
    if (user) navigate('/search');
    else navigate('/login');
  };

  const handleGetStarted = () => navigate('/signup');

  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section */}
  <section className="relative bg-gradient-to-br from-blue-50 via-white to-purple-50 pt-20 pb-32 overflow-hidden scroll-mt-16" id="hero">
        {/* Subtle background decoration */}
        <div className="absolute inset-0 overflow-hidden opacity-30">
          <div className="absolute top-20 right-20 w-72 h-72 bg-blue-200 rounded-full mix-blend-multiply filter blur-3xl animate-blob"></div>
          <div className="absolute top-40 left-20 w-72 h-72 bg-purple-200 rounded-full mix-blend-multiply filter blur-3xl animate-blob animation-delay-2000"></div>
        </div>

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Powered by badge */}
          <div className="flex justify-center mb-8">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-100 text-blue-700 rounded-full text-sm font-medium">
              <Activity className="w-4 h-4" />
              Powered by Llama 3.2 - Cerebras AI
            </div>
          </div>

          {/* Main heading */}
          <div className="text-center max-w-4xl mx-auto">
            <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
              Find Life-Saving
              <br />
              <span className="text-blue-600">Clinical Trials</span>
              <br />
              <span className="text-gray-900">in Under 100ms</span>
            </h1>

            <p className="text-xl text-gray-600 mb-10 max-w-3xl mx-auto leading-relaxed">
              AI-powered matching connects cancer patients with eligible clinical trials using cutting-edge technology and <span className="font-semibold text-gray-900">explainable reasoning</span>.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row justify-center gap-4 mb-16">
              <button onClick={handleFindTrial} className="px-8 py-4 rounded-lg font-semibold text-white bg-gradient-to-br from-[#1e68d1] to-[#0b4fa1] shadow-lg hover:from-[#1757b8] hover:to-[#083f83] transition-all hover:shadow-xl transform hover:-translate-y-0.5">
                Find Your Trial →
              </button>
              <button onClick={() => {
                const el = document.getElementById('for-providers');
                if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
                else navigate('/');
              }} className="px-8 py-4 bg-white text-gray-700 font-semibold rounded-lg border-2 border-gray-200 hover:border-blue-600 hover:text-blue-600 transition-all">
                For Healthcare Providers
              </button>
            </div>

            {/* Trust badges */}
            <div className="flex flex-wrap justify-center items-center gap-8 text-sm text-gray-600">
              <div className="flex items-center gap-2">
                <Shield className="w-5 h-5 text-green-600" />
                <span>HIPAA Compliant</span>
              </div>
              <div className="flex items-center gap-2">
                <Clock className="w-5 h-5 text-blue-600" />
                <span>&lt; 100ms Response</span>
              </div>
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-purple-600" />
                <span>Open Source</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
  <section id="how-it-works" className="py-24 bg-white scroll-mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
              How It Works
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Three simple steps to find your clinical trial match
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Step 1 */}
            <div className="bg-white border-2 border-gray-100 rounded-2xl p-8 hover:border-blue-200 hover:shadow-lg transition-all">
              <div className="w-16 h-16 bg-blue-100 rounded-xl flex items-center justify-center mb-6">
                <FileText className="w-8 h-8 text-blue-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">
                Enter Patient Information
              </h3>
              <p className="text-gray-600 leading-relaxed">
                Upload medical records, enter diagnosis details, and patient demographics in a simple, secure form.
              </p>
            </div>

            {/* Step 2 */}
            <div className="bg-white border-2 border-gray-100 rounded-2xl p-8 hover:border-blue-200 hover:shadow-lg transition-all">
              <div className="w-16 h-16 bg-purple-100 rounded-xl flex items-center justify-center mb-6">
                <Brain className="w-8 h-8 text-purple-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">
                AI Matches Trials
              </h3>
              <p className="text-gray-600 leading-relaxed">
                Our AI analyzes 1000+ clinical trials in under 100ms, ranking them by eligibility match score.
              </p>
            </div>

            {/* Step 3 */}
            <div className="bg-white border-2 border-gray-100 rounded-2xl p-8 hover:border-blue-200 hover:shadow-lg transition-all">
              <div className="w-16 h-16 bg-green-100 rounded-xl flex items-center justify-center mb-6">
                <Stethoscope className="w-8 h-8 text-green-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">
                Get Personalized Results
              </h3>
              <p className="text-gray-600 leading-relaxed">
                View detailed trial information with plain-language explanations and direct contact options.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Platform Features Section */}
  <section id="features" className="py-24 bg-gradient-to-br from-gray-50 to-blue-50 scroll-mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
              Platform Features
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Everything you need to find the right clinical trial, powered by AI
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Lightning Fast */}
            <div className="bg-white rounded-2xl p-8 shadow-sm hover:shadow-xl transition-all">
              <div className="w-14 h-14 bg-yellow-100 rounded-xl flex items-center justify-center mb-6">
                <Zap className="w-7 h-7 text-yellow-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">Lightning Fast</h3>
              <p className="text-gray-600">
                Get matching results in under 100ms with our optimized AI infrastructure powered by Cerebras.
              </p>
            </div>

            {/* HIPAA Compliant */}
            <div className="bg-white rounded-2xl p-8 shadow-sm hover:shadow-xl transition-all">
              <div className="w-14 h-14 bg-green-100 rounded-xl flex items-center justify-center mb-6">
                <Shield className="w-7 h-7 text-green-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">HIPAA Compliant</h3>
              <p className="text-gray-600">
                Bank-level encryption and full HIPAA compliance ensure your medical data stays private and secure.
              </p>
            </div>

            {/* Explainable AI */}
            <div className="bg-white rounded-2xl p-8 shadow-sm hover:shadow-xl transition-all">
              <div className="w-14 h-14 bg-purple-100 rounded-xl flex items-center justify-center mb-6">
                <Brain className="w-7 h-7 text-purple-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">Explainable AI</h3>
              <p className="text-gray-600">
                Understand exactly why each trial was matched with clear, transparent reasoning in plain language.
              </p>
            </div>

            {/* Real-time Alerts */}
            <div className="bg-white rounded-2xl p-8 shadow-sm hover:shadow-xl transition-all">
              <div className="w-14 h-14 bg-blue-100 rounded-xl flex items-center justify-center mb-6">
                <Activity className="w-7 h-7 text-blue-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">Find Near Me</h3>
              <p className="text-gray-600">
                Automatically filter trials by location to find options closest to you or your patients.
              </p>
            </div>

            {/* Open Source */}
            <div className="bg-white rounded-2xl p-8 shadow-sm hover:shadow-xl transition-all">
              <div className="w-14 h-14 bg-indigo-100 rounded-xl flex items-center justify-center mb-6">
                <FileText className="w-7 h-7 text-indigo-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">Open Source</h3>
              <p className="text-gray-600">
                Built transparently with open-source technology. Review our code and contribute on GitHub.
              </p>
            </div>

            {/* Provider Dashboard */}
            <div className="bg-white rounded-2xl p-8 shadow-sm hover:shadow-xl transition-all">
              <div className="w-14 h-14 bg-pink-100 rounded-xl flex items-center justify-center mb-6">
                <Users className="w-7 h-7 text-pink-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">Provider Dashboard</h3>
              <p className="text-gray-600">
                Healthcare providers get dedicated tools to manage multiple patients and track referrals.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-20 bg-gradient-to-r from-blue-600 to-indigo-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center text-white">
            <div>
              <div className="text-5xl md:text-6xl font-extrabold mb-2 text-[#00c2c7]">&lt; 100ms</div>
              <div className="text-blue-200 text-lg">Avg Response</div>
            </div>
            <div>
              <div className="text-5xl md:text-6xl font-extrabold mb-2">1000+</div>
              <div className="text-blue-200 text-lg">Clinical Trials</div>
            </div>
            <div>
              <div className="text-5xl md:text-6xl font-extrabold mb-2">100%</div>
              <div className="text-blue-200 text-lg">Match Rate</div>
            </div>
            <div>
              <div className="text-5xl md:text-6xl font-extrabold mb-2">HIPAA</div>
              <div className="text-blue-200 text-lg">Compliant</div>
            </div>
          </div>
        </div>
      </section>

      {/* Healthcare Providers Section */}
  <section id="for-providers" className="py-24 bg-gray-900 text-white scroll-mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold mb-6">
              Built for Healthcare Providers
            </h2>
            <p className="text-xl text-gray-300 max-w-2xl mx-auto">
              Advanced tools built for medical professionals to help their patients find hope
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto">
            <div className="flex items-start gap-4 bg-gray-800 p-6 rounded-xl">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center flex-shrink-0">
                <Users className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-semibold mb-1">Multi-patient Management</h3>
                <p className="text-gray-400 text-sm">Manage and track multiple patients from one dashboard</p>
              </div>
            </div>

            <div className="flex items-start gap-4 bg-gray-800 p-6 rounded-xl">
              <div className="w-8 h-8 bg-green-600 rounded-lg flex items-center justify-center flex-shrink-0">
                <Shield className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-semibold mb-1">Enterprise-grade Security</h3>
                <p className="text-gray-400 text-sm">Full HIPAA compliance and data encryption at rest</p>
              </div>
            </div>

            <div className="flex items-start gap-4 bg-gray-800 p-6 rounded-xl">
              <div className="w-8 h-8 bg-purple-600 rounded-lg flex items-center justify-center flex-shrink-0">
                <Brain className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-semibold mb-1">AI-powered Insights</h3>
                <p className="text-gray-400 text-sm">Get detailed matching explanations and trial recommendations</p>
              </div>
            </div>

            <div className="flex items-start gap-4 bg-gray-800 p-6 rounded-xl">
              <div className="w-8 h-8 bg-yellow-600 rounded-lg flex items-center justify-center flex-shrink-0">
                <Zap className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-semibold mb-1">Instant Results</h3>
                <p className="text-gray-400 text-sm">Sub-100ms response times for time-sensitive cases</p>
              </div>
            </div>
          </div>

          <div className="text-center mt-12">
            <button className="px-8 py-4 bg-white text-gray-900 font-semibold rounded-lg hover:bg-gray-100 transition-all">
              Request Provider Access
            </button>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-24 bg-gradient-to-br from-blue-600 via-blue-700 to-indigo-800 text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <Heart className="w-16 h-16 mx-auto mb-6 text-blue-200" />
          <h2 className="text-4xl md:text-5xl font-extrabold mb-6">
            Ready to discover your
            <br />
            <span className="text-white">clinical trial </span><span className="text-[#00c2c7]">options?</span>
          </h2>
          <p className="text-lg text-blue-100 mb-10 max-w-2xl mx-auto">
            Join thousands of patients and caregivers finding hope through clinical trials. Start your journey today.
          </p>
          <div className="flex flex-col sm:flex-row justify-center gap-4">
            <button onClick={handleGetStarted} className="px-10 py-4 rounded-lg font-bold text-white bg-gradient-to-br from-[#1e68d1] to-[#0b4fa1] shadow-xl hover:from-[#1757b8] hover:to-[#083f83] transition transform hover:-translate-y-0.5">
              Get Started Now
            </button>
            <button className="px-10 py-4 rounded-lg bg-transparent border border-white/30 text-white font-semibold hover:bg-white/10 transition">
              Learn More
            </button>
          </div>
        </div>
      </section>

      {/* Newsletter removed from landing - moved to footer */}
      {/* Scroll to top button */}
      {showTop && (
        <button onClick={scrollToTop} aria-label="Scroll to top" className="fixed right-6 bottom-6 w-12 h-12 rounded-full bg-gradient-to-br from-[#1e68d1] to-[#0b4fa1] text-white flex items-center justify-center shadow-lg hover:scale-105 transition">
          <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 5l-7 7h4v7h6v-7h4l-7-7z" fill="currentColor" />
          </svg>
        </button>
      )}
    </div>
  );
}

export default Landing;