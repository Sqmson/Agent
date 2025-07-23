from flask import Flask, render_template, request, jsonify
import requests, os
from dotenv import load_dotenv
from datetime import datetime
from vector import get_top_k_docs, classify_service_from_query
import traceback

load_dotenv()
API_KEY = os.getenv("API_KEY")
app = Flask(__name__)

# Core system prompt
SYSTEM_PROMPT = """
You are a professional, helpful, and accurate AI assistant trained to provide customer support for our company. Your responses must be based solely on the provided context document, which contains up-to-date and complete information on the selected service.

Guidelines:
- Stick to the content in the context. If a question is outside the context, politely respond that the information is not available.
- Provide clear, concise, and friendly responses.
- Break down complex answers into steps or bullet points.
- Clarify ambiguous queries before responding.
- Avoid assumptions or hallucinations.
"""

@app.route("/")
def index():
    # You'll pass service names here for frontend to populate radio buttons
    services = os.listdir("contexts")  # assuming context docs live in /contexts
    services = [s.replace(".txt", "") for s in services if s.endswith(".txt")]
    return render_template("base.html", services=services)

@app.route("/initial", methods=["GET"])
def initial():
    hour = datetime.now().hour
    greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 17 else "Good evening"
    return jsonify({
        "reply": f"{greeting}! How can I help you today?"
    })

@app.route("/ask", methods=["POST"])
def ask():
    user_message = request.json.get("message", "").strip()
    selected_service = request.json.get("selectedService", "").strip()

    try:
        # Determine context file
        if selected_service:
            context_path = f"contexts/{selected_service}.txt"
        else:
            # Auto-classify based on query
            selected_service = classify_service_from_query(user_message)
            context_path = f"contexts/{selected_service}.txt"

        if not os.path.exists(context_path):
            return jsonify({"reply": "⚠️ Could not determine the appropriate service to answer your question."})

        with open(context_path, encoding="utf-8") as f:
            raw_context = f.read()

        retrieved_chunks = get_top_k_docs(user_message, raw_context)
        if not retrieved_chunks or all(len(c.strip()) < 40 for c in retrieved_chunks):
            return jsonify({"reply": "⚠️ I couldn't find enough relevant information in the document."})

        context = "\n".join(f"- {chunk}" for chunk in retrieved_chunks)
        final_user_prompt = f"{SYSTEM_PROMPT}\n\nContext:\n{context}\n\nUser: {user_message}"

        payload = {
            "model": "google/gemma-3n-e4b-it",
            "messages": [{"role": "user", "content": final_user_prompt}],
            "max_tokens": 512,
            "temperature": 0.20,
            "top_p": 0.70,
            "frequency_penalty": 0.00,
            "presence_penalty": 0.00,
            "stream": False
        }

        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Accept": "application/json"
        }

        response = requests.post("https://integrate.api.nvidia.com/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()

        reply = response.json()["choices"][0]["message"]["content"]
        return jsonify({"reply": reply})

    except Exception as e:
        print("❌ ERROR:", str(e))
        traceback.print_exc()
        return jsonify({"reply": "⚠️ Sorry, an internal error occurred."}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
