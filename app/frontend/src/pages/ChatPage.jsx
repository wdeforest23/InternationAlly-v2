import { useState } from 'react';
import ApiService from '../services/api';

function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim()) return;

    const newMessage = {
      id: Date.now(),
      content: inputMessage,
      sender: 'user'
    };

    setMessages(prev => [...prev, newMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await ApiService.sendChatMessage(inputMessage);
      setMessages(prev => [...prev, {
        id: Date.now(),
        content: response.response || response.message,
        sender: 'assistant'
      }]);
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, {
        id: Date.now(),
        content: 'Sorry, there was an error processing your message.',
        sender: 'assistant'
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <div className="w-64 bg-gray-800 text-white p-4 hidden md:block">
        <div className="mb-4">
          <button className="w-full bg-teal-500 hover:bg-teal-600 text-white rounded-md p-2 flex items-center justify-center">
            <span className="mr-2">+</span> New Chat
          </button>
        </div>
        <div className="space-y-2">
          {/* Chat history would go here */}
          <div className="p-2 hover:bg-gray-700 rounded cursor-pointer">
            Previous Chat 1
          </div>
          <div className="p-2 hover:bg-gray-700 rounded cursor-pointer">
            Previous Chat 2
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Chat Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${
                message.sender === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              <div
                className={`max-w-3xl rounded-lg p-4 ${
                  message.sender === 'user'
                    ? 'bg-teal-500 text-white'
                    : 'bg-white text-gray-800'
                } shadow`}
              >
                {message.content}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-white text-gray-800 rounded-lg p-4 shadow">
                <div className="animate-pulse">Typing...</div>
              </div>
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="border-t border-gray-200 p-4">
          <form onSubmit={handleSendMessage} className="flex space-x-4">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Type your message here..."
              className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500"
            />
            <button
              type="submit"
              disabled={isLoading}
              className="bg-teal-500 text-white px-6 py-2 rounded-lg hover:bg-teal-600 disabled:opacity-50"
            >
              Send
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default ChatPage; 