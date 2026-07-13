import { spawnSync } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(dirname(fileURLToPath(import.meta.url)));

function bin(name) {
  return join(root, "node_modules", ".bin", process.platform === "win32" ? `${name}.cmd` : name);
}

function run(command, args) {
  const result =
    process.platform === "win32"
      ? spawnSync("cmd.exe", ["/c", command, ...args], { stdio: "inherit" })
      : spawnSync(command, args, { stdio: "inherit" });
  if (result.error) {
    console.error(result.error.message);
    process.exit(1);
  }
  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}

run(bin("tsc"), ["-b"]);
run(bin("vite"), ["build"]);
