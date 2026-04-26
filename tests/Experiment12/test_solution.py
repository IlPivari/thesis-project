from __future__ import annotations

from collections.abc import Iterable, Iterator

import pytest

from tests._shared import load_function_from_env


def _generator(values: Iterable[object]) -> Iterator[object]:
    for value in values:
        yield value


@pytest.mark.parametrize(
    ("first", "second", "expected"),
    [
        ([1, 2, 2, 3], [3, 4, 2, 5], [1, 2, 3, 4, 5]),
        (("alpha", "beta"), ("beta", "gamma"), ["alpha", "beta", "gamma"]),
        ([], [], []),
    ],
)
def test_merges_values_preserving_first_occurrence(
    first: Iterable[object], second: Iterable[object], expected: list[object]
) -> None:
    fn = load_function_from_env()

    assert fn(first, second) == expected


def test_accepts_general_iterables() -> None:
    fn = load_function_from_env()

    first = _generator([1, 2, 2, 3])
    second = (3, 4, 4, 5)

    assert fn(first, second) == [1, 2, 3, 4, 5]


def test_accepts_range_objects_as_iterable_inputs() -> None:
    fn = load_function_from_env()

    first = range(0, 5)
    second = range(3, 8)

    assert fn(first, second) == [0, 1, 2, 3, 4, 5, 6, 7]


def test_accepts_dictionary_key_views() -> None:
    fn = load_function_from_env()

    first = {"alpha": 1, "beta": 2, "gamma": 3}.keys()
    second = {"beta": 20, "delta": 4}.keys()

    assert fn(first, second) == ["alpha", "beta", "gamma", "delta"]


def test_handles_values_compared_by_equality_even_when_not_hashable() -> None:
    fn = load_function_from_env()

    first = [[1, 2], {"role": "reader"}, [1, 2]]
    second = [{"role": "reader"}, [3, 4], [1, 2], [3, 4]]

    assert fn(first, second) == [[1, 2], {"role": "reader"}, [3, 4]]


def test_handles_nested_unhashable_values_with_repeated_content() -> None:
    fn = load_function_from_env()

    first = [
        {"id": 1, "tags": ["a", "b"]},
        {"id": 2, "tags": ["c"]},
    ]
    second = [
        {"id": 1, "tags": ["a", "b"]},
        {"id": 3, "tags": ["d"]},
        {"id": 2, "tags": ["c"]},
    ]

    assert fn(first, second) == [
        {"id": 1, "tags": ["a", "b"]},
        {"id": 2, "tags": ["c"]},
        {"id": 3, "tags": ["d"]},
    ]


def test_returns_a_new_list_without_mutating_inputs() -> None:
    fn = load_function_from_env()

    first = [1, 2, 2]
    second = [2, 3, 4]

    result = fn(first, second)

    assert result == [1, 2, 3, 4]
    assert result is not first
    assert result is not second
    assert first == [1, 2, 2]
    assert second == [2, 3, 4]


@pytest.mark.parametrize(
    ("first", "second"),
    [
        (10, [1, 2]),
        ([1, 2], 20),
        (None, [1, 2]),
        ([1, 2], None),
    ],
)
def test_rejects_non_iterable_inputs(first: object, second: object) -> None:
    fn = load_function_from_env()

    with pytest.raises(TypeError):
        fn(first, second)