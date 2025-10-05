import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { User } from 'lucide-react';

export function Header() {
  const { user, signOut } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  

  const isLandingPage = location.pathname === '/';

  const scrollToSection = (sectionId: string) => {
    const doScroll = () => {
      const element = document.getElementById(sectionId);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    };

    if (isLandingPage) {
      doScroll();
    } else {
      // Navigate to landing then scroll after a short delay
      navigate('/');
      setTimeout(doScroll, 250);
    }
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-3 items-center h-16">
          {/* Left: M logo + brand name */}
          <div className="col-start-1">
            <Link to="/" className="inline-flex items-center gap-3" aria-label="MedMatch AI home">
              <div className="w-11 h-11 rounded-lg bg-gradient-to-br from-[#1e68d1] to-[#0b4fa1] shadow-md flex items-center justify-center text-white font-extrabold text-lg">M</div>
              <span className="text-lg font-extrabold text-gray-900 tracking-tight">MedMatch<span className="text-[#00c2c7]">AI</span></span>
            </Link>
          </div>

          {/* Center navigation - visible when not logged in (centered) */}
          <nav className="col-start-2 justify-self-center flex items-center space-x-4">
            {!user && (
              <>
                <button onClick={() => scrollToSection('features')} className="px-3 py-2 rounded-md text-gray-700 hover:bg-gray-100 hover:shadow-sm transition">Features</button>
                <button onClick={() => scrollToSection('how-it-works')} className="px-3 py-2 rounded-md text-gray-700 hover:bg-gray-100 hover:shadow-sm transition">How It Works</button>
                <button onClick={() => scrollToSection('for-providers')} className="px-3 py-2 rounded-md text-gray-700 hover:bg-gray-100 hover:shadow-sm transition">For Providers</button>
              </>
            )}

            {user && (
              <>
                <Link to="/dashboard" className="px-3 py-2 rounded-md text-gray-700 hover:bg-gray-100 hover:shadow-sm transition">Dashboard</Link>
                <Link to="/search" className="px-3 py-2 rounded-md text-gray-700 hover:bg-gray-100 hover:shadow-sm transition">Trials</Link>
                <Link to="/saved" className="px-3 py-2 rounded-md text-gray-700 hover:bg-gray-100 hover:shadow-sm transition">Saved</Link>
              </>
            )}
          </nav>

          {/* Right side - auth buttons */}
          <div className="col-start-3 justify-self-end flex items-center space-x-4">
            {!user ? (
              <>
                <Link to="/login" className="px-3 py-2 rounded-md text-gray-700 hover:bg-gray-100 hover:shadow-sm transition">Sign In</Link>
                <Link to="/signup" className="px-4 py-2 rounded-md font-semibold text-white bg-gradient-to-br from-[#1e68d1] to-[#0b4fa1] shadow-md hover:from-[#1757b8] hover:to-[#083f83] transition">Get Started</Link>
              </>
            ) : (
              <div className="flex items-center space-x-3">
                <Link to="/profile" className="text-gray-600 hover:text-gray-900 flex items-center gap-2">
                  <User className="w-5 h-5" />
                  <span className="hidden sm:inline">Profile</span>
                </Link>
                <button onClick={() => signOut()} className="px-3 py-2 rounded-md text-gray-600 hover:bg-red-600 hover:text-white transition font-semibold">Sign Out</button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}