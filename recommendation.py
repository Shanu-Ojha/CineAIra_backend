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
from huggingface_hub import hf_hub_download

# =========================================================
# === HuggingFace Repo Info ===============================
# =========================================================
HF_REPO = "ShanuOjha/movie-embeddings"  # ✅ CHANGE IF NEEDED
CSV_FILE = "movies_light.csv"
PKL_FILE = "movie_embeddings.pkl"

print("Fetching files from HuggingFace Hub...")

# =========================================================
# === Download CSV from HuggingFace ========================
# =========================================================
csv_path = hf_hub_download(
    repo_id=HF_REPO,
    filename=CSV_FILE,
    repo_type="dataset",
    cache_dir="./"
)

print(f"CSV loaded from: {csv_path}")

new_data = pd.read_csv(csv_path)
required_columns = {"id", "title", "tags"}
if not required_columns.issubset(set(new_data.columns)):
    print("CSV must contain 'id', 'title', and 'tags' columns.")
    sys.exit(1)

# =========================================================
# === Download Embeddings PKL from HuggingFace =============
# =========================================================
pkl_path = hf_hub_download(
    repo_id=HF_REPO,
    filename=PKL_FILE,
    repo_type="dataset",
    cache_dir="./"
)

print(f"Embeddings file loaded from: {pkl_path}")

# Load embeddings
with open(pkl_path, "rb") as f:
    loaded = pickle.load(f)

if isinstance(loaded, dict):
    embeddings = loaded.get("embeddings", None)
else:
    embeddings = loaded

if embeddings is None:
    raise ValueError("Embeddings file missing valid data")

device = "cuda" if torch.cuda.is_available() else "cpu"

embeddings_tensor = torch.tensor(
    np.array(embeddings),
    dtype=torch.float32,
    device=device
)

print("Embeddings loaded:", embeddings_tensor.shape)
print("Device:", device)

# =========================================================
# === Recommendation Function =============================
# =========================================================
def recommend(movie_title, top_n=5):
    if not movie_title or not isinstance(movie_title, str):
        return {"error": "Invalid movie title."}

    titles = new_data["title"].dropna().tolist()
    lower_titles = [t.lower() for t in titles]

    matches = difflib.get_close_matches(movie_title.lower(), lower_titles, n=1, cutoff=0.5)
    if not matches:
        return {"error": f"'{movie_title}' not found in dataset."}

    best_match = matches[0]
    idx_list = new_data[new_data["title"].str.lower() == best_match].index
    if len(idx_list) == 0:
        return {"error": f"'{movie_title}' not found in dataset."}

    idx = int(idx_list[0])
    target_emb = embeddings_tensor[idx].unsqueeze(0)

    cosine_scores = util.cos_sim(target_emb, embeddings_tensor)[0]
    similar_indices = torch.argsort(cosine_scores, descending=True)[1:top_n + 1]

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
# === CLI / Node Integration ==============================
# =========================================================
if __name__ == "__main__":
    if len(sys.argv) > 1:
        movie_name = " ".join(sys.argv[1:]).strip()
        try:
            result = recommend(movie_name)
            print(json.dumps(result))
        except Exception as e:
            print(json.dumps({"error": str(e)}))
        sys.exit(0)
    else:
        print("Recommender ready (HuggingFace mode).")
        while True:
            user_input = input("\nEnter a movie name (or 'exit'): ").strip()
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
