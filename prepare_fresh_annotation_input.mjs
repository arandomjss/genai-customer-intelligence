import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "file:///C:/Users/jaskirat%20singh/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";

const root = process.cwd();
const workbookPath = path.join(root, "outputs", "blind_holdout_250", "blind_holdout_annotation_250.xlsx");
const outputPath = path.join(root, "data", "validation", "fresh_annotation_input_250.csv");
const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(workbookPath));
const sheet = workbook.worksheets.getItem("Annotation");
const rows = sheet.getRange("B5:E254").values;
const quote = (value) => `"${String(value ?? "").replaceAll('"', '""')}"`;
const csv = ["review_id,parent_asin,rating,review_text", ...rows.map((row) => row.map(quote).join(","))].join("\n") + "\n";
await fs.writeFile(outputPath, csv, "utf8");
console.log(JSON.stringify({ outputPath, rows: rows.length }));
