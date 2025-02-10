document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chatForm');
    const messageInput = document.getElementById('messageInput');
    const chatMessages = document.getElementById('chatMessages');

    // Auto-resize textarea
    messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });

    // Handle form submission
    chatForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const message = messageInput.value.trim();
        if (!message) return;

        // Add user message to chat
        addMessage(message, 'user');
        
        // Clear input
        messageInput.value = '';
        messageInput.style.height = 'auto';

        // Show loading indicator
        const loadingIndicator = addLoadingIndicator();

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });

            const data = await response.json();
            
            // Remove loading indicator
            loadingIndicator.remove();

            if (response.ok) {
                addMessage(data.response, 'bot');
            } else {
                addMessage('Sorry, I encountered an error. Please try again.', 'bot');
            }
        } catch (error) {
            console.error('Error:', error);
            loadingIndicator.remove();
            addMessage('Sorry, I encountered an error. Please try again.', 'bot');
        }

        // Scroll to bottom
        scrollToBottom();
    });

    function addMessage(content, type) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', `${type}-message`);
        
        const textContent = document.createElement('p');
        textContent.textContent = content;
        messageDiv.appendChild(textContent);
        
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }

    function addLoadingIndicator() {
        const loadingDiv = document.createElement('div');
        loadingDiv.classList.add('loading-indicator');
        
        const loadingDots = document.createElement('div');
        loadingDots.classList.add('loading-dots');
        
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('span');
            loadingDots.appendChild(dot);
        }
        
        loadingDiv.appendChild(loadingDots);
        chatMessages.appendChild(loadingDiv);
        scrollToBottom();
        
        return loadingDiv;
    }

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
});
