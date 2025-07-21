class Chatbox {
    constructor() {
        this.args = {
            openButton: document.querySelector('.chatbox__button'),
            chatBox: document.querySelector('.chatbox__support'),
            sendButton: document.querySelector('.send__button'),
            chatContainer: document.querySelector('.chatbox__messages'),
            inputField: document.querySelector('.chatbox__footer input')
        }

        this.state = false;
        this.messages = [];
    }

    display() {
        const { openButton, chatBox, sendButton, inputField } = this.args;

        openButton.addEventListener('click', () => this.toggleState(chatBox));
        sendButton.addEventListener('click', () => this.onSendButton(chatBox));

        inputField.addEventListener("keyup", ({ key }) => {
            if (key === "Enter") this.onSendButton(chatBox);
        });
    }

    toggleState(chatbox) {
        this.state = !this.state;
        chatbox.classList.toggle('chatbox--active', this.state);
    }

    onSendButton(chatbox) {
        const { inputField } = this.args;
        const message = inputField.value.trim();
        if (!message) return;

        this.addUserMessage(message);
        inputField.value = "";
        this.scrollToBottom();
        this.showTypingIndicator();

        fetch('/ask', {
            method: 'POST',
            body: JSON.stringify({ message }),
            headers: { 'Content-Type': 'application/json' },
        })
        .then(r => r.json())
        .then(r => {
            this.addBotMessage(r.reply);
            this.hideTypingIndicator();
        })
        .catch(error => {
            console.error('Error:', error);
            this.addBotMessage("⚠️ Network error. Try again.");
            this.hideTypingIndicator();
        });
    }

    addUserMessage(text) {
        const div = document.createElement('div');
        div.className = 'messages__item messages__item--operator';
        div.textContent = text;
        this.args.chatContainer.appendChild(div);
    }

    addBotMessage(text) {
        const div = document.createElement('div');
        div.className = 'messages__item messages__item--visitor';
        div.innerHTML = this.parseMarkdown(text);
        this.args.chatContainer.appendChild(div);
        this.scrollToBottom();
    }

    parseMarkdown(markdown) {
        // Replace markdown-like syntax for bold/italic if needed
        return markdown.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>')
                       .replace(/\*(.*?)\*/g, '<i>$1</i>');
    }

    showTypingIndicator() {
        const typing = document.createElement('div');
        typing.className = 'messages__item messages__item--visitor typing';
        typing.textContent = 'Typing...';
        typing.id = 'typing-indicator';
        this.args.chatContainer.appendChild(typing);
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        const typing = document.getElementById('typing-indicator');
        if (typing) typing.remove();
    }

    scrollToBottom() {
        this.args.chatContainer.scrollTop = this.args.chatContainer.scrollHeight;
    }
}

const chatbox = new Chatbox();
chatbox.display();