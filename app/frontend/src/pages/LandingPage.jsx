import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const cultureFacts = [
  "Americans often greet each other with 'How are you?' as a greeting, not expecting a detailed response!",
  "Tipping 15-20% is customary in U.S. restaurants",
  "In the U.S., it's common to make small talk with strangers",
  "Americans typically maintain a 'personal space' bubble of about 2-3 feet",
  "It's normal to address professors by their first name in many U.S. universities",
  "Americans often eat dinner between 6:00-8:00 PM",
  "Making eye contact during conversations is considered respectful"
];

function LandingPage() {
  const [fact, setFact] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const today = new Date().getDate();
    setFact(cultureFacts[today % cultureFacts.length]);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-12">
        <div className="text-center">
          <h1 className="text-4xl tracking-tight font-extrabold text-gray-900 sm:text-5xl md:text-6xl">
            <span className="block">Your Guide to</span>
            <span className="block text-primary-DEFAULT">Student Life in the U.S.</span>
          </h1>
          <p className="mt-3 max-w-md mx-auto text-base text-gray-500 sm:text-lg md:mt-5 md:text-xl md:max-w-3xl">
            Get personalized help with visas, housing, and campus life from your AI companion
          </p>
          <div className="mt-8 flex justify-center">
            <button
              onClick={() => navigate('/chat')}
              className="bg-teal-500 hover:bg-teal-600 text-white px-6 py-4 rounded-md text-lg font-bold transition-colors"
            >
              Start Chatting
            </button>
          </div>
        </div>
      </div>

      {/* Culture Fact Card */}
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow-lg p-6 border border-gray-100">
          <h2 className="text-xl font-semibold text-primary-DEFAULT flex items-center">
            <span className="mr-2">🌎</span>
            Today's U.S. Culture Fact
          </h2>
          <p className="mt-2 text-gray-600">{fact}</p>
        </div>
      </div>

      {/* Categories Grid */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {[
            {
              title: 'Visa & Immigration',
              description: 'Get help with F-1 visa requirements and maintaining status',
              icon: '🛂'
            },
            {
              title: 'Housing',
              description: 'Find apartments and understand rental processes',
              icon: '🏠'
            },
            {
              title: 'Campus Life',
              description: 'Learn about student life and resources',
              icon: '🎓'
            }
          ].map((category) => (
            <div
              key={category.title}
              onClick={() => navigate('/chat')}
              className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow cursor-pointer transform transition-transform duration-200 hover:scale-105"
            >
              <div className="text-3xl mb-3">{category.icon}</div>
              <h3 className="text-lg font-medium text-gray-900">{category.title}</h3>
              <p className="mt-2 text-gray-600">{category.description}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default LandingPage;
