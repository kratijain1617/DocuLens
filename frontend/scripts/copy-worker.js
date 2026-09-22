const fs = require("fs");
const path = require("path");

const root = path.join(__dirname, "..");
const candidates = [
  "node_modules/pdfjs-dist/build/pdf.worker.min.mjs",
  "node_modules/pdfjs-dist/legacy/build/pdf.worker.min.mjs",
  "node_modules/react-pdf/node_modules/pdfjs-dist/build/pdf.worker.min.mjs",
];

const destinationDir = path.join(root, "public");
fs.mkdirSync(destinationDir, { recursive: true });

for (const candidate of candidates) {
  const source = path.join(root, candidate);
  if (fs.existsSync(source)) {
    fs.copyFileSync(source, path.join(destinationDir, "pdf.worker.min.mjs"));
    console.log("Copied PDF worker from", candidate);
    process.exit(0);
  }
}

console.log("PDF worker was not found. The viewer will look for /pdf.worker.min.mjs.");
process.exit(0);
