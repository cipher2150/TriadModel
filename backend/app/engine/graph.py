"""Minimal calculation dependency graph.

Each node declares the keys it reads. Evaluation order is derived by topological sort,
cycles are reported by name, and a node only ever sees the inputs it declared.
"""

from collections import deque
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal

Values = Mapping[str, Decimal]


def key(name: str, period: int) -> str:
    return f"{name}@{period}"


@dataclass(frozen=True)
class Node:
    key: str
    formula: str
    deps: tuple[str, ...]
    compute: Callable[[Values], Decimal]


@dataclass(frozen=True)
class TraceEntry:
    formula: str
    inputs: Mapping[str, Decimal]
    value: Decimal


class GraphError(Exception):
    """Structural problem: duplicate node or reference to an undefined node."""


class CycleError(GraphError):
    def __init__(self, cycle: tuple[str, ...]) -> None:
        super().__init__("Circular dependency: " + " -> ".join(cycle))
        self.cycle = cycle


def _validate(nodes: Mapping[str, Node]) -> None:
    for node in nodes.values():
        for dep in node.deps:
            if dep not in nodes:
                raise GraphError(f"{node.key} depends on undefined node {dep}")


def _index(nodes: Iterable[Node]) -> dict[str, Node]:
    indexed: dict[str, Node] = {}
    for node in nodes:
        if node.key in indexed:
            raise GraphError(f"Duplicate node {node.key}")
        indexed[node.key] = node
    return indexed


def _find_cycle(remaining: Mapping[str, Node]) -> tuple[str, ...]:
    """Walk dependencies among nodes that could not be ordered until a key repeats."""
    current = next(iter(remaining))
    path: list[str] = []
    seen: dict[str, int] = {}
    while current not in seen:
        seen[current] = len(path)
        path.append(current)
        current = next(dep for dep in remaining[current].deps if dep in remaining)
    return (*path[seen[current] :], current)


def topological_order(nodes: Iterable[Node]) -> list[Node]:
    indexed = _index(nodes)
    _validate(indexed)
    unmet = {k: len(set(n.deps)) for k, n in indexed.items()}
    dependents: dict[str, list[str]] = {k: [] for k in indexed}
    for node in indexed.values():
        for dep in set(node.deps):
            dependents[dep].append(node.key)

    ready = deque(k for k, count in unmet.items() if count == 0)
    ordered: list[Node] = []
    while ready:
        current = ready.popleft()
        ordered.append(indexed[current])
        for dependent in dependents[current]:
            unmet[dependent] -= 1
            if unmet[dependent] == 0:
                ready.append(dependent)

    if len(ordered) != len(indexed):
        done = {n.key for n in ordered}
        raise CycleError(_find_cycle({k: n for k, n in indexed.items() if k not in done}))
    return ordered


def evaluate(nodes: Iterable[Node]) -> tuple[dict[str, Decimal], dict[str, TraceEntry]]:
    values: dict[str, Decimal] = {}
    trace: dict[str, TraceEntry] = {}
    for node in topological_order(nodes):
        inputs = {dep: values[dep] for dep in node.deps}
        value = node.compute(inputs)
        values[node.key] = value
        trace[node.key] = TraceEntry(formula=node.formula, inputs=inputs, value=value)
    return values, trace


def downstream(nodes: Iterable[Node], changed: str) -> set[str]:
    """All nodes that transitively depend on `changed` (used for change-impact analysis)."""
    indexed = _index(nodes)
    dependents: dict[str, set[str]] = {k: set() for k in indexed}
    for node in indexed.values():
        for dep in node.deps:
            dependents[dep].add(node.key)
    affected: set[str] = set()
    stack = [changed]
    while stack:
        for dependent in dependents[stack.pop()]:
            if dependent not in affected:
                affected.add(dependent)
                stack.append(dependent)
    return affected
