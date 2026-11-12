const express = require("express");
const axios = require("axios");
const router = express.Router();

const FASTAPI_URL = process.env.FASTAPI_URL || "http://localhost:8000";

router.post("/qa", async (req, res) => {
  try {
    const { query } = req.body;

    if (!query) {
      return res.status(400).json({ error: "Query string is required." });
    }

    const aiResponse = await axios.post(`${FASTAPI_URL}/semantic-search`, {
      query,
      limit: 4,
    });

    return res.status(200).json({
      success: true,
      query,
      context: aiResponse.data.context,
      matches: aiResponse.data.matches,
    });
  } catch (error) {
    console.error("Error in Q&A gateway:", error.message);
    return res
      .status(500)
      .json({ error: "Internal server error while processing request." });
  }
});

// Export router directly
module.exports = router;
