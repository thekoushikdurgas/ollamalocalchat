document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chatForm');
    const messageInput = document.getElementById('messageInput');
    const chatMessages = document.getElementById('chatMessages');
    const modeButtons = document.querySelectorAll('.mode-button');

    let currentMode = 'chat'; // Default mode

    // Handle mode toggle
    modeButtons.forEach(button => {
        button.addEventListener('click', () => {
            modeButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            currentMode = button.dataset.mode;

            // Update placeholder based on mode
            messageInput.placeholder = currentMode === 'chat' 
                ? "What's on your mind?" 
                : "Enter your prompt for generation...";
        });
    });

    // Load previous messages
    loadMessages();

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
                body: JSON.stringify({ 
                    message: message,
                    mode: currentMode
                })
            });

            const data = await response.json();

            // Remove loading indicator
            loadingIndicator.remove();

            if (response.ok) {
                addMessage(data.response, 'bot', true);
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

    async function loadMessages() {
        try {
            const response = await fetch('/messages');
            const messages = await response.json();

            // Clear welcome message if there are previous messages
            if (messages.length > 0) {
                chatMessages.innerHTML = '';
            }

            messages.forEach(message => {
                addMessage(message.content, message.role, true);
            });

            scrollToBottom();
        } catch (error) {
            console.error('Error loading messages:', error);
        }
    }

    function addMessage(content, type, showActions = false) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', `${type}-message`);

        const textContent = document.createElement('p');
        textContent.textContent = content;
        messageDiv.appendChild(textContent);

        // Add action buttons for bot messages
        if (type === 'bot' && showActions) {
            const actionsDiv = document.createElement('div');
            actionsDiv.classList.add('message-actions');

            // Regenerate button
            const regenerateBtn = document.createElement('button');
            regenerateBtn.classList.add('action-button');
            regenerateBtn.innerHTML = '<i data-feather="refresh-cw"></i> Regenerate';
            regenerateBtn.addEventListener('click', async () => {
                const lastUserMessage = chatMessages.querySelector('.user-message:last-of-type');
                if (lastUserMessage) {
                    // Remove the current bot message
                    messageDiv.remove();

                    // Show loading indicator
                    const loadingIndicator = addLoadingIndicator();

                    try {
                        const response = await fetch('/chat', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({ message: lastUserMessage.querySelector('p').textContent })
                        });

                        const data = await response.json();
                        loadingIndicator.remove();

                        if (response.ok) {
                            addMessage(data.response, 'bot', true);
                        } else {
                            addMessage('Sorry, I encountered an error. Please try again.', 'bot');
                        }
                    } catch (error) {
                        console.error('Error:', error);
                        loadingIndicator.remove();
                        addMessage('Sorry, I encountered an error. Please try again.', 'bot');
                    }
                }
            });
            actionsDiv.appendChild(regenerateBtn);

            // Copy button
            const copyBtn = document.createElement('button');
            copyBtn.classList.add('action-button');
            copyBtn.innerHTML = '<i data-feather="copy"></i> Copy';
            copyBtn.addEventListener('click', () => {
                navigator.clipboard.writeText(content);
                copyBtn.innerHTML = '<i data-feather="check"></i> Copied';
                feather.replace();
                setTimeout(() => {
                    copyBtn.innerHTML = '<i data-feather="copy"></i> Copy';
                    feather.replace();
                }, 2000);
            });
            actionsDiv.appendChild(copyBtn);

            messageDiv.appendChild(actionsDiv);
        }

        chatMessages.appendChild(messageDiv);
        feather.replace();
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