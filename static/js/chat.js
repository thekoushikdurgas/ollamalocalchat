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

                // Create or update image preview
                let preview = document.getElementById('imagePreview');
                if (!preview) {
                    preview = document.createElement('img');
                    preview.id = 'imagePreview';
                    preview.className = 'image-preview';
                    document.querySelector('.chat-input-container').insertBefore(
                        preview, 
                        document.getElementById('chatForm')
                    );
                }
                preview.src = e.target.result;
                preview.style.display = 'block';

                // Add remove button
                let removeBtn = document.getElementById('removeImage');
                if (!removeBtn) {
                    removeBtn = document.createElement('button');
                    removeBtn.id = 'removeImage';
                    removeBtn.className = 'remove-image-btn';
                    removeBtn.innerHTML = '<i data-feather="x"></i>';
                    removeBtn.onclick = clearImageUpload;
                    preview.parentElement.appendChild(removeBtn);
                    feather.replace();
                }
            };
            reader.readAsDataURL(file);
        }
    }

    function clearImageUpload() {
        currentImageData = null;
        const preview = document.getElementById('imagePreview');
        const removeBtn = document.getElementById('removeImage');
        if (preview) preview.remove();
        if (removeBtn) removeBtn.remove();
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
            const data = await response.json();
            const modelSelect = document.getElementById('modelSelect');
            modelSelect.innerHTML = ''; // Clear existing options

            if (response.ok && !data.error) {
                data.forEach(model => {
                    const option = document.createElement('option');
                    option.value = model.name;
                    let modelText = model.name;
                    if (model.size) modelText += ` (${model.size})`;
                    if (model.family) modelText += ` - ${model.family}`;
                    option.textContent = modelText;
                    modelSelect.appendChild(option);
                });
            } else {
                const errorOption = document.createElement('option');
                errorOption.value = '';
                errorOption.textContent = data.error || 'Error loading models';
                errorOption.disabled = true;
                modelSelect.appendChild(errorOption);
                console.error('Model fetch error:', data.error);
            }
        } catch (error) {
            console.error('Error fetching models:', error);
            const modelSelect = document.getElementById('modelSelect');
            modelSelect.innerHTML = '<option disabled>Failed to load models</option>';
        }
    }

    // Refresh models list periodically
    setInterval(fetchModels, 30000); // Every 30 seconds

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
    const newChatBtn = document.querySelector('.new-chat-btn');
    const chatModal = document.getElementById('chatModal');
    const closeChatModal = document.getElementById('closeChatModal');
    const createChatBtn = document.getElementById('createChatBtn');

    createModelBtn.addEventListener('click', () => {
        modelModal.style.display = 'block';
    });

    closeModal.addEventListener('click', () => {
        modelModal.style.display = 'none';
    });

    const createModelSubmit = document.getElementById('createModelSubmit');
    const modelSelect = document.getElementById('modelSelect');

    function createProgressBar(digest) {
    const progressContainer = document.createElement('div');
    progressContainer.className = 'progress-container';
    progressContainer.innerHTML = `
        <div class="progress-label">Pulling ${digest}</div>
        <div class="progress">
            <div class="progress-bar" role="progressbar" style="width: 0%"></div>
        </div>
    `;
    return progressContainer;
}

async function trackPullProgress() {
    const progressArea = document.getElementById('pullProgress');
    const progressBars = {};

    while (true) {
        const response = await fetch('/pull-progress');
        const progress = await response.json();

        if (progress.status) {
            const statusDiv = document.createElement('div');
            statusDiv.textContent = progress.status;
            progressArea.appendChild(statusDiv);
            continue;
        }

        for (const [digest, info] of Object.entries(progress)) {
            if (!progressBars[digest] && info.total) {
                progressBars[digest] = createProgressBar(info.digest_short);
                progressArea.appendChild(progressBars[digest]);
            }

            if (info.completed && info.total) {
                const percent = (info.completed / info.total) * 100;
                const bar = progressBars[digest].querySelector('.progress-bar');
                bar.style.width = `${percent}%`;
                bar.textContent = `${Math.round(percent)}%`;
            }
        }

        await new Promise(resolve => setTimeout(resolve, 100));
    }
}

createModelSubmit.addEventListener('click', async () => {
        const modelName = document.getElementById('modelName').value;
        const baseModel = document.getElementById('baseModel').value;
        const systemPrompt = document.getElementById('systemPrompt').value;

        // Add progress area to modal
        const progressArea = document.createElement('div');
        progressArea.id = 'pullProgress';
        document.querySelector('.modal-content').appendChild(progressArea);

        // Start progress tracking
        const progressTracker = trackPullProgress();

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

    // New chat modal handlers
    newChatBtn.addEventListener('click', () => {
        chatModal.style.display = 'block';
    });

    closeChatModal.addEventListener('click', () => {
        chatModal.style.display = 'none';
    });

    createChatBtn.addEventListener('click', async () => {
        const chatName = document.getElementById('chatName').value;
        const baseModel = document.getElementById('chatBaseModel').value;
        const systemPrompt = document.getElementById('chatSystemPrompt').value;

        try {
            const response = await fetch('/create-chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: chatName,
                    base_model: baseModel,
                    system_prompt: systemPrompt
                })
            });

            const data = await response.json();
            if (response.ok) {
                // Add new chat to sidebar
                const conversationsList = document.querySelector('.conversations-list');
                const newChat = document.createElement('a');
                newChat.href = '#';
                newChat.className = 'nav-item';
                newChat.innerHTML = `
                    <i data-feather="message-square"></i>
                    ${chatName}
                `;
                conversationsList.insertBefore(newChat, conversationsList.firstChild);
                feather.replace();

                chatModal.style.display = 'none';
                // Clear chat messages
                document.getElementById('chatMessages').innerHTML = '';
                // Clear form
                document.getElementById('chatName').value = '';
                document.getElementById('chatSystemPrompt').value = '';
            } else {
                alert('Error creating chat: ' + data.error);
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to create chat');
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
            const formatSelect = document.getElementById('formatSelect'); // Added format selection
            const format = formatSelect ? formatSelect.value : null;     // Added format value
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
                    stream: endpoint !== '/multimodal-chat',  // Disable streaming for multimodal
                    format: format, // Added format to the request body
                    options: {
                        temperature: parseFloat(document.getElementById('temperature')?.value || 0.7),
                        top_p: parseFloat(document.getElementById('top_p')?.value || 0.9),
                        top_k: parseInt(document.getElementById('top_k')?.value || 40)
                    }
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

    async function checkProcessStatus() {
        try {
            const response = await fetch('/process-status');
            const data = await response.json();
            if (response.ok) {
                console.log('Process Status:', data);
                // Update UI with model status -  replace with your actual UI element
                document.getElementById('modelStatus').textContent = JSON.stringify(data, null, 2);
                return data;
            } else {
                console.error('Error:', data.error);
            }
        } catch (error) {
            console.error('Failed to check process status:', error);
        }
    }


    //Periodically check model status
    // Add comic analysis button
    const comicButton = document.createElement('button');
    comicButton.type = 'button';
    comicButton.className = 'btn btn-secondary';
    comicButton.innerHTML = '<i data-feather="smile"></i>';
    comicButton.title = 'Analyze XKCD Comic';
    comicButton.onclick = async () => {
        const comicNum = prompt('Enter XKCD comic number (leave empty for random):');

        // Add loading message
        const loadingMessage = addMessage('Analyzing comic...', 'bot');

        try {
            const response = await fetch('/analyze-comic', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ comic_num: comicNum })
            });

            const data = await response.json();
            if (response.ok) {
                loadingMessage.remove();
                const comicMessage = document.createElement('div');
                comicMessage.className = 'bot-message comic-analysis';
                comicMessage.innerHTML = `
                    <h3>XKCD #${data.comic_num}: ${data.title}</h3>
                    <img src="${data.image_url}" alt="${data.alt}" style="max-width: 100%; margin: 10px 0;">
                    <p><strong>Alt text:</strong> ${data.alt}</p>
                    <p><strong>Link:</strong> <a href="${data.link}" target="_blank">${data.link}</a></p>
                    <p><strong>AI Explanation:</strong></p>
                    <p>${data.explanation}</p>
                `;
                chatMessages.appendChild(comicMessage);
                scrollToBottom();
            } else {
                loadingMessage.textContent = 'Error: ' + (data.error || 'Failed to analyze comic');
            }
        } catch (error) {
            loadingMessage.textContent = 'Error: ' + error.message;
        }
    };

    document.querySelector('.input-group').insertBefore(comicButton, document.querySelector('.send-button'));
    feather.replace();

    setInterval(checkProcessStatus, 5000); // Check every 5 seconds

});

function appendMessage(message, isUser = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = isUser ? 'user-message' : 'bot-message';

    // Try to parse as JSON for structured outputs
    try {
        const jsonData = JSON.parse(message);
        const pre = document.createElement('pre');
        pre.className = 'structured-output';
        pre.textContent = JSON.stringify(jsonData, null, 2);
        messageDiv.appendChild(pre);
    } catch (e) {
        messageDiv.textContent = message;
    }

    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}