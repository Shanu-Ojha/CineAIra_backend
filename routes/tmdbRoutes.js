import express from "express";
import axios from "axios";

const router = express.Router();
const TMDB_BASE_URL = "https://api.themoviedb.org/3";

// Search for a movie
router.get("/search", async (req, res) => {
  const { query } = req.query;
  if (!query) {
    return res.status(400).json({
      message: "Query parameter is required" 
    });
  }
  try {
    const response = await axios.get(`${TMDB_BASE_URL}/search/multi`, {
      params: {
        api_key: process.env.TMDB_API_KEY,
        query,
      },
    });
    res.json(response.data);
  } catch (error) {
    console.error("TMDB API Error:", error.message);
    res.status(500).json({ 
      message: "Error fetching data from TMDB", 
      error: error.message 
    });
  }
});

// Popular movies
router.get("/popular", async (req, res)=>{
  try{
    const response = await axios.get(`${TMDB_BASE_URL}/movie/popular`, {
      params: { 
        api_key: process.env.TMDB_API_KEY,
        page: 1
      },
    });
    // Limit to 12 movies on backend
    const limitedResults = {
      ...response.data,
      results: response.data.results.slice(0, 12)
    };
    res.json(limitedResults);
  } catch(error){
    console.error("TMDB API Error:", error.message);
    res.status(500).json({ 
      message: "Error fetching data from TMDB", 
      error: error.message 
    });
  }
});

// Trending movies
router.get("/trending", async (req, res)=>{
  try{
    const response = await axios.get(`${TMDB_BASE_URL}/trending/all/day`, {
      params: { 
        api_key: process.env.TMDB_API_KEY,
        page: 1
      },
    });
    // Limit to 12 movies on backend
    const limitedResults = {
      ...response.data,
      results: response.data.results.slice(0, 12)
    };
    res.json(limitedResults);
  } catch(error){
    console.error("TMDB API Error:", error.message);
    res.status(500).json({ 
      message: "Error fetching data from TMDB", 
      error: error.message 
    });
  }
});

// Top Rated Movies
router.get("/toprated", async (req, res) => {
  try {
    const response = await axios.get(`${TMDB_BASE_URL}/movie/top_rated`, {
      params: { 
        api_key: process.env.TMDB_API_KEY,
        page: 1
      },
    });
    // Limit to 12 movies on backend
    const limitedResults = {
      ...response.data,
      results: response.data.results.slice(0, 12)
    };
    res.json(limitedResults);
  } catch (error) {
    console.error("TMDB API Error:", error.message);
    res.status(500).json({ 
      message: "Error fetching data from TMDB", 
      error: error.message 
    });
  }
});

// Now playing Movies
router.get("/nowplaying", async (req, res) => {
  try {
    const response = await axios.get(`${TMDB_BASE_URL}/movie/now_playing`, {
      params: { 
        api_key: process.env.TMDB_API_KEY,
        page: 1
      },
    });
    // Limit to 12 movies on backend
    const limitedResults = {
      ...response.data,
      results: response.data.results.slice(0, 12)
    };
    res.json(limitedResults);
  } catch (error) {
    console.error("TMDB API Error:", error.message);
    res.status(500).json({ 
      message: "Error fetching data from TMDB", 
      error: error.message 
    });
  }
});

// Trailer
router.get("/trailer/:id", async (req, res) => {
  const { id } = req.params;
  const apiKey = process.env.TMDB_API_KEY;

  try {
    let videos = [];

    // ✅ Try movie first
    try {
      const movieRes = await axios.get(
        `https://api.themoviedb.org/3/movie/${id}/videos?api_key=${apiKey}`
      );
      videos = movieRes.data.results;
    } catch {}

    // ✅ If no videos, try TV
    if (!videos || videos.length === 0) {
      try {
        const tvRes = await axios.get(
          `https://api.themoviedb.org/3/tv/${id}/videos?api_key=${apiKey}`
        );
        videos = tvRes.data.results;
      } catch {}
    }

    // ✅ Find trailer or teaser
    const trailer =
      videos.find(
        (v) =>
          v.site === "YouTube" && (v.type === "Trailer")
      ) || videos.find((v) => v.site === "YouTube");

    // ✅ If still nothing → return graceful JSON (NOT 500)
    if (!trailer) {
      return res.json({ key: null, message: "No trailer available" });
    }

    res.json({ key: trailer.key });
  } catch (err) {
    console.error("TRAILER ERROR:", err.response?.data || err);
    res.status(200).json({ key: null, message: "No trailer found" });
  }
});



export default router;