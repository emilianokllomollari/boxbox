var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

function appendMessage(message, sender) {
    var messagesDiv = document.getElementById('messages');

    // Define prefix based on sender
    var prefix = sender === 'user' ? 'You: ' : (sender === 'gemini' ? 'Gemini: ' : 'GPT-3.5: ');

    // Create a generic div for the message
    var messageDiv = document.createElement('div');
    messageDiv.textContent = prefix + message; // Now prefix is correctly defined before use

    if (sender === 'user') {
        messageDiv.className = 'user-message';
        messagesDiv.appendChild(messageDiv); // Append directly for user messages
    } else {
        var lastElement = messagesDiv.lastElementChild;
        var rowDiv;
        if (lastElement && lastElement.classList.contains('ai-message-container')) {
            rowDiv = lastElement;
        } else {
            rowDiv = document.createElement('div');
            rowDiv.className = 'ai-message-container d-flex justify-content-between';
            messagesDiv.appendChild(rowDiv);
        }

        var aiMessageDiv = document.createElement('div');
        aiMessageDiv.className = sender === 'gemini' ? 'gemini-message' : 'gpt3_5-message';
        aiMessageDiv.textContent = prefix + message;
        rowDiv.appendChild(aiMessageDiv);
    }

    scrollToBottom(); // Ensure autoscroll is called correctly
}


// Message sender
function sendMessage() {
    var messageInput = document.getElementById('messageInput');
    var userMessage = messageInput.value.trim();

    console.log("Attempting to send message:", userMessage); // Debugging line

    if (userMessage) {
        appendMessage(userMessage, 'user');
        socket.emit('send_message', {
            chat_id: chatId,
            message: userMessage
        });
        messageInput.value = '';
    } else {
        console.log("Message is empty or whitespace."); // Debugging line
    }
}


// Event listener for the send button
document.getElementById('sendButton').addEventListener('click', function () {
    sendMessage();
});

// Event listener for handling Enter and Shift+Enter in the textarea
document.getElementById('messageInput').addEventListener('keydown', function (event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault(); // Prevent newline on Enter
        sendMessage();
    }
    // Shift+Enter is allowed by default, inserting a newline
});

// Handling messages received from the server
socket.on('gemini_message', function (data) {
    appendMessage(data.message, 'gemini');
});

socket.on('gpt3_5_message', function (data) {
    appendMessage(data.message, 'gpt3_5');
});

//Change the name of the chat
// Shows the rename input and hides the rename button
function showRenameField(chatId) {
    const inputId = `rename-input-${chatId}`;
    const buttonId = `rename-btn-${chatId}`;
    const chatBtnId = `chat-btn-${chatId}`;

    const input = document.getElementById(inputId);
    const renameButton = document.getElementById(buttonId);
    const chatButton = document.getElementById(chatBtnId);

    if (input && renameButton && chatButton) {
        input.classList.remove('d-none'); // Show the input
        renameButton.classList.add('d-none'); // Hide the rename button
        chatButton.classList.add('d-none'); // Hide the chat button
        input.value = chatButton.textContent.trim(); // Set input value to current chat name
        input.focus(); // Focus on the input
    }
}



// Submits the new chat name when Enter is pressed and hides the input field
function submitNewChatName(chatId, newName) {
    if (!newName.trim()) return; // Avoid empty names

    // Replace 'fetchEndpoint' with the correct endpoint URL
    const fetchEndpoint = `/rename_chat/${chatId}`;

    fetch(fetchEndpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            // Add your CSRF token here if needed
        },
        body: JSON.stringify({ newName: newName.trim() })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Handle successful name change
            console.log('Chat name changed successfully.');
            location.reload(); // Reload the page or update UI as needed
        } else {
            // Handle error
            console.error('Failed to change chat name:', data.message);
        }
    })
    .catch(error => console.error('Error:', error));

    // Optionally, hide the input and show the button again
    const inputId = `rename-input-${chatId}`;
    const buttonId = `rename-btn-${chatId}`;

    const input = document.getElementById(inputId);
    const button = document.getElementById(buttonId);

    if (input && button) {
        input.classList.add('d-none'); // Hide the input
        button.classList.remove('d-none'); // Show the button
    }
}


// Event listener for handling Enter in the rename input
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.rename-input').forEach(input => {
        input.addEventListener('keypress', event => {
            if (event.key === 'Enter') {
                event.preventDefault(); // Prevent form submission
                const chatId = input.getAttribute('data-chat-id');
                const newName = input.value;
                submitNewChatName(chatId, newName);
            }
        });
    });
});


//Part of Autoscroll
function scrollToBottom() {
    var messageContainer = document.getElementById('messages');
    messageContainer.scrollTop = messageContainer.scrollHeight;
}
// Call the function after adding a new message (within your chat logic)
scrollToBottom();



