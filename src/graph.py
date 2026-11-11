"""Build a reachable dependency graph using iterative depth-first search."""

from typing import Callable

from .config import Config
from .pypi_repository import PyPIRepository
from .test_repository import read_test_repository

VISITING = 1
FINISHED = 2


def build_graph(
    root: str, get_children: Callable[[str], list[str]]
) -> tuple[dict[str, list[str]], list[list[str]]]:
    """Walk with a stack of iterators and record back edges as cycles."""
    graph = {root: list(dict.fromkeys(get_children(root)))}
    colors = {root: VISITING}
    path = [root]
    stack = [iter(graph[root])]
    cycles = []
    while stack:
        child = next(stack[-1], None)
        if child is None:
            colors[path.pop()] = FINISHED
            stack.pop()
            continue
        if colors.get(child) == VISITING:
            cycle = path[path.index(child):] + [child]
            if cycle not in cycles:
                cycles.append(cycle)
            continue
        if colors.get(child) == FINISHED:
            continue
        graph[child] = list(dict.fromkeys(get_children(child)))
        colors[child] = VISITING
        path.append(child)
        stack.append(iter(graph[child]))
    return graph, cycles


def load_graph(config: Config) -> tuple[dict, list]:
    """Choose the local or remote repository and build the root graph."""
    if config.test_mode:
        packages = read_test_repository(config.repository)
        if config.package not in packages:
            raise ValueError(f"Test package not found: {config.package}")
        return build_graph(config.package, packages.__getitem__)
    repository = PyPIRepository(config)
    return build_graph(repository.root, repository.get_children)
