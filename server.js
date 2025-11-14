import express from "express";
import dotenv from "dotenv";
import cors from "cors";

import tmdbRoutes from "./routes/tmdbRoutes.js";
import aiRoutes from "./routes/aiRoutes.js";

dotenv.config();
const app = express();

app.use(cors());
app.use(express.json());

// API Routes
app.use("/api/tmdb", tmdbRoutes);
app.use("/api/ai", aiRoutes);

// Render requires port = 10000
const PORT = process.env.PORT || 10000;

app.listen(PORT, () =>
  console.log(`🚀 Backend running on port ${PORT}`)
);


