export function Footer() {
  return (
    <footer className="bg-gray-50 border-t border-gray-200 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-3">About MedMatch AI</h3>
            <p className="text-sm text-gray-600">
              Connecting cancer patients with potentially life-saving clinical trials using AI-powered matching.
            </p>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-3">Resources</h3>
            <ul className="space-y-2">
              <li>
                <a href="/faq" className="text-sm text-gray-600 hover:text-primary-blue">
                  FAQ
                </a>
              </li>
              <li>
                <a href="/how-it-works" className="text-sm text-gray-600 hover:text-primary-blue">
                  How It Works
                </a>
              </li>
              <li>
                <a href="/privacy" className="text-sm text-gray-600 hover:text-primary-blue">
                  Privacy Policy
                </a>
              </li>
              <li>
                <a href="/terms" className="text-sm text-gray-600 hover:text-primary-blue">
                  Terms of Service
                </a>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-3">Contact</h3>
            <p className="text-sm text-gray-600">
              For support or questions:
              <br />
              <a href="mailto:support@medmatch.ai" className="text-primary-blue hover:underline">
                support@medmatch.ai
              </a>
            </p>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-gray-200">
          <p className="text-xs text-gray-500 text-center">
            © {new Date().getFullYear()} MedMatch AI. This tool is for informational purposes only and should not replace professional medical advice.
          </p>
        </div>
      </div>
    </footer>
  );
}
