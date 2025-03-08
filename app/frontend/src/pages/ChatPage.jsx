import { useState } from 'react';
import ApiService from '../services/api';
import { useUI } from '../context/UIContext';

function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { showError } = useUI();

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim()) return;

    const userMessage = {
      id: Date.now(),
      content: inputMessage,
      sender: 'user'
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await ApiService.sendChatMessage(inputMessage);
      console.log('Chat response:', response); // Debug log
      
      if (response.success) {
        setMessages(prev => [...prev, {
          id: Date.now() + 1,
          content: response.response || response.message,
          sender: 'assistant'
        }]);
      } else {
        throw new Error(response.error || 'Failed to get response');
      }
    } catch (error) {
      console.error('Chat error:', error);
      showError('Failed to send message: ' + error.message);
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        content: 'Sorry, there was an error processing your message.',
        sender: 'assistant'
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="h-[calc(100vh-64px)] flex bg-gray-100"> {/* Adjusted height for navbar */}
      {/* Sidebar */}
      <div className="w-80 bg-gray-800 text-white p-4 hidden md:block">
        <button 
          className="w-full bg-teal-500 hover:bg-teal-600 text-white rounded-md p-2 flex items-center justify-center mb-4"
          onClick={() => {/* handle new chat */}}
        >
          <span className="mr-2">+</span> New Chat
        </button>
        
        <div className="space-y-2">
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
        <div className="flex-1 overflow-y-auto p-4 max-w-4xl mx-auto w-full">
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
        <div className="border-t border-gray-200 p-4 bg-white">
          <div className="max-w-4xl mx-auto">
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
    </div>
  );
}

export default ChatPage; 