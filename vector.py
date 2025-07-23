import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import re, os

# Load model once
model = SentenceTransformer("all-MiniLM-L6-v2")

# Preload all service documents and build searchable structure
service_contexts = {}
service_embeddings = {}
faiss_indices = {}

context_dir = "contexts"

for fname in os.listdir(context_dir):
    if fname.endswith(".txt"):
        service_name = fname.replace(".txt", "")
        with open(os.path.join(context_dir, fname), encoding="utf-8") as f:
            raw_text = f.read()
            docs = re.split(r'\n\s*\n|(?=^### )', raw_text.strip(), flags=re.MULTILINE)
            docs = [doc.strip() for doc in docs if len(doc.strip()) > 40]

            embeddings = model.encode(docs, show_progress_bar=False)
            dimension = embeddings.shape[1]

            index = faiss.IndexFlatL2(dimension)
            index.add(np.array(embeddings))

            service_contexts[service_name] = docs
            service_embeddings[service_name] = embeddings
            faiss_indices[service_name] = index

# Get top-k relevant chunks from a specific document

def get_top_k_docs(query, raw_text, k=3):
    docs = re.split(r'\n\s*\n|(?=^### )', raw_text.strip(), flags=re.MULTILINE)
    docs = [doc.strip() for doc in docs if len(doc.strip()) > 40]
    embeddings = model.encode(docs)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(np.array(embeddings))
    query_vec = model.encode([query])
    _, indices = index.search(query_vec, k)
    return [docs[i] for i in indices[0] if i < len(docs)]

# Determine the most likely service category

def classify_service_from_query(query):
    query_vec = model.encode([query])
    scores = {}
    for service_name, index in faiss_indices.items():
        D, _ = index.search(query_vec, 1)
        scores[service_name] = D[0][0]

    # Return service with the lowest distance (highest relevance)
    return min(scores, key=scores.get)