const fs = require("fs");
const path = require("path");

module.exports = (req, res) => {
  let files = [];
  try {
    files = fs
      .readdirSync(path.join(process.cwd(), "pdfs"))
      .filter((f) => /^(tongi|mohila|dhaka)_[a-z0-9-]+_[a-z0-9-]+_\d{4}\.pdf$/.test(f));
  } catch (e) {
    files = [];
  }
  res.setHeader("Cache-Control", "s-maxage=60, stale-while-revalidate=300");
  res.status(200).json({ files });
};
