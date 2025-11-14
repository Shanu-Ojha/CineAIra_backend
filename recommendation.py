import sys
import json
import time
import pickle
import torch
import pandas as pd
import numpy as np
from sentence_transformers import util
import difflib
import os

if os.environ.get("DEBUG_MODE") == "1":
    print("Loading embeddings...", file=sys.stderr)

# =========================================================
# === Configuration =======================================
# =========================================================
DATA_PATH = "movies_light.csv"           
EMBEDDINGS_PATH = "movie_embeddings.pkl"   

# =========================================================
# === Load dataset and embeddings =========================
# =========================================================
print("Loading dataset and embeddings...")

if not os.path.exists(DATA_PATH):
    print(f"Dataset file not found: {DATA_PATH}")
    sys.exit(1)

if not os.path.exists(EMBEDDINGS_PATH):
    print(f"Embeddings file not found: {EMBEDDINGS_PATH}")
    sys.exit(1)

# Load dataset
new_data = pd.read_csv(DATA_PATH)
required_columns = {"id", "title", "tags"}
if not required_columns.issubset(set(new_data.columns)):
    print("movies_light.csv must contain 'id', 'title', and 'tags' columns.")
    sys.exit(1)

# =========================================================
# === Load embeddings from .pkl ===========================
# =========================================================
import pickle
import torch
import numpy as np

device = "cuda" if torch.cuda.is_available() else "cpu"

with open(EMBEDDINGS_PATH, "rb") as f:
    loaded = pickle.load(f)

if isinstance(loaded, dict):
    embeddings = loaded.get("embeddings", None)
else:
    embeddings = loaded

if embeddings is None:
    raise ValueError("embeddings.pkl is missing valid embedding data")

embeddings_tensor = torch.tensor(np.array(embeddings), dtype=torch.float32, device=device)
print("Embeddings loaded successfully:", embeddings_tensor.shape)
print(f"Device in use: {device}, Movies loaded: {len(new_data)}")

# =========================================================
# === Recommendation function =============================
# =========================================================
def recommend(movie_title, top_n=5):
    if not movie_title or not isinstance(movie_title, str):
        return {"error": "Invalid movie title."}

    titles = new_data["title"].dropna().tolist()
    lower_titles = [t.lower() for t in titles]

    # Fuzzy match
    matches = difflib.get_close_matches(movie_title.lower(), lower_titles, n=1, cutoff=0.5)
    if not matches:
        return {"error": f"'{movie_title}' not found in dataset."}

    best_match = matches[0]
    idx_list = new_data[new_data["title"].str.lower() == best_match].index
    if len(idx_list) == 0:
        return {"error": f"'{movie_title}' not found in dataset."}

    idx = int(idx_list[0])
    target_emb = embeddings_tensor[idx].unsqueeze(0)

    # Compute cosine similarity
    cosine_scores = util.cos_sim(target_emb, embeddings_tensor)[0]
    similar_indices = torch.argsort(cosine_scores, descending=True)[1:top_n + 1]

    # Build results
    results = []
    for i in similar_indices:
        i = int(i)
        results.append({
            "id": int(new_data.iloc[i]["id"]),
            "title": new_data.iloc[i]["title"],
            "similarity": round(float(cosine_scores[i]), 4)
        })

    return {"recommendations": results}


# =========================================================
# === CLI + Node Integration ==============================
# =========================================================
if __name__ == "__main__":
    if len(sys.argv) > 1:
        movie_name = " ".join(sys.argv[1:]).strip()
        try:
            result = recommend(movie_name)
            # Output only JSON for Node.js to parse safely
            print(json.dumps(result))
        except Exception as e:
            print(json.dumps({"error": str(e)}))
        sys.exit(0)
    else:
        print("Recommender ready. Use CLI mode or Node API.")
        while True:
            user_input = input("\nEnter a movie name (or 'exit' to quit): ").strip()
            if user_input.lower() in {"exit", "quit"}:
                break
            start = time.time()
            result = recommend(user_input)
            end = time.time()
            if "error" in result:
                print(result["error"])
            else:
                print(f"Done in {end - start:.2f}s\nRecommendations:")
                for r in result["recommendations"]:
                    print(f"- {r['title']} ({r['similarity']})")
