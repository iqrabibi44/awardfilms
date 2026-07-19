/**
 * Custom robust CSV parser to split values by commas while respecting quoted fields.
 */
export function parseCSV(csvText: string): Record<string, string>[] {
  const lines = csvText.split("\n");
  const results: Record<string, string>[] = [];
  if (lines.length === 0) return results;

  // Header row cleaning
  const headers = lines[0].split(",").map((h) => h.trim().replace(/^"|"$/g, ""));

  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;

    const cells: string[] = [];
    let inQuotes = false;
    let currentCell = "";

    for (let charIdx = 0; charIdx < line.length; charIdx++) {
      const char = line[charIdx];
      if (char === '"') {
        inQuotes = !inQuotes;
      } else if (char === "," && !inQuotes) {
        cells.push(currentCell.trim());
        currentCell = "";
      } else {
        currentCell += char;
      }
    }
    cells.push(currentCell.trim());

    const record: Record<string, string> = {};
    headers.forEach((header, index) => {
      let val = cells[index] || "";
      val = val.replace(/^"|"$/g, "").trim();
      record[header] = val;
    });
    results.push(record);
  }
  return results;
}
