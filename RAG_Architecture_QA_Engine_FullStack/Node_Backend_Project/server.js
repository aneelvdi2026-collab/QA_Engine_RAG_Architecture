require("dotenv").config();
const express = require("express");
const cors = require("cors");

// Import the router directly
const semanticSearchRouter = require("./controllers/searchController");

const app = express();
const PORT = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());

// Mount the route (line 15)
app.use("/api", semanticSearchRouter);

app.listen(PORT, () => {
  console.log(`Node.js API Gateway running on port ${PORT}`);
});
