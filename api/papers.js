const fs = require("fs");
const path = require("path");

// Cache the file list in-memory for the lifetime of the serverless function instance
let cachedFiles = null;

module.exports = (req, res) => {
  if (!cachedFiles) {
    try {
      cachedFiles = fs
        .readdirSync(path.join(process.cwd(), "pdfs"))
        .filter((f) => /^(tongi|mohila|dhaka)_[a-z0-9-]+_[a-z0-9-]+_\d{4}\.pdf$/.test(f));
    } catch (e) {
      cachedFiles = [];
    }
  }
  res.setHeader("Cache-Control", "public, s-maxage=300, stale-while-revalidate=600");
  res.setHeader("Content-Type", "application/json");
  res.status(200).json({ files: cachedFiles });
};
