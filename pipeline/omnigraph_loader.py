from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from .edge_endpoints import load_existing_nodes_from_jsonl
from .models import GraphNode


@dataclass(frozen=True)
class LoadResult:
    branch_name: str
    stdout: str
    stderr: str


class OmnigraphLoader:
    def __init__(self, omnigraph_bin: str, graph_uri: str, actor: str):
        self.omnigraph_bin = omnigraph_bin
        self.graph_uri = graph_uri
        self.actor = actor

    def _run(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [self.omnigraph_bin, *args],
            text=True,
            capture_output=True,
            check=True,
        )

    def create_branch(self, branch_name: str, from_branch: str = "main") -> None:
        self._run(["branch", "create", branch_name, "--uri", self.graph_uri, "--from", from_branch])

    def load_jsonl(self, branch_name: str, jsonl_path: str | Path) -> LoadResult:
        result = self._run(
            [
                "--as",
                self.actor,
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
        return LoadResult(branch_name=branch_name, stdout=result.stdout, stderr=result.stderr)

    def export_nodes(self, branch_name: str, node_types: list[str]) -> dict[str, GraphNode]:
        nodes: dict[str, GraphNode] = {}
        for node_type in node_types:
            result = self._run(
                [
                    "export",
                    self.graph_uri,
                    "--branch",
                    branch_name,
                    "--type",
                    node_type,
                ]
            )
            nodes.update(load_existing_nodes_from_jsonl(result.stdout.splitlines()))
        return nodes
