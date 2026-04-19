from __future__ import annotations

import copy
from typing import Any

import pytest

from tests._shared import load_function_from_env


def test_returns_new_list_and_does_not_mutate_input() -> None:
    fn = load_function_from_env()

    items = [{"k": 2}, {"k": 1}]
    original = copy.deepcopy(items)

    out = fn(items, sort_key="k")

    assert out == [{"k": 1}, {"k": 2}]
    assert items == original
    assert out is not items


def test_empty_list_returns_empty_list() -> None:
    fn = load_function_from_env()

    items: list[dict[str, int]] = []
    out = fn(items, sort_key="k")

    assert out == []
    assert out is not items


def test_sort_is_stable_for_equal_values() -> None:
    fn = load_function_from_env()

    items = [
        {"k": 1, "name": "first"},
        {"k": 1, "name": "second"},
        {"k": 0, "name": "third"},
    ]

    out = fn(items, sort_key="k")

    assert [item["name"] for item in out] == ["third", "first", "second"]


def test_sort_key_string_existing_values_numeric_ordering() -> None:
    fn = load_function_from_env()

    items = [{"k": 10}, {"k": -1}, {"k": 3}]

    out = fn(items, sort_key="k")

    assert [item["k"] for item in out] == [-1, 3, 10]


def test_sort_key_string_existing_values_string_ordering() -> None:
    fn = load_function_from_env()

    items = [{"name": "delta"}, {"name": "alpha"}, {"name": "charlie"}]

    out = fn(items, sort_key="name")

    assert [item["name"] for item in out] == ["alpha", "charlie", "delta"]


def test_sort_key_string_allows_none_values_mixed_with_numbers() -> None:
    fn = load_function_from_env()

    items = [{"k": 2}, {"k": None}, {"k": 1}]

    out = fn(items, sort_key="k")

    assert out == [{"k": 1}, {"k": 2}, {"k": None}]


def test_sort_key_string_allows_none_values_mixed_with_strings() -> None:
    fn = load_function_from_env()

    items = [{"name": "beta"}, {"name": None}, {"name": "alpha"}]

    out = fn(items, sort_key="name")

    assert out == [{"name": "alpha"}, {"name": "beta"}, {"name": None}]


def test_reverse_sort() -> None:
    fn = load_function_from_env()

    items = [{"k": 1}, {"k": 2}]
    out = fn(items, sort_key="k", reverse=True)
    assert out == [{"k": 2}, {"k": 1}]


def test_invalid_items_raises() -> None:
    fn = load_function_from_env()

    with pytest.raises(Exception):
        fn(None)

    with pytest.raises(Exception):
        fn([{"k": 1}, 123])


def test_invalid_reverse_raises() -> None:
    fn = load_function_from_env()

    with pytest.raises(Exception):
        fn([{"k": 1}], sort_key="k", reverse="yes")


def test_empty_sort_key_is_rejected_even_if_present_in_items() -> None:
    fn = load_function_from_env()

    items = [{"": 2}, {"": 1}]

    with pytest.raises(Exception):
        fn(items, sort_key="")


def test_invalid_sort_key_raises() -> None:
    fn = load_function_from_env()

    with pytest.raises(Exception):
        fn([{"k": 1}], sort_key=object())


def test_mixed_incomparable_values_raise() -> None:
    fn = load_function_from_env()

    items: list[dict[str, Any]] = [{"k": 1}, {"k": "two"}]

    with pytest.raises(Exception):
        fn(items, sort_key="k")


def test_bool_and_number_values_are_not_mixed_silently() -> None:
    fn = load_function_from_env()

    items: list[dict[str, Any]] = [{"k": True}, {"k": 1}]

    with pytest.raises(Exception):
        fn(items, sort_key="k")


def test_unsupported_sort_values_raise_even_for_single_item() -> None:
    fn = load_function_from_env()

    items: list[dict[str, Any]] = [{"k": {"nested": 1}}]

    with pytest.raises(Exception):
        fn(items, sort_key="k")


def test_list_values_are_rejected_as_unsupported_sort_values() -> None:
    fn = load_function_from_env()

    items: list[dict[str, Any]] = [{"k": [2, 0]}, {"k": [1, 9]}]

    with pytest.raises(Exception):
        fn(items, sort_key="k")
