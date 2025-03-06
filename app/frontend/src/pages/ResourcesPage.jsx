import { useState } from 'react';
import { Link } from 'react-router-dom';

function ResourcesPage() {
  const [activeCategory, setActiveCategory] = useState('all');

  const resources = {
    visa: [
      {
        title: 'F-1 Visa Guide',
        description: 'Complete guide to maintaining F-1 student status',
        icon: '📝',
        link: '/resources/f1-guide',
        tags: ['visa', 'important']
      },
      {
        title: 'OPT/CPT Information',
        description: 'Understanding work authorization options for students',
        icon: '💼',
        link: '/resources/work-auth',
        tags: ['visa', 'work']
      }
    ],
    housing: [
      {
        title: 'Housing Search Guide',
        description: 'Tips for finding and securing student housing',
        icon: '🏠',
        link: '/resources/housing-guide',
        tags: ['housing']
      },
      {
        title: 'Lease Understanding',
        description: 'Understanding US rental agreements and terms',
        icon: '📄',
        link: '/resources/lease-guide',
        tags: ['housing', 'legal']
      }
    ],
    academic: [
      {
        title: 'US Academic System',
        description: 'Understanding GPA, credit hours, and academic expectations',
        icon: '📚',
        link: '/resources/academic-guide',
        tags: ['academic']
      },
      {
        title: 'Academic Writing',
        description: 'Guide to academic writing in US universities',
        icon: '✍️',
        link: '/resources/writing-guide',
        tags: ['academic', 'writing']
      }
    ],
    cultural: [
      {
        title: 'Cultural Adjustment',
        description: 'Tips for adapting to life in the United States',
        icon: '🌎',
        link: '/resources/cultural-guide',
        tags: ['culture']
      },
      {
        title: 'American Customs',
        description: 'Understanding American social norms and customs',
        icon: '🤝',
        link: '/resources/customs-guide',
        tags: ['culture']
      }
    ]
  };

  const categories = [
    { id: 'all', name: 'All Resources', icon: '📚' },
    { id: 'visa', name: 'Visa & Immigration', icon: '🛂' },
    { id: 'housing', name: 'Housing', icon: '🏠' },
    { id: 'academic', name: 'Academic', icon: '📝' },
    { id: 'cultural', name: 'Cultural', icon: '🌎' }
  ];

  const getAllResources = () => {
    if (activeCategory === 'all') {
      return Object.values(resources).flat();
    }
    return resources[activeCategory] || [];
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-3xl font-bold text-gray-900">
            Student Resources
          </h1>
          <p className="mt-2 text-lg text-gray-600">
            Helpful guides and information for international students
          </p>
        </div>

        {/* Category Tabs */}
        <div className="flex flex-wrap justify-center gap-4 mb-8">
          {categories.map((category) => (
            <button
              key={category.id}
              onClick={() => setActiveCategory(category.id)}
              className={`px-4 py-2 rounded-full flex items-center space-x-2 ${
                activeCategory === category.id
                  ? 'bg-primary-DEFAULT text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              } transition-colors duration-200`}
            >
              <span>{category.icon}</span>
              <span>{category.name}</span>
            </button>
          ))}
        </div>

        {/* Resource Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {getAllResources().map((resource, index) => (
            <div
              key={index}
              className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200"
            >
              <div className="p-6">
                <div className="text-3xl mb-4">{resource.icon}</div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  {resource.title}
                </h3>
                <p className="text-gray-600 mb-4">
                  {resource.description}
                </p>
                <div className="flex flex-wrap gap-2 mb-4">
                  {resource.tags.map((tag, tagIndex) => (
                    <span
                      key={tagIndex}
                      className="px-2 py-1 bg-gray-100 text-gray-600 rounded-full text-sm"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
                <Link
                  to={resource.link}
                  className="text-primary-DEFAULT hover:text-primary-dark font-medium"
                >
                  Learn more →
                </Link>
              </div>
            </div>
          ))}
        </div>

        {/* Quick Help Section */}
        <div className="mt-12 bg-white rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            Need Immediate Help?
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Link
              to="/chat"
              className="flex items-center p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <span className="text-2xl mr-3">💬</span>
              <div>
                <h3 className="font-medium text-gray-900">Chat with AI Assistant</h3>
                <p className="text-sm text-gray-600">Get immediate answers to your questions</p>
              </div>
            </Link>
            <a
              href="mailto:support@internationally.com"
              className="flex items-center p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <span className="text-2xl mr-3">📧</span>
              <div>
                <h3 className="font-medium text-gray-900">Contact Support</h3>
                <p className="text-sm text-gray-600">Email us for personalized assistance</p>
              </div>
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ResourcesPage;
