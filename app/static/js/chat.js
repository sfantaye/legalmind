// app/static/js/chat.js
function setupChat(sessionId) {
    const chatbox = document.getElementById('chatbox');
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');

    // Function to add message to chatbox
    function addMessage(sender, text) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        // Basic Markdown-like formatting for code blocks
        text = text.replace(/```([\s\S]*?)```/g, (match, p1) => {
            const codeContent = p1.trim();
            return `<pre><code>${escapeHtml(codeContent)}</code></pre>`;
        });
         // Simple bold/italic - might interfere with code blocks if not careful
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
        // Basic link detection (very simple)
        text = text.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');


        // Use innerHTML carefully as it can be a security risk if text is not sanitized
        // We are doing basic HTML escaping for code blocks, might need more robust solution
        messageDiv.innerHTML = `<p>${text.replace(/\n/g, '<br>')}</p>`; // Replace newlines with <br>

        if (sender === 'user') {
            messageDiv.classList.add('user-message');
        } else {
            messageDiv.classList.add('ai-message');
        }
        chatbox.appendChild(messageDiv);
        // Scroll to bottom
        chatbox.scrollTop = chatbox.scrollHeight;
    }

     // Basic HTML escaping
    function escapeHtml(unsafe) {
        if (!unsafe) return '';
        return unsafe
             .replace(/&/g, "&")
             .replace(/</g, "<")
             .replace(/>/g, ">")
             .replace(/"/g, """)
             .replace(/'/g, "'");
     }


    // Handle form submission
    chatForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const messageText = userInput.value.trim();
        if (!messageText) return;

        // Display user message immediately
        addMessage('user', messageText);
        userInput.value = ''; // Clear input
        sendButton.disabled = true; // Disable button while waiting
        addMessage('ai', 'Thinking...'); // Show thinking indicator

        try {
            // Send message to backend
            const response = await fetch(`/assistant/chat/${sessionId}`, { // Corrected endpoint
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded', // FastAPI Form expects this
                },
                body: new URLSearchParams({ 'user_input': messageText }) // Send as form data
            });

             // Remove "Thinking..." message
            const thinkingMsg = chatbox.querySelector('.ai-message:last-child');
            if (thinkingMsg && thinkingMsg.textContent.includes('Thinking...')) {
                chatbox.removeChild(thinkingMsg);
            }


            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'Unknown server error' }));
                console.error('Chat API error:', response.status, errorData);
                addMessage('ai', `Sorry, an error occurred: ${errorData.detail || response.statusText}`);
            } else {
                const data = await response.json();
                addMessage('ai', data.response || 'Received an empty response.');
            }

        } catch (error) {
             // Remove "Thinking..." message even on network error
            const thinkingMsg = chatbox.querySelector('.ai-message:last-child');
            if (thinkingMsg && thinkingMsg.textContent.includes('Thinking...')) {
                chatbox.removeChild(thinkingMsg);
            }
            console.error('Failed to send message:', error);
            addMessage('ai', 'Sorry, could not connect to the server.');
        } finally {
             sendButton.disabled = false; // Re-enable button
             userInput.focus(); // Focus input for next message
        }
    });

    console.log(`Chat initialized for session: ${sessionId}`);
}

// Make sure the function is globally available or called correctly after DOM loads
// The setupChat call is placed in the chat.html template script block.
