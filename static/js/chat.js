document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chatForm');
    let currentImageData = null;

    // Add image upload handler
    const imageInput = document.createElement('input');
    imageInput.type = 'file';
    imageInput.accept = 'image/*';
    imageInput.style.display = 'none';
    imageInput.addEventListener('change', handleImageUpload);
    document.body.appendChild(imageInput);

    function handleImageUpload(event) {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                currentImageData = e.target.result.split(',')[1]; // Get base64 data
                const preview = document.getElementById('imagePreview');
                if (preview) {
                    preview.src = e.target.result;
                    preview.style.display = 'block';
                }
            };
            reader.readAsDataURL(file);
        }
    }

    // Add image upload button to chat form
    const uploadButton = document.createElement('button');
    uploadButton.type = 'button';
    uploadButton.className = 'btn btn-secondary';
    uploadButton.innerHTML = '<i data-feather="image"></i>';
    uploadButton.onclick = () => imageInput.click();
    document.querySelector('.input-group').insertBefore(uploadButton, document.querySelector('.send-button'));

    // Fetch available models
    async function fetchModels() {
        try {
            const response = await fetch('/models');
            const models = await response.json();
            const modelSelect = document.getElementById('modelSelect');
            modelSelect.innerHTML = ''; // Clear existing options

            models.forEach(model => {
                const option = document.createElement('option');
                option.value = model.name;
                option.textContent = `${model.name} (${model.size})`;
                modelSelect.appendChild(option);
            });
        } catch (error) {
            console.error('Error fetching models:', error);
        }
    }

    // Fetch models on page load
    fetchModels();

    async function generateCode(prompt, suffix = '') {
        try {
            const response = await fetch('/generate-code', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    prompt: prompt,
                    suffix: suffix,
                    model: document.getElementById('modelSelect').value
                })
            });
            const data = await response.json();
            return data.response;
        } catch (error) {
            console.error('Error generating code:', error);
            throw error;
        }
    }
    const createModelBtn = document.getElementById('createModelBtn');
    const modelModal = document.getElementById('modelModal');
    const closeModal = document.getElementById('closeModal');
    const createModelSubmit = document.getElementById('createModelSubmit');
    const modelSelect = document.getElementById('modelSelect');

    createModelBtn.addEventListener('click', () => {
        modelModal.style.display = 'block';
    });

    closeModal.addEventListener('click', () => {
        modelModal.style.display = 'none';
    });

    createModelSubmit.addEventListener('click', async () => {
        const modelName = document.getElementById('modelName').value;
        const baseModel = document.getElementById('baseModel').value;
        const systemPrompt = document.getElementById('systemPrompt').value;

        try {
            const response = await fetch('/create-model', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    model_name: modelName,
                    base_model: baseModel,
                    system_prompt: systemPrompt
                })
            });

            const data = await response.json();
            if (response.ok) {
                // Add new model to select options
                const option = document.createElement('option');
                option.value = modelName;
                option.textContent = modelName;
                modelSelect.appendChild(option);
                modelSelect.value = modelName;
                modelModal.style.display = 'none';
            } else {
                alert('Error creating model: ' + data.error);
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to create model');
        }
    });
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
            let endpoint = currentMode === 'generate' ? '/generate' : '/chat';
            if (currentImageData) {
                endpoint = '/multimodal-chat';
            }
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    prompt: message,  // For generate endpoint
                    mode: currentMode,
                    model: document.getElementById('modelSelect').value,
                    image: currentImageData,
                    stream: endpoint !== '/multimodal-chat'  // Disable streaming for multimodal
                })
            });

            if (response.headers.get('content-type')?.includes('text/event-stream')) {
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let currentMessage = '';
                const messageDiv = addMessage('', 'bot', true);
                const textContent = messageDiv.querySelector('p');

                while (true) {
                    const {value, done} = await reader.read();
                    if (done) break;

                    const chunk = decoder.decode(value);
                    const lines = chunk.split('\n');

                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            const data = JSON.parse(line.slice(6));
                            currentMessage += data.response;
                            textContent.textContent = currentMessage;
                        }
                    }
                }
                return;
            }

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