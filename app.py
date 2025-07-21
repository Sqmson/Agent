from flask import Flask, render_template, request, jsonify
import requests, os
from dotenv import load_dotenv
from datetime import datetime
from vector import get_top_k_docs
import traceback

load_dotenv()
API_KEY = os.getenv("API_KEY")
app = Flask(__name__)

with open("Document.txt") as f:
    knowledge_base = f.read()

def process(knowledge_base, question):
    """Basic fallback response using whole document."""
    return "Let me connect you with support — I'm still learning this topic."

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    question = data["message"]
    response = process(knowledge_base, question)
    if response:
        return jsonify({"answer": response})
    else:
        return jsonify({"answer": "I'm not sure about that."})

@app.route("/")
def index():
    return render_template("base.html")

@app.route("/ask", methods=["POST"])
def ask():
    user_message = request.json.get("message", "").strip()

    try:
        retrieved_chunks = get_top_k_docs(user_message)
        if not retrieved_chunks or all(len(c.strip()) < 40 for c in retrieved_chunks):
            return jsonify({"reply": "⚠️ I couldn't find enough relevant information in the document."})

        context = "\n".join(f"- {chunk}" for chunk in retrieved_chunks)
        system_prompt = open("Prompt_Engineering.txt").read()

        payload = {
            "model": "google/gemma-3n-e4b-it",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context:\n{context}\n\nUser: {user_message}"}
            ],
            "max_tokens": 512,
            "temperature": 0.3,
            "top_p": 0.9,
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

@app.route("/initial", methods=["GET"])
def initial():
    hour = datetime.now().hour
    greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 17 else "Good evening"
    intro = f"{greeting}! How can i help?."
    return jsonify({
        "reply": intro
    })

if __name__ == "__main__":
    app.run(debug=True)
