import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUI } from '../context/UIContext';
import ApiService from '../services/api';

function OnboardingPage() {
  const { showError, startLoading, stopLoading } = useUI();
  const [step, setStep] = useState(1);
  const [userData, setUserData] = useState({
    university: '',
    studentStatus: '',
    interests: [],
    visaType: '',
    housingPreferences: {
      budget: '',
      roommates: false,
      location: '',
    }
  });
  const navigate = useNavigate();

  const handleNext = () => {
    if (step < 3) {
      setStep(step + 1);
    } else {
      handleSubmit();
    }
  };

  const handleBack = () => {
    if (step > 1) {
      setStep(step - 1);
    }
  };

  const handleSubmit = async () => {
    startLoading();
    try {
      await ApiService.updateProfile(userData);
      navigate('/chat');
    } catch (error) {
      showError('Failed to save preferences: ' + error.message);
    } finally {
      stopLoading();
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full mx-auto">
        {/* Progress indicator */}
        <div className="mb-8">
          <h2 className="text-center text-3xl font-bold text-gray-900 mb-4">
            Complete Your Profile
          </h2>
          <div className="flex justify-between items-center">
            {[1, 2, 3].map((num) => (
              <div key={num} className="flex flex-col items-center">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center ${
                    step >= num ? 'bg-teal-500 text-white' : 'bg-gray-200'
                  }`}
                >
                  {num}
                </div>
                <span className="text-sm mt-1">
                  {num === 1 ? 'Basic Info' : num === 2 ? 'Visa' : 'Housing'}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Form Content */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          {step === 1 && (
            <div className="space-y-4">
              <h3 className="text-xl font-semibold mb-4">Tell us about yourself</h3>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  University
                </label>
                <input
                  type="text"
                  value={userData.university}
                  onChange={(e) => setUserData({...userData, university: e.target.value})}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT"
                  placeholder="Enter your university"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Student Status
                </label>
                <select
                  value={userData.studentStatus}
                  onChange={(e) => setUserData({...userData, studentStatus: e.target.value})}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT"
                >
                  <option value="">Select status</option>
                  <option value="incoming">Incoming Student</option>
                  <option value="current">Current Student</option>
                  <option value="graduating">Graduating Student</option>
                </select>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <h3 className="text-xl font-semibold mb-4">Visa Information</h3>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Visa Type
                </label>
                <select
                  value={userData.visaType}
                  onChange={(e) => setUserData({...userData, visaType: e.target.value})}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT"
                >
                  <option value="">Select visa type</option>
                  <option value="F1">F-1 Student</option>
                  <option value="J1">J-1 Exchange Visitor</option>
                  <option value="other">Other</option>
                </select>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-4">
              <h3 className="text-xl font-semibold mb-4">Housing Preferences</h3>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Monthly Budget (USD)
                </label>
                <input
                  type="number"
                  value={userData.housingPreferences.budget}
                  onChange={(e) => setUserData({
                    ...userData,
                    housingPreferences: {
                      ...userData.housingPreferences,
                      budget: e.target.value
                    }
                  })}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT"
                  placeholder="Enter your monthly budget"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Preferred Location
                </label>
                <input
                  type="text"
                  value={userData.housingPreferences.location}
                  onChange={(e) => setUserData({
                    ...userData,
                    housingPreferences: {
                      ...userData.housingPreferences,
                      location: e.target.value
                    }
                  })}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT"
                  placeholder="e.g., Near campus, Downtown"
                />
              </div>
              <div className="flex items-center mt-4">
                <input
                  type="checkbox"
                  id="roommates"
                  checked={userData.housingPreferences.roommates}
                  onChange={(e) => setUserData({
                    ...userData,
                    housingPreferences: {
                      ...userData.housingPreferences,
                      roommates: e.target.checked
                    }
                  })}
                  className="h-4 w-4 text-primary-DEFAULT focus:ring-primary-DEFAULT border-gray-300 rounded"
                />
                <label htmlFor="roommates" className="ml-2 block text-sm text-gray-700">
                  Open to having roommates
                </label>
              </div>
            </div>
          )}
        </div>

        {/* Navigation Buttons */}
        <div className="flex justify-between mt-6">
          {step > 1 && (
            <button
              onClick={handleBack}
              className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900"
            >
              Back
            </button>
          )}
          <button
            onClick={handleNext}
            className="ml-auto px-6 py-2 bg-teal-500 text-white rounded-md hover:bg-teal-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500"
          >
            {step === 3 ? 'Finish' : 'Next'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default OnboardingPage;
