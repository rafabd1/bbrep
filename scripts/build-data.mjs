import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import YAML from "yaml";
import { globPrograms, normalizeProgram } from "./lib/data.js";

const root = process.cwd();
const files = await globPrograms(root);
const programs = [];

for (const file of files) {
  const raw = await readFile(file, "utf8");
  const parsed = YAML.parse(raw);
  programs.push(normalizeProgram(parsed, file, root));
}

programs.sort((a, b) => {
  if (b.averageRating !== a.averageRating) return b.averageRating - a.averageRating;
  if (b.reviewCount !== a.reviewCount) return b.reviewCount - a.reviewCount;
  return a.name.localeCompare(b.name);
});

const outDir = path.join(root, "site", "src", "generated");
await mkdir(outDir, { recursive: true });
await writeFile(
  path.join(outDir, "programs.json"),
  JSON.stringify({ generatedAt: new Date().toISOString(), programs }, null, 2) + "\n",
);

console.log(`Built ${programs.length} program records.`);
