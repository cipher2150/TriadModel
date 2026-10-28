from decimal import Decimal as D

import pytest

from app.engine.graph import (
    CycleError,
    GraphError,
    Node,
    Values,
    downstream,
    evaluate,
    topological_order,
)


def const(name: str, value: int) -> Node:
    return Node(name, "constant", (), lambda _: D(value))


def add(name: str, left: str, right: str) -> Node:
    return Node(name, f"{left} + {right}", (left, right), lambda v: v[left] + v[right])


def test_nodes_evaluate_after_their_dependencies_regardless_of_declaration_order() -> None:
    nodes = [add("c", "a", "b"), const("a", 2), const("b", 3)]
    values, _ = evaluate(nodes)
    assert values["c"] == D(5)
    order = [n.key for n in topological_order(nodes)]
    assert order.index("c") > order.index("a") and order.index("c") > order.index("b")


def test_trace_records_formula_inputs_and_value() -> None:
    _, trace = evaluate([const("a", 2), const("b", 3), add("c", "a", "b")])
    assert trace["c"].formula == "a + b"
    assert dict(trace["c"].inputs) == {"a": D(2), "b": D(3)}
    assert trace["c"].value == D(5)


def test_cycle_is_reported_with_the_participating_keys() -> None:
    nodes = [add("a", "b", "x"), add("b", "a", "x"), const("x", 1)]
    with pytest.raises(CycleError) as error:
        evaluate(nodes)
    assert set(error.value.cycle) == {"a", "b"}
    assert error.value.cycle[0] == error.value.cycle[-1]


def test_self_dependency_is_a_cycle() -> None:
    with pytest.raises(CycleError):
        evaluate([Node("a", "a", ("a",), lambda v: v["a"])])


def test_undefined_dependency_is_rejected() -> None:
    with pytest.raises(GraphError, match="undefined node missing"):
        evaluate([add("a", "missing", "missing")])


def test_duplicate_node_is_rejected() -> None:
    with pytest.raises(GraphError, match="Duplicate node a"):
        evaluate([const("a", 1), const("a", 2)])


def test_node_cannot_read_an_undeclared_input() -> None:
    def sneaky(v: Values) -> D:
        return v["b"]

    with pytest.raises(KeyError):
        evaluate([const("a", 1), const("b", 2), Node("c", "sneaky", ("a",), sneaky)])


def test_downstream_returns_transitive_dependents_only() -> None:
    nodes = [const("a", 1), const("b", 1), add("c", "a", "a"), add("d", "c", "b")]
    assert downstream(nodes, "a") == {"c", "d"}
    assert downstream(nodes, "b") == {"d"}
    assert downstream(nodes, "d") == set()


def test_empty_graph_evaluates_to_nothing() -> None:
    assert evaluate([]) == ({}, {})
