// Pyodide smoke runner (spec 000 FR-000-25, NFR-000-06).
// Usage: node tests/pyodide/run_smoke.mjs <path-to-wheel>
// Loads the pinned Pyodide (npm package "pyodide", series 314.0.x), loads Pyodide's own numpy and pyyaml packages,
// installs the wheel with micropip without resolving dependencies, runs tests/pyodide/smoke.py and prints
// "SMOKE OK <module>" per module and "SMOKE OK" at the end. Exit status 0 only when every check passed.
import { readFileSync } from "node:fs";
import { basename, dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { loadPyodide } from "pyodide";

const wheelPath = process.argv[2];
if (!wheelPath) {
  console.error("usage: node run_smoke.mjs <path-to-wheel>");
  process.exit(2);
}

const here = dirname(fileURLToPath(import.meta.url));
const pyodide = await loadPyodide();
await pyodide.loadPackage(["numpy", "pyyaml", "micropip"]);

const wheelName = basename(wheelPath);
pyodide.FS.writeFile(`/tmp/${wheelName}`, readFileSync(wheelPath));
const micropip = pyodide.pyimport("micropip");
await micropip.install(`emfs:/tmp/${wheelName}`, { deps: false });

const smoke = readFileSync(join(here, "smoke.py"), "utf8");
try {
  await pyodide.runPythonAsync(smoke);
} catch (err) {
  console.error(String(err));
  process.exit(1);
}
console.log("SMOKE OK");
