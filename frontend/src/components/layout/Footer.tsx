import { Link } from 'react-router-dom';
import { Heart, Mail, MapPin, Phone } from 'lucide-react';

export function Footer() {
  return (
    <footer className="bg-gradient-to-br from-gray-900 via-slate-800 to-gray-900 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        {/* Newsletter Section */}
        <div className="border-b border-gray-800/50 pb-10 mb-10">
          <div className="max-w-3xl mx-auto text-center">
            <h3 className="text-3xl font-bold mb-4">Stay Updated</h3>
            <p className="text-gray-400 mb-6">Get the latest updates on clinical trials, AI matching improvements, and healthcare insights.</p>
            <div className="flex items-center justify-center gap-3 max-w-md mx-auto">
              <input type="email" placeholder="Enter your email" className="flex-1 h-12 px-4 rounded-lg bg-gray-800/60 border border-gray-700 text-white placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all" />
              <button className="h-12 px-6 rounded-lg font-semibold text-white bg-gradient-to-br from-[#1e68d1] to-[#0b4fa1] shadow-lg hover:from-[#1757b8] hover:to-[#083f83] transition">Subscribe</button>
            </div>
            <p className="text-xs text-gray-500 mt-3">We respect your privacy. Unsubscribe at any time.</p>
          </div>
        </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {/* Company Info */}
            <div className="lg:col-span-1">
            <div className="flex items-center space-x-3 mb-6">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-600 to-cyan-600 flex items-center justify-center shadow-lg">
                <span className="text-white font-black text-2xl">M</span>
              </div>
              <span className="text-2xl font-black">MedMatch<span className="text-cyan-500">AI</span></span>
            </div>
            <p className="text-gray-300 mb-6 leading-relaxed">
              Connecting cancer patients with potentially life-saving clinical trials using AI-powered matching.
              Bringing hope when it matters most.
            </p>
            <div className="flex space-x-4">
              <a href="#" className="text-gray-400 hover:text-blue-400 transition-colors">
                <div className="w-10 h-10 bg-gray-800 rounded-full flex items-center justify-center hover:bg-blue-600 transition-colors">
                  <Mail className="w-5 h-5" />
                </div>
              </a>
              <a href="#" className="text-gray-400 hover:text-blue-400 transition-colors">
                <div className="w-10 h-10 bg-gray-800 rounded-full flex items-center justify-center hover:bg-blue-600 transition-colors">
                  <Phone className="w-5 h-5" />
                </div>
              </a>
              <a href="#" className="text-gray-400 hover:text-blue-400 transition-colors">
                <div className="w-10 h-10 bg-gray-800 rounded-full flex items-center justify-center hover:bg-blue-600 transition-colors">
                  <MapPin className="w-5 h-5" />
                </div>
              </a>
            </div>
          </div>

          {/* Resources */}
          <div>
            <h3 className="text-lg font-semibold text-white mb-6">Resources</h3>
            <ul className="space-y-3">
              {[
                { name: 'How It Works', href: '/how-it-works' },
                { name: 'FAQ', href: '/faq' },
                { name: 'Success Stories', href: '/stories' },
                { name: 'Research', href: '/research' },
                { name: 'Blog', href: '/blog' }
              ].map((item) => (
                <li key={item.name}>
                  <Link
                    to={item.href}
                    className="text-gray-300 hover:text-blue-400 transition-colors duration-200 hover:translate-x-1 transform inline-block"
                  >
                    {item.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Support */}
          <div>
            <h3 className="text-lg font-semibold text-white mb-6">Support</h3>
            <ul className="space-y-3">
              {[
                { name: 'Contact Us', href: '/contact' },
                { name: 'Help Center', href: '/help' },
                { name: 'Privacy Policy', href: '/privacy' },
                { name: 'Terms of Service', href: '/terms' },
                { name: 'Accessibility', href: '/accessibility' }
              ].map((item) => (
                <li key={item.name}>
                  <Link
                    to={item.href}
                    className="text-gray-300 hover:text-blue-400 transition-colors duration-200 hover:translate-x-1 transform inline-block"
                  >
                    {item.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h3 className="text-lg font-semibold text-white mb-6">Get in Touch</h3>
            <div className="space-y-4">
              <div className="flex items-start space-x-3">
                <Mail className="w-5 h-5 text-blue-400 mt-0.5" />
                <div>
                  <p className="text-gray-300 text-sm">Email us at</p>
                  <a
                    href="mailto:support@medmatch.ai"
                    className="text-blue-400 hover:text-blue-300 transition-colors"
                  >
                    support@medmatch.ai
                  </a>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <Phone className="w-5 h-5 text-blue-400 mt-0.5" />
                <div>
                  <p className="text-gray-300 text-sm">Call us at</p>
                  <a
                    href="tel:+1-800-MEDMATCH"
                    className="text-blue-400 hover:text-blue-300 transition-colors"
                  >
                    1-800-MEDMATCH
                  </a>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <MapPin className="w-5 h-5 text-blue-400 mt-0.5" />
                <div>
                  <p className="text-gray-300 text-sm">
                    123 Healthcare Blvd<br />
                    San Francisco, CA 94107
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Section */}
        <div className="mt-12 pt-8 border-t border-gray-700">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            <p className="text-sm text-gray-400 text-center md:text-left">
              © {new Date().getFullYear()} MedMatch AI. All rights reserved.
            </p>
            <p className="text-xs text-gray-500 text-center md:text-right max-w-md">
              This tool is for informational purposes only and should not replace professional medical advice.
              Always consult with healthcare professionals for medical decisions.
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
}
