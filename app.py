from flask import Flask, render_template, request, jsonify
import requests, os
from dotenv import load_dotenv
from datetime import datetime
from vector import get_top_k_docs
import traceback

load_dotenv()
API_KEY = os.getenv("API_KEY")
app = Flask(__name__)

@app.route("/")
def index():
    return render_template("base.html")  # Make sure base.html exists

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

    try:
        # Retrieve context chunks using FAISS
        retrieved_chunks = get_top_k_docs(user_message)
        if not retrieved_chunks or all(len(c.strip()) < 40 for c in retrieved_chunks):
            return jsonify({"reply": "⚠️ I couldn't find enough relevant information in the document."})

        context = "\n".join(f"- {chunk}" for chunk in retrieved_chunks)
        system_prompt = open("Prompt_Engineering.txt", encoding="utf-8").read()

        # Compose RAG-enabled API prompt
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

# Port binding for Render.com
if __name__ == "__main__":
<<<<<<< HEAD
    port = int(os.environ.get("PORT", 5000))
=======
    port = int(os.environ.get("PORT", 5001))  # fallback for local dev
>>>>>>> refs/remotes/origin/main
    app.run(host="0.0.0.0", port=port)
