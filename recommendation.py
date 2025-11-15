import sys
import json
import pandas as pd
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from fuzzywuzzy import process

# =========================================================
# === Text Cleaning =======================================
# =========================================================
def clean_text(text):
    text = str(text).lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# =========================================================
# === Load Dataset ========================================
# =========================================================
def load_data():
    data = pd.read_csv("movies.csv")

    selected_cols = ['genres', 'keywords', 'cast', 'director', 'tagline']
    for col in selected_cols:
        data[col] = data[col].fillna("").apply(clean_text)

    data['combined_data'] = (
        data['genres'] + " " +
        (data['keywords'] + " ") * 2 +
        (data['cast'] + " ") * 2 +
        (data['director'] + " ") * 3 +
        data['tagline']
    )

    data = data.drop_duplicates(subset="title")
    return data

# =========================================================
# === Compute TF-IDF Embeddings ===========================
# =========================================================
def compute_similarity(data):
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    vectors = vectorizer.fit_transform(data["combined_data"])
    return cosine_similarity(vectors)

# =========================================================
# === Recommendation Function (MATCHES recommendation.py) ==
# =========================================================
def recommend(movie_title, data, similarity_matrix, top_n=5):
    if not movie_title or not isinstance(movie_title, str):
        return {"error": "Invalid movie title."}

    titles = data["title"].str.lower().tolist()
    movie_title = movie_title.lower()

    best_match, score = process.extractOne(movie_title, titles)

    if score < 60:
        return {"error": f"'{movie_title}' not found in dataset."}

    idx = titles.index(best_match)
    similarity_scores = list(enumerate(similarity_matrix[idx]))
    sorted_scores = sorted(similarity_scores, key=lambda x: x[1], reverse=True)[1:top_n + 1]

    results = []
    for i, score_val in sorted_scores:
        results.append({
            "id": int(data.iloc[i]["id"]),
            "title": data.iloc[i]["title"],
            "similarity": round(float(score_val), 4)
        })

    return {"recommendations": results}

# =========================================================
# === CLI / Node.js Integration (Same as recommendation.py)
# =========================================================
if __name__ == "__main__":
    try:
        data = load_data()
        similarity_matrix = compute_similarity(data)
    except Exception as e:
        print(json.dumps({"error": "Failed to load data: " + str(e)}))
        sys.exit(1)

    # Node CLI mode
    if len(sys.argv) > 1:
        movie_name = " ".join(sys.argv[1:]).strip()
        try:
            result = recommend(movie_name, data, similarity_matrix)
            print(json.dumps(result))
        except Exception as e:
            print(json.dumps({"error": str(e)}))
        sys.exit(0)

    # Terminal mode
    print("Recommender ready.")
    while True:
        user_input = input("\nEnter a movie name (or 'exit'): ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break
        result = recommend(user_input, data, similarity_matrix)
        print(result)
