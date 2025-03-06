import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useUI } from '../context/UIContext';
import ApiService from '../services/api';

function ProfilePage() {
  const { user } = useAuth();
  const { showError } = useUI();
  const [isLoading, setIsLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [profile, setProfile] = useState({
    firstName: '',
    lastName: '',
    email: '',
    university: '',
    studentStatus: '',
    visaType: '',
    housingPreferences: {
      budget: '',
      roommates: false,
      location: ''
    }
  });

  useEffect(() => {
    let isMounted = true;

    const fetchProfile = async () => {
      try {
        const data = await ApiService.getProfile();
        if (isMounted) {
          setProfile({
            ...data,
            housingPreferences: data.housingPreferences || {
              budget: '',
              roommates: false,
              location: ''
            }
          });
        }
      } catch (error) {
        if (isMounted) {
          showError('Failed to load profile: ' + error.message);
          console.error('Profile fetch error:', error);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    fetchProfile();

    return () => {
      isMounted = false;
    };
  }, [showError]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await ApiService.updateProfile(profile);
      setIsEditing(false);
      showError('Profile updated successfully!');
    } catch (error) {
      showError('Failed to update profile: ' + error.message);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-teal-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white shadow rounded-lg">
          {/* Profile Header */}
          <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
            <div className="flex justify-between items-center">
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                Profile Information
              </h3>
              <button
                onClick={() => setIsEditing(!isEditing)}
                className="text-teal-500 hover:text-teal-600"
              >
                {isEditing ? 'Cancel' : 'Edit'}
              </button>
            </div>
          </div>

          {/* Profile Content */}
          <div className="px-4 py-5 sm:p-6">
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-1 gap-y-6 sm:grid-cols-2 sm:gap-x-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    First Name
                  </label>
                  <input
                    type="text"
                    value={profile.firstName}
                    onChange={(e) => setProfile({...profile, firstName: e.target.value})}
                    disabled={!isEditing}
                    className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Last Name
                  </label>
                  <input
                    type="text"
                    value={profile.lastName}
                    onChange={(e) => setProfile({...profile, lastName: e.target.value})}
                    disabled={!isEditing}
                    className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Email
                  </label>
                  <input
                    type="email"
                    value={profile.email}
                    disabled
                    className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 bg-gray-50"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    University
                  </label>
                  <input
                    type="text"
                    value={profile.university || ''}
                    onChange={(e) => setProfile({...profile, university: e.target.value})}
                    disabled={!isEditing}
                    className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Student Status
                  </label>
                  <select
                    value={profile.studentStatus || ''}
                    onChange={(e) => setProfile({...profile, studentStatus: e.target.value})}
                    disabled={!isEditing}
                    className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
                  >
                    <option value="">Select status</option>
                    <option value="incoming">Incoming Student</option>
                    <option value="current">Current Student</option>
                    <option value="graduating">Graduating Student</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Visa Type
                  </label>
                  <select
                    value={profile.visaType || ''}
                    onChange={(e) => setProfile({...profile, visaType: e.target.value})}
                    disabled={!isEditing}
                    className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
                  >
                    <option value="">Select visa type</option>
                    <option value="F1">F-1 Student</option>
                    <option value="J1">J-1 Exchange Visitor</option>
                    <option value="other">Other</option>
                  </select>
                </div>
              </div>

              {/* Housing Preferences Section */}
              <div className="mt-6">
                <h4 className="text-lg font-medium text-gray-900 mb-4">
                  Housing Preferences
                </h4>
                <div className="grid grid-cols-1 gap-y-6 sm:grid-cols-2 sm:gap-x-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Monthly Budget
                    </label>
                    <input
                      type="number"
                      value={profile.housingPreferences?.budget || ''}
                      onChange={(e) => setProfile({
                        ...profile,
                        housingPreferences: {
                          ...profile.housingPreferences,
                          budget: e.target.value
                        }
                      })}
                      disabled={!isEditing}
                      className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Location Preference
                    </label>
                    <input
                      type="text"
                      value={profile.housingPreferences?.location || ''}
                      onChange={(e) => setProfile({
                        ...profile,
                        housingPreferences: {
                          ...profile.housingPreferences,
                          location: e.target.value
                        }
                      })}
                      disabled={!isEditing}
                      className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
                    />
                  </div>
                </div>

                <div className="mt-4">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={profile.housingPreferences?.roommates || false}
                      onChange={(e) => setProfile({
                        ...profile,
                        housingPreferences: {
                          ...profile.housingPreferences,
                          roommates: e.target.checked
                        }
                      })}
                      disabled={!isEditing}
                      className="h-4 w-4 text-teal-500 focus:ring-teal-500 border-gray-300 rounded"
                    />
                    <span className="ml-2 text-sm text-gray-700">Open to roommates</span>
                  </label>
                </div>
              </div>

              {isEditing && (
                <div className="flex justify-end">
                  <button
                    type="submit"
                    className="bg-teal-500 text-white px-4 py-2 rounded-md hover:bg-teal-600"
                  >
                    Save Changes
                  </button>
                </div>
              )}
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ProfilePage;
