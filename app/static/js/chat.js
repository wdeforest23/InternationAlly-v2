document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');
    const clearButton = document.getElementById('clear-chat');

    function addMessage(content, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `${type}-message`;
        messageDiv.textContent = typeof content === 'string' ? content : JSON.stringify(content);
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function showTypingIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        indicator.id = 'typing-indicator';
        indicator.innerHTML = '<span></span><span></span><span></span>';
        chatMessages.appendChild(indicator);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function removeTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }

    chatForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const message = userInput.value.trim();
        if (!message) return;

        // Add user message
        addMessage(message, 'user');
        userInput.value = '';

        // Show typing indicator
        showTypingIndicator();

        try {
            console.log("Sending message:", message);  // Debug log
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: message })
            });

            console.log("Raw response:", response);  // Debug log
            const data = await response.json();
            console.log("Response data:", data);  // Debug log
            
            removeTypingIndicator();

            if (data.success) {
                addMessage(data.response, 'assistant');
            } else {
                const errorMessage = data.error || 'Unknown error';
                console.error("Error details:", data);  // Debug log
                addMessage(`Sorry, I encountered an error: ${errorMessage}`, 'system');
            }
        } catch (error) {
            console.error("Full error:", error);  // Debug log
            removeTypingIndicator();
            addMessage('Sorry, I encountered an error. Please try again.', 'system');
        }
    });

    clearButton.addEventListener('click', async function() {
        try {
            await fetch('/clear', { method: 'POST' });
            chatMessages.innerHTML = `
                <div class="system-message">
                    Welcome to InternationAlly! I'm here to help you with:
                    <ul class="list-disc ml-4 mt-2">
                        <li>Information about UChicago and student life</li>
                        <li>Housing options near campus</li>
                        <li>Local restaurants and places of interest</li>
                        <li>Visa and immigration questions</li>
                    </ul>
                </div>
            `;
        } catch (error) {
            addMessage('Error clearing chat history.', 'system');
            console.error('Error:', error);
        }
    });
}); 