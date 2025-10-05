import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './hooks/useAuth';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { Header } from './components/layout/Header';
import { Footer } from './components/layout/Footer';

// Pages
import { Landing } from './pages/Landing';
import { Login } from './pages/Login';
import { Signup } from './pages/Signup';
import { Dashboard } from './pages/Dashboard';
import { TrialSearch } from './pages/TrialSearch';
import { Results } from './pages/Results';
import { SavedTrials } from './pages/SavedTrials';
import { Profile } from './pages/Profile';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <div className="flex flex-col min-h-screen">
            <Header />
            <main className="flex-1">
              <Routes>
                {/* Landing page handles its own spacing for fixed header */}
                <Route path="/" element={<Landing />} />
                
                {/* Auth pages with proper spacing */}
                <Route path="/login" element={
                  <div className="pt-16">
                    <Login />
                  </div>
                } />
                <Route path="/signup" element={
                  <div className="pt-16">
                    <Signup />
                  </div>
                } />

                {/* Protected Routes with proper spacing */}
                <Route element={<ProtectedRoute />}>
                  <Route path="/dashboard" element={
                    <div className="pt-16">
                      <Dashboard />
                    </div>
                  } />
                  <Route path="/search" element={
                    <div className="pt-16">
                      <TrialSearch />
                    </div>
                  } />
                  <Route path="/results" element={
                    <div className="pt-16">
                      <Results />
                    </div>
                  } />
                  <Route path="/saved" element={
                    <div className="pt-16">
                      <SavedTrials />
                    </div>
                  } />
                  <Route path="/profile" element={
                    <div className="pt-16">
                      <Profile />
                    </div>
                  } />
                </Route>

                {/* Fallback */}
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </main>
            <Footer />
          </div>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}
export default App;