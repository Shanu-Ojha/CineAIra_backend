import express from "express";
import { spawn } from "child_process";
import path from "path";
import fetch from "node-fetch";
import { fileURLToPath } from "url";
import dotenv from "dotenv";

dotenv.config();
const router = express.Router();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// TMDB API configuration
const TMDB_API_KEY = process.env.TMDB_API_KEY;
const TMDB_BASE_URL = "https://api.themoviedb.org/3";

// Helper to fetch movie poster by TMDB ID
async function fetchPosterById(id) {
  try {
    const response = await fetch(`${TMDB_BASE_URL}/movie/${id}?api_key=${TMDB_API_KEY}`);
    const data = await response.json();
    return data.poster_path || null;
  } catch (error) {
    console.error("Error fetching TMDB poster:", error);
    return null;
  }
}

router.get("/recommend", (req, res) => {
  const movie = req.query.query; // ✅ correct parameter
  if (!movie) {
    return res.status(400).json({ error: "Missing 'movie' parameter" });
  }

  const pythonScript = path.join(__dirname, "../recommendation.py");
  const pythonProcess = spawn("python", [pythonScript, movie]);

  let data = "";
  let errorOutput = "";

  pythonProcess.stdout.on("data", (chunk) => {
    data += chunk.toString();
  });

  pythonProcess.stderr.on("data", (err) => {
    errorOutput += err.toString();
    console.error("Python stderr:", err.toString());
  });

  pythonProcess.on("close", async () => {
    const jsonStart = data.indexOf("{");
    const jsonEnd = data.lastIndexOf("}") + 1;
    let jsonText = data.slice(jsonStart, jsonEnd);

    try {
      const jsonData = JSON.parse(jsonText);

      // If Python returned error
      if (jsonData.error) {
        return res.status(500).json({ error: jsonData.error });
      }

      // Fetch posters for each recommendation
      const recommendationsWithPosters = await Promise.all(
        (jsonData.recommendations || []).map(async (rec) => {
          const poster_path = await fetchPosterById(rec.id);
          return { ...rec, poster_path };
        })
      );

      res.json({ recommendations: recommendationsWithPosters });
    } catch (e) {
      console.error("Parsing error:", e);
      res.status(500).json({
        error: "Python script error",
        details: data || errorOutput || e.message,
      });
    }
  });
});

export default router;
