var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

function appendMessage(message, sender) {
    var messagesDiv = document.getElementById('messages');
    var messageDiv = document.createElement('div');
    messageDiv.className = sender === 'user' ? 'user-message' :
        (sender === 'gemini' ? 'gemini-message' :
            'gpt3_5-message');

    var prefix = sender === 'user' ? 'You: ' :
        (sender === 'gemini' ? 'Gemini: ' :
            'GPT-3.5: ');

    messageDiv.textContent = prefix + message;
    messagesDiv.appendChild(messageDiv);
    //Autoscroll
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// Function to handle sending messages
function sendMessage() {
    var messageInput = document.getElementById('messageInput');
    var userMessage = messageInput.value.trim();

    if (userMessage) {
        appendMessage(userMessage, 'user');

        socket.emit('send_message', {
            // Ensure chatId is defined correctly in your context
            chat_id: chatId, // This assumes you have a chatId variable defined
            message: userMessage
        });

        messageInput.value = ''; // Clear the input after sending
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

//Part of Autoscroll
function scrollToBottom() {
    var messageContainer = document.getElementById('messages');
    messageContainer.scrollTop = messageContainer.scrollHeight;
}
// Call the function after adding a new message (within your chat logic)
scrollToBottom();
