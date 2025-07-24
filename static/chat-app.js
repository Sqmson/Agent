
      const mockServices = [
        "Technical Support",
        "Billing",
        "General Inquiry",
        "Account Issues",
        "Product Information",
      ];

      class Chatbox {
        constructor() {
          const q = (s) => document.querySelector(s);
          const qa = (s) => document.querySelectorAll(s);
          this.args = {
            openButton: q(".chatbox__button"),
            chatBox: q(".chatbox__support"),
            sendButton: q(".send__button"),
            chatContainer: q(".chatbox__messages"),
            inputField: q(".chatbox__footer input"),
            serviceToggle: q("#serviceToggle"),
            serviceSelector: q("#serviceSelector"),
            serviceForm: q("#serviceForm"),
          };
          this.state = false;
          this.selectedService = "";
          this.isServiceSelectorOpen = false;
        }

        display() {
          const { openButton, sendButton, inputField, serviceToggle } =
            this.args;
          this.initServices();
          openButton.onclick = () => this.toggleState();
          sendButton.onclick = () => this.onSendButton();
          inputField.oninput = () => this.toggleSendButton();
          inputField.onkeyup = ({ key }) =>
            key === "Enter" && this.onSendButton();
          serviceToggle.onclick = () => this.toggleServiceSelector();
        }

        initServices() {
          this.args.serviceForm.innerHTML = "";
          mockServices.forEach((service, i) => {
            const div = document.createElement("div");
            div.className = "service-option";
            div.innerHTML = `
        <input type="radio" name="selectedService" value="${service}" id="service-${i}">
        <label for="service-${i}">${service}</label>`;

            const radio = div.querySelector("input");
            const clickHandler = (e) => {
              if (e.target === radio) return;
              radio.checked
                ? this.clearService()
                : this.selectService(service, radio);
            };
            div.onclick = clickHandler;
            div.querySelector("label").onclick = clickHandler;
            radio.onclick = (e) => {
              e.preventDefault();
              this.selectedService === service
                ? this.clearService()
                : this.selectService(service, radio);
            };
            this.args.serviceForm.appendChild(div);
          });
        }

        selectService(service, radio) {
          document
            .querySelectorAll('input[name="selectedService"]')
            .forEach((r) => r !== radio && (r.checked = false));
          radio.checked = true;
          this.selectedService = service;
          this.updateIndicator();
        }

        clearService() {
          this.selectedService = "";
          document
            .querySelectorAll('input[name="selectedService"]')
            .forEach((r) => (r.checked = false));
          this.updateIndicator();
        }

        updateIndicator() {
          const existing = document.querySelector(
            ".selected-service-indicator"
          );
          if (existing) existing.remove();
          if (this.selectedService) {
            const ind = document.createElement("div");
            ind.className = "selected-service-indicator";
            ind.textContent = `Selected: ${this.selectedService}`;
            this.args.chatContainer.prepend(ind);
          }
        }

        toggleServiceSelector() {
          this.isServiceSelectorOpen = !this.isServiceSelectorOpen;
          this.args.serviceSelector.classList.toggle(
            "active",
            this.isServiceSelectorOpen
          );
          this.args.serviceToggle.textContent = this.isServiceSelectorOpen
            ? "Hide"
            : "Services";
        }

        toggleSendButton() {
          this.args.sendButton.disabled = !this.args.inputField.value.trim();
        }

        toggleState() {
          this.state = !this.state;
          this.args.chatBox.classList.toggle("chatbox--active", this.state);
        }

        async onSendButton() {
          const message = this.args.inputField.value.trim();
          if (!message) return;
          this.addUserMessage(message);
          this.args.inputField.value = "";
          this.toggleSendButton();
          this.showTypingIndicator();
          try {
            const res = await fetch("/ask", {
              method: "POST",
              body: JSON.stringify({
                message,
                selectedService: this.selectedService,
              }),
              headers: { "Content-Type": "application/json" },
            });
            const data = await res.json();
            this.addBotMessage(data.reply);
          } catch {
            this.addBotMessage("⚠️ Network error. Try again.");
          } finally {
            this.hideTypingIndicator();
          }
        }

        addUserMessage(text) {
          this.appendMessage(text, "operator");
        }

        addBotMessage(text) {
          this.appendMessage(this.parseMarkdown(text), "visitor", true);
        }

        appendMessage(content, userType, isHTML = false) {
          const div = document.createElement("div");
          div.className = `messages__item messages__item--${userType}`;
          if (isHTML) div.innerHTML = content;
          else div.textContent = content;
          this.args.chatContainer.appendChild(div);
          this.scrollToBottom();
        }

        parseMarkdown(md) {
          return md
            .replace(/\*\*(.+?)\*\*/g, "<b>$1</b>")
            .replace(/\*(.+?)\*/g, "<i>$1</i>");
        }

        showTypingIndicator() {
          if (!this.args.chatContainer.querySelector("#typing-indicator")) {
            const div = document.createElement("div");
            div.id = "typing-indicator";
            div.className = "messages__item messages__item--visitor typing";
            div.textContent = "Typing...";
            this.args.chatContainer.appendChild(div);
            this.scrollToBottom();
          }
        }

        hideTypingIndicator() {
          const typing =
            this.args.chatContainer.querySelector("#typing-indicator");
          if (typing) typing.remove();
        }

        scrollToBottom() {
          this.args.chatContainer.scrollTop =
            this.args.chatContainer.scrollHeight;
        }
      }

      const chatbox = new Chatbox();
      chatbox.display();

      window.onload = async () => {
        const h3 = document.querySelector(".empty-state h3");
        const p = document.querySelector(".empty-state p");
        try {
          const res = await fetch("/initial");
          const data = await res.json();
          const [first, ...rest] = data.reply.split("\n");
          h3.textContent = "🤖 " + first;
          p.textContent = rest.join(" ");
        } catch {
          h3.textContent = "🤖 Welcome to Chat Support";
          p.textContent =
            "Click 'Services' to select a category, then type your message below.";
        }
      };
    