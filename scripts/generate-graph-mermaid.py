"""
Generate a Mermaid diagram of god nodes (top 15 by degree) from graphify-out/graph.json
and patch it into graphify-out/GRAPH_REPORT.md between <!-- MERMAID-START --> / <!-- MERMAID-END --> markers.

Called as: python3 scripts/generate-graph-mermaid.py
No external dependencies — Python 3 standard library only.
Silent on success. Errors go to stderr. Exit code always 0.
"""

import contextlib
import json
import os
import sys
import tempfile
from pathlib import Path

GRAPH_JSON = Path("graphify-out/graph.json")
REPORT_MD = Path("graphify-out/GRAPH_REPORT.md")

MARKER_START = "<!-- MERMAID-START -->"
MARKER_END = "<!-- MERMAID-END -->"
GOD_NODES_PREFIX = "## God Nodes"

MAX_LABEL_LEN = 30
TOP_N = 15
MAX_EDGES = 30


def truncate(label: str, max_len: int = MAX_LABEL_LEN) -> str:
    if len(label) > max_len:
        return label[: max_len - 1] + "…"
    return label


def main() -> None:
    # Resolve paths relative to repo root (robust from git hooks and CI)
    repo_root = Path(__file__).resolve().parent.parent

    graph_json = repo_root / GRAPH_JSON
    report_md = repo_root / REPORT_MD

    if not graph_json.exists():
        # Silent exit — expected on fresh clone before graphify run
        return

    try:
        with graph_json.open(encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception as exc:
        print(f"generate-graph-mermaid: failed to read graph.json: {exc}", file=sys.stderr)
        return

    nodes_raw = data.get("nodes", [])
    links_raw = data.get("links", [])

    id_to_label: dict[str, str] = {}
    for node in nodes_raw:
        node_id = node.get("id")
        label = node.get("label", node_id)
        if node_id:
            id_to_label[node_id] = label

    degree: dict[str, int] = {}
    for link in links_raw:
        src = link.get("source")
        tgt = link.get("target")
        if src:
            degree[src] = degree.get(src, 0) + 1
        if tgt:
            degree[tgt] = degree.get(tgt, 0) + 1

    top_ids = {
        node_id
        for node_id, _ in sorted(degree.items(), key=lambda kv: kv[1], reverse=True)[:TOP_N]
    }

    filtered_edges = [
        link
        for link in links_raw
        if link.get("source") in top_ids and link.get("target") in top_ids
    ]
    filtered_edges = filtered_edges[:MAX_EDGES]

    lines = ["```mermaid", "graph LR"]
    for link in filtered_edges:
        src = link.get("source")
        tgt = link.get("target")
        if not src or not tgt:
            continue
        src_label = truncate(id_to_label.get(src, src))
        tgt_label = truncate(id_to_label.get(tgt, tgt))
        src_safe = src_label.replace('"', "'")
        tgt_safe = tgt_label.replace('"', "'")
        lines.append(f'  {src}["{src_safe}"] --> {tgt}["{tgt_safe}"]')
    lines.append("```")

    mermaid_block = "\n".join(lines)
    full_block = f"{MARKER_START}\n{mermaid_block}\n{MARKER_END}\n"

    if not report_md.exists():
        return

    try:
        content = report_md.read_text(encoding="utf-8")
    except Exception as exc:
        print(f"generate-graph-mermaid: failed to read GRAPH_REPORT.md: {exc}", file=sys.stderr)
        return

    if MARKER_START in content and MARKER_END in content:
        before = content[: content.index(MARKER_START)]
        after_marker_end = content[content.index(MARKER_END) + len(MARKER_END) :]
        if after_marker_end.startswith("\n"):
            after_marker_end = after_marker_end[1:]
        new_content = before + full_block + after_marker_end
    else:
        report_lines = content.splitlines(keepends=True)
        insert_after = -1
        for i, line in enumerate(report_lines):
            if line.startswith(GOD_NODES_PREFIX):
                insert_after = i
                break
        if insert_after == -1:
            new_content = content.rstrip("\n") + "\n\n" + full_block
        else:
            before_lines = report_lines[: insert_after + 1]
            after_lines = report_lines[insert_after + 1 :]
            new_content = "".join(before_lines) + "\n" + full_block + "".join(after_lines)

    tmp_path = None
    try:
        dir_path = report_md.parent
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=dir_path, delete=False, suffix=".tmp"
        ) as tmp:
            tmp_path = tmp.name
            tmp.write(new_content)
        os.replace(tmp_path, report_md)
    except Exception as exc:
        print(f"generate-graph-mermaid: failed to write GRAPH_REPORT.md: {exc}", file=sys.stderr)
        if tmp_path:
            with contextlib.suppress(Exception):
                os.unlink(tmp_path)


if __name__ == "__main__":
    main()
