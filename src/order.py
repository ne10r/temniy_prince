"""Find a dependency-first loading order without recursion."""

from .graph import FINISHED, VISITING


def get_load_order(graph: dict, root: str) -> list[str]:
    """Return DFS finishing order and reject cyclic dependencies."""
    if root not in graph:
        raise ValueError(f"Package not found in graph: {root}")
    colors = {root: VISITING}
    stack = [(root, iter(graph[root]))]
    order = []
    while stack:
        package, children = stack[-1]
        child = next(children, None)
        if child is None:
            colors[package] = FINISHED
            order.append(package)
            stack.pop()
            continue
        if child not in graph:
            raise ValueError(f"Missing dependency: {child}")
        if colors.get(child) == VISITING:
            raise ValueError(f"Cannot order a cycle: {package} -> {child}")
        if colors.get(child) == FINISHED:
            continue
        colors[child] = VISITING
        stack.append((child, iter(graph[child])))
    return order
