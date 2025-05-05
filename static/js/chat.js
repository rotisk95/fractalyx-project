/**
 * Simple chat functionality for Fractalyx
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing simple chat - updated version with error handling');
    
    // Debug environment
    console.log('Project ID from DOM:', document.getElementById('projectData')?.getAttribute('data-project-id'));
    
    // Add mutation observer to debug DOM changes
    const chatContainer = document.getElementById('chatMessages');
    if (chatContainer) {
        console.log('Setting up mutation observer for chatMessages container');
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList') {
                    if (mutation.addedNodes.length > 0) {
                        console.log('Elements added to chat container:', mutation.addedNodes.length);
                    }
                    if (mutation.removedNodes.length > 0) {
                        console.log('Elements removed from chat container:', mutation.removedNodes.length);
                    }
                }
            });
        });
        
        observer.observe(chatContainer, { childList: true, subtree: true });
    }
    
    // Set up image upload preview
    const imageUpload = document.getElementById('imageUpload');
    if (imageUpload) {
        imageUpload.addEventListener('change', function() {
            console.log('Image upload changed');
            if (this.files && this.files[0]) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const previewContainer = document.getElementById('imagePreviewContainer');
                    const preview = document.getElementById('imagePreview');
                    if (preview && previewContainer) {
                        preview.src = e.target.result;
                        previewContainer.classList.remove('d-none');
                    }
                };
                reader.readAsDataURL(this.files[0]);
            }
        });
    }
    
    // Set up clear image button
    const clearImageBtn = document.getElementById('clearImage');
    if (clearImageBtn) {
        clearImageBtn.addEventListener('click', function() {
            const previewContainer = document.getElementById('imagePreviewContainer');
            const imageUpload = document.getElementById('imageUpload');
            if (previewContainer) {
                previewContainer.classList.add('d-none');
            }
            if (imageUpload) {
                imageUpload.value = '';
            }
        });
    }
    
    // Check if we have an active conversation in the DOM
    const conversationItems = document.querySelectorAll('.conversation-item');
    if (conversationItems.length > 0) {
        const activeItem = document.querySelector('.conversation-item.active');
        if (activeItem) {
            // We already have an active conversation, load it
            const conversationId = parseInt(activeItem.getAttribute('data-id'));
            console.log('Found active conversation:', conversationId);
            activeConversationId = conversationId;
            loadConversation(conversationId);
        } else {
            // No active conversation, but we have conversations, load the first one
            const firstId = parseInt(conversationItems[0].getAttribute('data-id'));
            console.log('Loading first conversation:', firstId);
            activeConversationId = firstId;
            loadConversation(firstId);
        }
    } else {
        // No conversations at all, create one
        console.log('No conversations found, creating new one');
        createConversation();
    }
    
    // Set up the chat form submission
    const chatForm = document.getElementById('chatForm');
    if (chatForm) {
        console.log('Chat form found, setting up submit handler');
        chatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            console.log('Form submitted, sending message...');
            sendMessage();
            return false;
        });
    } else {
        console.error('Chat form not found!');
    }
    
    // Set up new conversation button
    const newConversationBtn = document.getElementById('newConversation');
    if (newConversationBtn) {
        console.log('New conversation button found, setting up click handler');
        newConversationBtn.addEventListener('click', function() {
            console.log('New conversation button clicked');
            createConversation();
        });
    } else {
        console.error('New conversation button not found!');
    }
});

function loadConversation(conversationId) {
    if (!conversationId) return;
    
    const chatContainer = document.getElementById('chatMessages');
    if (!chatContainer) {
        console.error('Chat container not found!');
        return;
    }
    
    // Add loading indicator
    chatContainer.innerHTML = '<div id="chat-loading" class="text-center p-4"><div class="spinner-border text-primary" role="status"></div><p class="mt-2">Loading messages...</p></div>';
    
    console.log(`Fetching messages for conversation ${conversationId}`);
    fetch(`/api/conversations/${conversationId}/messages`)
        .then(response => {
            console.log('Message fetch response status:', response.status);
            if (!response.ok) {
                throw new Error('Network response was not ok ' + response.statusText);
            }
            return response.json();
        })
        .then(data => {
            console.log('Message data received:', data);
            
            // Remove loading indicator
            const loadingElement = document.getElementById('chat-loading');
            if (loadingElement) {
                loadingElement.remove();
            }
            
            if (data.messages && data.messages.length > 0) {
                console.log(`Found ${data.messages.length} messages to display`);
                
                // Sort messages by timestamp if needed
                data.messages.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
                
                // Clear any previous messages to be safe
                while (chatContainer.firstChild) {
                    chatContainer.removeChild(chatContainer.firstChild);
                }
                
                // Display all messages with forEach loop
                data.messages.forEach((msg, index) => {
                    appendMessageToChat(msg);
                });
            } else {
                chatContainer.innerHTML = '<div class="text-center p-4"><p>No messages yet. Start a conversation!</p></div>';
            }
        })
        .catch(error => {
            console.error('Fetch error:', error);
            chatContainer.innerHTML = `<div class="alert alert-danger">Failed to load messages: ${error.message}</div>`;
        });
}

function appendMessageToChat(message) {
    const chatContainer = document.getElementById('chatMessages');
    if (!chatContainer) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = message.is_user ? 'chat-message user-message' : 'chat-message agent-message';
    
    let messageContent = `
        <div class="message-header">
            <span class="message-sender">${message.is_user ? 'You' : (message.agent_name || 'Agent')}</span>
            <span class="message-time">${new Date(message.timestamp).toLocaleString()}</span>
        </div>
        <div class="message-content">
            ${message.content ? message.content.replace(/\n/g, '<br>') : ''}
        </div>
    `;
    
    if (message.has_image && message.image_path) {
        messageContent += `
            <div class="message-image mt-2">
                <img src="${message.image_path}" class="img-fluid rounded" alt="Uploaded image">
            </div>
        `;
    }
    
    messageDiv.innerHTML = messageContent;
    chatContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Store the active conversation ID
let activeConversationId = null;

/**
 * Create a new conversation
 */
function createConversation() {
    console.log('Creating new conversation');
    
    // Get project ID from the DOM, defaulting to 1 if not found
    const projectDataElement = document.getElementById('projectData');
    let projectId = 1; // Default value
    
    if (projectDataElement) {
        const dataProjectId = projectDataElement.getAttribute('data-project-id');
        if (dataProjectId && dataProjectId !== 'null') {
            projectId = parseInt(dataProjectId);
        }
    }
    console.log('Using project ID:', projectId);
    
    fetch('/api/conversations', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            project_id: projectId
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Conversation created:', data);
        activeConversationId = data.id;
        
        // Clear chat messages
        const chatContainer = document.getElementById('chatMessages');
        if (chatContainer) {
            chatContainer.innerHTML = '';
        }
        
        // Update the list of conversations
        updateConversationsList();
    })
    .catch(error => {
        console.error('Error creating conversation:', error);
        displayAlert('Could not create conversation. Please try again.', 'danger');
    });
}

/**
 * Send a message to the active conversation
 */
function sendMessage() {
    if (!activeConversationId) {
        displayAlert('No active conversation. Please refresh the page.', 'warning');
        return;
    }
    
    const messageInput = document.getElementById('userMessage');
    const message = messageInput.value.trim();
    
    if (!message) {
        console.log('Empty message, not sending');
        return; // Don't send empty messages
    }
    
    console.log(`Preparing to send message to conversation ${activeConversationId}:`, message);
    
    // Clear any 'no messages' placeholder if present
    const chatContainer = document.getElementById('chatMessages');
    if (!chatContainer) {
        console.error('Chat container not found, cannot send message');
        displayAlert('Unable to display messages. Please refresh the page.', 'danger');
        return;
    }
    
    const noMessagesPlaceholder = chatContainer.querySelector('.text-center.p-5');
    if (noMessagesPlaceholder) {
        console.log('Removing empty conversation placeholder');
        noMessagesPlaceholder.remove();
    }
    
    // Display user message immediately in UI
    console.log('Displaying user message in UI');
    displayMessage(message, true);
    
    // Clear input
    messageInput.value = '';
    messageInput.focus();
    
    // Clear image preview if present
    const previewContainer = document.getElementById('imagePreviewContainer');
    if (previewContainer && !previewContainer.classList.contains('d-none')) {
        previewContainer.classList.add('d-none');
    }
    
    // Show typing indicator
    console.log('Showing typing indicator');
    displayTypingIndicator();
    
    // Get file if present
    const imageInput = document.getElementById('imageUpload');
    let formData = new FormData();
    formData.append('message', message);
    
    if (imageInput && imageInput.files.length > 0) {
        console.log('Adding image to message');
        formData.append('image', imageInput.files[0]);
        // Clear the file input after use
        imageInput.value = '';
    }
    
    // Disable submit button during request
    const submitButton = document.querySelector('#chatForm button[type="submit"]');
    if (submitButton) {
        submitButton.disabled = true;
        submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>';
    }
    
    console.log('Sending API request to server');
    fetch(`/api/conversations/${activeConversationId}/messages`, {
        method: 'POST',
        body: formData
    })
    .then(response => {
        console.log('Received response with status:', response.status);
        if (!response.ok) {
            throw new Error(`Server responded with status ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Parsed response data:', data);
        
        // Hide typing indicator
        hideTypingIndicator();
        
        if (data.success) {
            console.log('Message sent successfully, displaying agent response');
            // Display agent response
            displayMessage(data.response, false, data.agent_name);
            
            // Update conversations list if needed
            if (data.conversation_updated) {
                updateConversationsList();
            }
            
            // Ensure we scroll to the bottom after new content is added
            if (chatContainer) {
                console.log('Scrolling chat to bottom');
                setTimeout(() => {
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                }, 100);
            }
        } else {
            console.error('API reported error:', data.error);
            throw new Error(data.error || 'Unknown error');
        }
    })
    .catch(error => {
        console.error('Error sending message:', error);
        hideTypingIndicator();
        displayAlert('Failed to send message. Please try again.', 'danger');
    })
    .finally(() => {
        // Re-enable submit button
        if (submitButton) {
            submitButton.disabled = false;
            submitButton.innerHTML = '<i class="bi bi-send"></i>';
        }
    });
}

/**
 * Display a message in the chat container
 */
function displayMessage(message, isUser, agentName = null) {
    console.log(`Displaying ${isUser ? 'user' : 'agent'} message:`, { message, agentName });
    
    const chatContainer = document.getElementById('chatMessages');
    if (!chatContainer) {
        console.error('Chat container not found!');
        displayAlert('Chat container not found. Please refresh the page.', 'danger');
        return;
    }
    
    // Make sure we have a message to display
    if (!message) {
        console.error('Attempted to display empty message');
        return;
    }
    
    // Ensure the container is properly set up for messages
    if (chatContainer.style.display !== 'flex') {
        console.log('Setting chat container to flex display');
        chatContainer.style.display = 'flex';
        chatContainer.style.flexDirection = 'column';
        chatContainer.style.maxHeight = '70vh';
        chatContainer.style.overflowY = 'auto';
    }
    
    // Remove any placeholders
    const placeholders = chatContainer.querySelectorAll('.text-center.p-5');
    if (placeholders.length > 0) {
        console.log('Removing', placeholders.length, 'placeholder elements');
        placeholders.forEach(el => el.remove());
    }
    
    // Check if we need a message wrapper for this conversation
    let messagesWrapper = chatContainer.querySelector('.messages-wrapper');
    if (!messagesWrapper) {
        console.log('Creating messages wrapper container');
        messagesWrapper = document.createElement('div');
        messagesWrapper.className = 'messages-wrapper w-100';
        messagesWrapper.style.display = 'flex';
        messagesWrapper.style.flexDirection = 'column';
        chatContainer.appendChild(messagesWrapper);
    }
    
    // Create the message row container for proper alignment
    const messageRow = document.createElement('div');
    messageRow.className = `message-row d-flex ${isUser ? 'justify-content-end' : 'justify-content-start'}`;
    messageRow.style.width = '100%';
    messageRow.style.marginBottom = '10px';
    
    // Create the message bubble element
    const messageBubble = document.createElement('div');
    messageBubble.className = `message-bubble ${isUser ? 'user-message' : 'agent-message'}`;
    messageBubble.style.maxWidth = '80%';
    messageBubble.style.wordBreak = 'break-word';
    
    // Create the message content using CSS classes
    if (isUser) {
        messageBubble.innerHTML = `
            <div class="message-content user">
                <div class="message-text">${formatText(message)}</div>
                <div class="message-meta">You</div>
            </div>
        `;
    } else {
        messageBubble.innerHTML = `
            <div class="message-content agent">
                <div class="message-header">
                    <span class="agent-name">${agentName || 'Fractal Node'}</span>
                </div>
                <div class="message-text">${formatText(message)}</div>
            </div>
        `;
    }
    
    // Build the DOM structure
    messageRow.appendChild(messageBubble);
    messagesWrapper.appendChild(messageRow);
    
    // Log DOM state for debugging
    console.log('Message added to DOM, row count:', messagesWrapper.childElementCount);
    
    // Force layout recalculation
    void chatContainer.offsetHeight;
    
    // Scroll to bottom with a small delay to ensure rendering is complete
    setTimeout(() => {
        chatContainer.scrollTop = chatContainer.scrollHeight;
        console.log('Scrolled to bottom, height:', chatContainer.scrollHeight);
    }, 100);
}

/**
 * Format message text (handle links, line breaks)
 */
function formatText(text) {
    // Convert line breaks to <br>
    text = text.replace(/\n/g, '<br>');
    
    // Make URLs clickable
    text = text.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
    
    return text;
}

/**
 * Display typing indicator
 */
function displayTypingIndicator() {
    console.log('Displaying typing indicator');
    
    const chatContainer = document.getElementById('chatMessages');
    if (!chatContainer) {
        console.error('Chat container not found for typing indicator');
        return;
    }
    
    // If already exists, don't add again
    if (document.getElementById('typingIndicator')) {
        console.log('Typing indicator already exists, skipping');
        return;
    }
    
    // Find messages wrapper or create one
    let messagesWrapper = chatContainer.querySelector('.messages-wrapper');
    if (!messagesWrapper) {
        console.log('Creating messages wrapper for typing indicator');
        messagesWrapper = document.createElement('div');
        messagesWrapper.className = 'messages-wrapper w-100';
        messagesWrapper.style.display = 'flex';
        messagesWrapper.style.flexDirection = 'column';
        chatContainer.appendChild(messagesWrapper);
    }
    
    // Create the typing indicator row
    const indicatorRow = document.createElement('div');
    indicatorRow.id = 'typingIndicator';
    indicatorRow.className = 'message-row d-flex justify-content-start';
    indicatorRow.style.width = '100%';
    indicatorRow.style.marginBottom = '10px';
    
    // Create the bubble
    const indicatorBubble = document.createElement('div');
    indicatorBubble.className = 'message-bubble agent-message';
    indicatorBubble.style.maxWidth = '80%';
    
    // Add the typing animation
    indicatorBubble.innerHTML = `
        <div class="message-content agent">
            <div class="typing-indicator">
                <span></span><span></span><span></span>
            </div>
        </div>
    `;
    
    // Assemble and add to DOM
    indicatorRow.appendChild(indicatorBubble);
    messagesWrapper.appendChild(indicatorRow);
    
    // Force layout recalculation
    void chatContainer.offsetHeight;
    
    // Scroll to bottom
    setTimeout(() => {
        chatContainer.scrollTop = chatContainer.scrollHeight;
        console.log('Scrolled to bottom for typing indicator');
    }, 50);
}

/**
 * Hide typing indicator
 */
function hideTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        // Also remove the clearfix div that follows the indicator
        const nextElement = indicator.nextElementSibling;
        if (nextElement && nextElement.style.clear === 'both') {
            nextElement.remove();
        }
        indicator.remove();
    }
}

/**
 * Update the list of conversations in the sidebar
 */
function updateConversationsList() {
    fetch('/api/conversations')
        .then(response => response.json())
        .then(data => {
            const conversationsList = document.getElementById('conversationsList');
            if (!conversationsList) return;
            
            conversationsList.innerHTML = '';
            
            if (data.conversations && data.conversations.length > 0) {
                data.conversations.forEach(conv => {
                    const item = document.createElement('li');
                    item.className = `conversation-item list-group-item ${conv.id === activeConversationId ? 'active' : ''}`;
                    item.setAttribute('data-id', conv.id);
                    
                    const date = new Date(conv.updated_at);
                    const formattedDate = date.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
                    
                    item.innerHTML = `
                        <div class="d-flex w-100 justify-content-between">
                            <h6 class="mb-1">${conv.title || 'Untitled Conversation'}</h6>
                            <small>${formattedDate}</small>
                        </div>
                    `;
                    
                    item.addEventListener('click', function() {
                        loadConversation(conv.id);
                    });
                    
                    conversationsList.appendChild(item);
                });
            } else {
                const item = document.createElement('li');
                item.className = 'list-group-item text-muted';
                item.textContent = 'No conversations yet';
                conversationsList.appendChild(item);
            }
        })
        .catch(error => {
            console.error('Error updating conversations list:', error);
        });
}

/**
 * Load a specific conversation
 */
function loadConversation(conversationId) {
    console.log('Loading conversation:', conversationId);
    
    // Mark as active
    activeConversationId = conversationId;
    
    // Update active state in list
    document.querySelectorAll('.conversation-item').forEach(item => {
        if (parseInt(item.getAttribute('data-id')) === conversationId) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
    
    // Ensure chat container exists and has proper styles
    const chatContainer = document.getElementById('chatMessages');
    if (!chatContainer) {
        console.error('Chat container not found, unable to load conversation');
        return;
    }
    
    // Set critical styles
    chatContainer.style.display = 'flex';
    chatContainer.style.flexDirection = 'column';
    chatContainer.style.overflowY = 'auto';
    
    // Clear messages
    console.log('Clearing existing messages');
    while (chatContainer.firstChild) {
        chatContainer.removeChild(chatContainer.firstChild);
    }
    
    // Show loading indicator
    console.log('Showing loading indicator');
    const loadingElement = document.createElement('div');
    loadingElement.id = 'chat-loading';
    loadingElement.className = 'text-center p-3';
    loadingElement.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';
    chatContainer.appendChild(loadingElement);
    
    // Load messages
    console.log(`Fetching messages for conversation ${conversationId}`);
    fetch(`/api/conversations/${conversationId}/messages`)
        .then(response => {
            console.log('Message fetch response status:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('Message data received:', data);
            
            // Remove loading indicator
            const loadingElement = document.getElementById('chat-loading');
            if (loadingElement) {
                loadingElement.remove();
            }
            
            if (data.messages && data.messages.length > 0) {
                console.log(`Found ${data.messages.length} messages to display`);
                
                // Sort messages by timestamp if needed
                data.messages.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
                
                // Clear any previous messages to be safe
                while (chatContainer.firstChild) {
                    chatContainer.removeChild(chatContainer.firstChild);
                }
                
                // Display all messages with forEach loop
                data.messages.forEach((msg, index) => {
                    console.log(`Displaying message ${index+1}/${data.messages.length}:`, {
                        content: msg.content ? msg.content.substring(0, 30) + '...' : 'null',
                        is_user: msg.is_user,
                        agent_name: msg.agent_name
                    });
                    displayMessage(msg.content, msg.is_user, msg.agent_name);
                });
                
                // Log final count to verify all messages were added
                console.log(`Chat container now has ${chatContainer.childElementCount} child elements`);
                
                // Force scroll to bottom
                setTimeout(() => {
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                    console.log('Scrolled to bottom after loading all messages');
                }, 100);
            } else {
                console.log('No messages found for this conversation');
                // Empty conversation
                chatContainer.innerHTML = `
                    <div class="text-center p-5">
                        <p class="text-muted">No messages in this conversation yet.</p>
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error loading conversation:', error);
            
            // Remove loading indicator
            const loadingElement = document.getElementById('chat-loading');
            if (loadingElement) {
                loadingElement.remove();
            }
            
            displayAlert('Failed to load conversation messages. Please try again.', 'danger');
        });
}

/**
 * Display an alert message
 */
function displayAlert(message, type = 'info') {
    console.log(`Alert: ${message} (${type})`);
    
    // Ensure container exists
    let alertContainer = document.getElementById('alertContainer');
    if (!alertContainer) {
        alertContainer = document.createElement('div');
        alertContainer.id = 'alertContainer';
        alertContainer.className = 'alert-container';
        document.body.appendChild(alertContainer);
    }
    
    // Create alert
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.role = 'alert';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    alertContainer.appendChild(alert);
    
    // Auto dismiss
    setTimeout(() => {
        alert.classList.remove('show');
        setTimeout(() => alert.remove(), 150);
    }, 5000);
}
