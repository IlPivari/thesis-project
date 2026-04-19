from __future__ import annotations

import copy

import pytest

from tests._shared import load_function_from_env


def test_returns_new_list_and_does_not_mutate_input() -> None:
    fn = load_function_from_env()

    items = [{"k": 2}, {"k": 1}]
    original = copy.deepcopy(items)

    out = fn(items, key="k")

    assert out == [{"k": 1}, {"k": 2}]
    assert items == original
    assert out is not items


def test_key_none_deterministic_sorting() -> None:
    fn = load_function_from_env()

    items = [{"b": 2}, {"a": 1}, {"a": 0}]
    out = fn(items)

    # Should return a list with same elements but sorted deterministically.
    assert sorted((tuple(sorted(d.items())) for d in out)) == sorted(
        (tuple(sorted(d.items())) for d in items)
    )


def test_key_string_missing_values_handled() -> None:
    fn = load_function_from_env()

    items = [{"k": 2}, {}, {"k": 1}]
    out = fn(items, key="k")

    # Missing key treated like None; should not crash.
    assert out[0] == {}
    assert out[1]["k"] == 1
    assert out[2]["k"] == 2


def test_key_sequence_of_fields() -> None:
    fn = load_function_from_env()

    items = [
        {"a": 1, "b": 2},
        {"a": 0, "b": 9},
        {"a": 1, "b": 1},
    ]
    out = fn(items, key=["a", "b"])

    assert out == [
        {"a": 0, "b": 9},
        {"a": 1, "b": 1},
        {"a": 1, "b": 2},
    ]


def test_key_callable() -> None:
    fn = load_function_from_env()

    items = [{"x": 2}, {"x": 1}, {"x": 3}]
    out = fn(items, key=lambda d: d["x"])
    assert [d["x"] for d in out] == [1, 2, 3]


def test_reverse_sort() -> None:
    fn = load_function_from_env()

    items = [{"k": 1}, {"k": 2}]
    out = fn(items, key="k", reverse=True)
    assert out == [{"k": 2}, {"k": 1}]


def test_invalid_items_raises() -> None:
    fn = load_function_from_env()

    with pytest.raises(Exception):
        fn(None)

    with pytest.raises(Exception):
        fn([{"k": 1}, 123])


def test_invalid_key_raises() -> None:
    fn = load_function_from_env()

    with pytest.raises(Exception):
        fn([{"k": 1}], key=object())
