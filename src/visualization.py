"""Write D2 diagrams and render graph images with the D2 executable."""

import json
import shutil
import subprocess
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def get_cycle_edges(cycles: list) -> set:
    """Collect the graph edges that belong to reported DFS cycles."""
    edges = set()
    for cycle in cycles:
        for edge in zip(cycle, cycle[1:]):
            edges.add(edge)
    return edges


def graph_to_d2(graph: dict, cycles: list, root: str) -> str:
    """Use stable node IDs, quoted labels and red cycle edges."""
    ids = {name: f"n{i}" for i, name in enumerate(graph)}
    red_edges = get_cycle_edges(cycles)
    lines = ["direction: right"]
    for name, node_id in ids.items():
        lines.append(f"{node_id}: {json.dumps(name, ensure_ascii=False)}")
        if name == root:
            lines.append(f'{node_id}.style.fill: "#e8f0fe"')
    for package, children in graph.items():
        for child in children:
            if child not in ids:
                raise ValueError(f"Missing graph vertex: {child}")
            edge = f"{ids[package]} -> {ids[child]}"
            if (package, child) in red_edges:
                lines.extend([
                    edge + ": {", '  style.stroke: "#c62828"', "}",
                ])
            else:
                lines.append(edge)
    return "\n".join(lines) + "\n"


def find_d2(binary=None) -> str:
    """Find an explicit executable, d2 on PATH or a local tools copy."""
    if binary:
        found = shutil.which(str(binary))
    else:
        found = shutil.which("d2")
        if found is None:
            found = shutil.which(str(ROOT / ".tools" / "d2"))
    if found is None:
        raise ValueError("D2 executable not found; install d2 or use --d2")
    return found


def render_graph(
    graph: dict, cycles: list, root: str, output: Path, binary=None
) -> tuple[Path, Path]:
    """Write a .d2 source and ask D2 to create its SVG image."""
    if output.suffix.lower() != ".svg":
        raise ValueError("Image output must have the .svg extension")
    executable = find_d2(binary)
    source = output.with_suffix(".d2")
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(graph_to_d2(graph, cycles, root), encoding="utf-8")
    result = subprocess.run(
        [executable, "--layout=dagre", str(source), str(output)],
        capture_output=True, text=True, timeout=120
    )
    if result.returncode:
        message = result.stderr.strip() or result.stdout.strip()
        raise ValueError(f"D2 rendering failed: {message}")
    if not output.is_file() or not output.stat().st_size:
        raise ValueError("D2 did not create an image")
    return source, output


def show_image(path: Path) -> None:
    """Open the saved SVG in the default browser."""
    if not webbrowser.open(path.resolve().as_uri()):
        raise ValueError(
            f"Cannot open image automatically: {path.resolve()}"
        )
