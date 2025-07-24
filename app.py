import os
import traceback
from datetime import datetime

from flask import Flask, render_template, request, jsonify, session
import requests
from dotenv import load_dotenv

from vector import get_top_k_docs, classify_service_from_query

# loading .env, API_KEY, directories
load_dotenv()
API_KEY        = os.getenv("API_KEY")
CONTEXT_DIR    = "contexts"
FALLBACK_DIR   = "general_contexts"
FALLBACK_FILES = [f for f in os.listdir(FALLBACK_DIR) if f.endswith(".txt")]

SYSTEM_PROMPT = """
You are a professional, precise, and reliable customer-support assistant.  
Respond only to the user’s specific query using information strictly from the provided context.  
If the query is unclear, ask for clarification.  
Do not invent answers or go beyond the context.
"""

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "sq_mso.n")


@app.route("/")
def index():
    services = [f[:-4] for f in os.listdir(CONTEXT_DIR) if f.endswith(".txt")]
    return render_template("base.html", services=services)


@app.route("/initial", methods=["GET"])
def initial():
    hour     = datetime.now().hour
    greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 17 else "Good evening"
    return jsonify({ "reply": f"{greeting}! How can I help you today?" })


@app.route("/classify", methods=["POST"])
def classify():
    query = request.json.get("message", "").strip()
    svc   = classify_service_from_query(query)
    return jsonify({"service": svc})


@app.route("/ask", methods=["POST"])
def ask():
    try:
        user_message     = request.json.get("message", "").strip()
        selected_service = request.json.get("selectedService", "").strip()

        #determining service to explicitly query from
        if selected_service:
            svc = selected_service
        else:
            svc = classify_service_from_query(user_message)

        #Loadin the appropriate context file.
        context_path = os.path.join(CONTEXT_DIR, f"{svc}.txt")
        if os.path.exists(context_path):
            with open(context_path, encoding="utf-8") as f:
                raw_context = f.read()
        else:
            # fallback: concatenate all general_contexts
            fragments = []
            for fname in FALLBACK_FILES:
                with open(os.path.join(FALLBACK_DIR, fname), encoding="utf-8") as g:
                    fragments.append(g.read())
            raw_context = "\n\n".join(fragments)

        # Retrieve top-3 relevant tokerns
        retrieved = get_top_k_docs(user_message, raw_context, k=3)
        context   = "\n".join(f"- {chunk}" for chunk in retrieved)

        # Load previous conversation turns from session
        history = session.get("history", [])

        # Build the messages list:
        #    - system: instructions + context
        #    - prior turns (role=user or assistant)
        #    - current user message
        messages = []
        messages.append({
            "role": "system",
            "content": SYSTEM_PROMPT + "\n\nContext:\n" + context
        })
        messages.extend(history)
        messages.append({
            "role": "user",
            "content": user_message
        })

        # nvidia api call
        payload = {
            "model": "google/gemma-3n-e4b-it",
            "messages": messages,
            "max_tokens": 512,
            "temperature": 0.2,
            "top_p": 0.7,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "stream": True
        }
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Accept": "application/json"
        }

        resp = requests.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers=headers, json=payload
        )
        resp.raise_for_status()
        ai_reply = resp.json()["choices"][0]["message"]["content"]

        # keep only last 6 conversation threads/turns to history
        history.append({"role": "user",      "content": user_message})
        history.append({"role": "assistant", "content": ai_reply})
        session["history"] = history[-6:]

        return jsonify({"reply": ai_reply})

    except Exception:
        traceback.print_exc()
        return jsonify({"reply": "⚠️ An internal error occurred. Please try again."}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
