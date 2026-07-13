from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


class OmnigraphError(RuntimeError):
    pass


class OmnigraphService:
    def __init__(self, omnigraph_bin: str, graph_uri: str, query_file: Path, timeout_seconds: int = 30):
        self.omnigraph_bin = omnigraph_bin
        self.graph_uri = graph_uri
        self.query_file = query_file
        self.timeout_seconds = timeout_seconds

    def _run(self, args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                [self.omnigraph_bin, *args],
                text=True,
                capture_output=True,
                check=check,
                timeout=self.timeout_seconds,
            )
        except subprocess.CalledProcessError as exc:
            message = (
                f"Omnigraph command failed with exit {exc.returncode}: {' '.join(map(str, exc.cmd))}\n"
                f"stdout: {exc.stdout.strip()}\n"
                f"stderr: {exc.stderr.strip()}"
            )
            raise OmnigraphError(message) from exc
        except subprocess.TimeoutExpired as exc:
            raise OmnigraphError(f"Omnigraph command timed out: {' '.join(map(str, exc.cmd))}") from exc

    def version(self) -> str:
        return self._run(["--version"]).stdout.strip()

    def list_branches(self) -> list[str]:
        result = self._run(["branch", "list", "--store", self.graph_uri])
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]

    def branch_exists(self, branch_name: str) -> bool:
        return branch_name in self.list_branches()

    def create_branch(self, branch_name: str, from_branch: str = "main") -> None:
        self._run(["branch", "create", branch_name, "--uri", self.graph_uri, "--from", from_branch])

    def delete_branch(self, branch_name: str, actor: str) -> dict[str, Any]:
        result = self._run(["--as", actor, "branch", "delete", branch_name, "--uri", self.graph_uri, "--yes"])
        return {"stdout": result.stdout, "stderr": result.stderr}

    def load_jsonl(self, branch_name: str, jsonl_path: str | Path, actor: str) -> dict[str, Any]:
        result = self._run(
            [
                "--as",
                actor,
                "load",
                self.graph_uri,
                "--data",
                str(jsonl_path),
                "--mode",
                "merge",
                "--branch",
                branch_name,
            ]
        )
        return {"stdout": result.stdout, "stderr": result.stderr}

    def merge_branch(self, source_branch: str, actor: str, target_branch: str = "main") -> dict[str, Any]:
        result = self._run(
            [
                "--as",
                actor,
                "branch",
                "merge",
                source_branch,
                "--uri",
                self.graph_uri,
                "--into",
                target_branch,
                "--json",
            ]
        )
        return self._parse_json_or_text(result.stdout, result.stderr)

    def export_branch(self, branch_name: str, type_name: str | None = None) -> list[dict[str, Any]]:
        args = ["export", self.graph_uri, "--branch", branch_name]
        if type_name:
            args.extend(["--type", type_name])
        result = self._run(args)
        records: list[dict[str, Any]] = []
        for line in result.stdout.splitlines():
            if line.strip():
                records.append(json.loads(line))
        return records

    def execute_query(self, query_name: str, params: dict[str, Any] | None = None, branch: str = "main") -> list[dict[str, Any]]:
        args = [
            "query",
            query_name,
            "--query",
            str(self.query_file),
            "--store",
            self.graph_uri,
            "--branch",
            branch,
            "--format",
            "jsonl",
        ]
        if params is not None:
            args.extend(["--params", json.dumps(params, sort_keys=True)])
        result = self._run(args)
        records = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
        return [record for record in records if record.get("kind") != "metadata"]

    def list_commits(self, branch: str = "main") -> list[dict[str, Any]]:
        result = self._run(["commit", "list", self.graph_uri, "--branch", branch, "--json"], check=False)
        if result.returncode != 0:
            return [{"error": result.stderr.strip()}]
        parsed = self._parse_json_or_text(result.stdout, result.stderr)
        if isinstance(parsed.get("json"), list):
            return parsed["json"]
        return [parsed]

    def _parse_json_or_text(self, stdout: str, stderr: str) -> dict[str, Any]:
        text = stdout.strip()
        if not text:
            return {"stdout": stdout, "stderr": stderr}
        try:
            return {"json": json.loads(text), "stdout": stdout, "stderr": stderr}
        except json.JSONDecodeError:
            return {"stdout": stdout, "stderr": stderr}
