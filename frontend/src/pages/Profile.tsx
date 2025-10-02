import { useAuth } from '../hooks/useAuth';
import { User, Mail, UserCheck, Calendar } from 'lucide-react';

export function Profile() {
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-8">
            <div className="flex items-center space-x-4 mb-8">
              <div className="w-16 h-16 bg-primary-blue bg-opacity-10 rounded-full flex items-center justify-center">
                <User className="w-8 h-8 text-primary-blue" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">User Profile</h1>
                <p className="text-gray-600">Manage your account information</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div className="flex items-center space-x-3 p-4 bg-gray-50 rounded-lg">
                  <Mail className="w-5 h-5 text-gray-400" />
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Email</label>
                    <p className="text-gray-900">{user?.email || 'Not available'}</p>
                  </div>
                </div>

                <div className="flex items-center space-x-3 p-4 bg-gray-50 rounded-lg">
                  <UserCheck className="w-5 h-5 text-gray-400" />
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Role</label>
                    <p className="text-gray-900 capitalize">
                      {user?.user_metadata?.role || user?.app_metadata?.role || 'Patient'}
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-3 p-4 bg-gray-50 rounded-lg">
                  <User className="w-5 h-5 text-gray-400" />
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Full Name</label>
                    <p className="text-gray-900">
                      {user?.user_metadata?.full_name || user?.user_metadata?.fullName || 'Not set'}
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-3 p-4 bg-gray-50 rounded-lg">
                  <Calendar className="w-5 h-5 text-gray-400" />
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Member Since</label>
                    <p className="text-gray-900">
                      {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'Not available'}
                    </p>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <div className="p-6 bg-blue-50 rounded-lg">
                  <h3 className="text-lg font-semibold text-blue-900 mb-2">Account Status</h3>
                  <div className="flex items-center space-x-2">
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                    <span className="text-blue-800">Active</span>
                  </div>
                  <p className="text-blue-700 text-sm mt-2">
                    Your account is active and ready to search for clinical trials.
                  </p>
                </div>

                <div className="p-6 bg-gray-50 rounded-lg">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Quick Actions</h3>
                  <div className="space-y-2">
                    <button className="w-full text-left px-4 py-2 text-primary-blue hover:bg-blue-50 rounded-md transition-colors">
                      Update Profile Information
                    </button>
                    <button className="w-full text-left px-4 py-2 text-primary-blue hover:bg-blue-50 rounded-md transition-colors">
                      Change Password
                    </button>
                    <button className="w-full text-left px-4 py-2 text-primary-blue hover:bg-blue-50 rounded-md transition-colors">
                      Download My Data
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-8 pt-6 border-t border-gray-200">
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <h4 className="text-yellow-800 font-medium mb-1">Privacy & Security</h4>
                <p className="text-yellow-700 text-sm">
                  Your personal information is encrypted and secure. We never share your medical data without your explicit consent.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}