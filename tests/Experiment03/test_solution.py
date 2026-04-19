from __future__ import annotations

from typing import Any

import pytest

from tests._shared import load_function_from_env


def test_finds_existing_value_in_sorted_list() -> None:
    fn = load_function_from_env()

    assert fn([1, 3, 5, 7, 9], 7) == 3


def test_returns_minus_one_when_value_is_missing() -> None:
    fn = load_function_from_env()

    assert fn([1, 3, 5, 7, 9], 4) == -1


def test_empty_sequence_returns_minus_one() -> None:
    fn = load_function_from_env()

    assert fn([], 10) == -1


def test_supports_single_item_sequences() -> None:
    fn = load_function_from_env()

    assert fn([5], 5) == 0
    assert fn([5], 1) == -1


def test_supports_tuple_input() -> None:
    fn = load_function_from_env()

    assert fn((2, 4, 6, 8), 6) == 2


def test_duplicate_values_return_first_matching_index() -> None:
    fn = load_function_from_env()

    assert fn([1, 2, 2, 2, 3], 2) == 1


@pytest.mark.parametrize(
    ("values", "target", "expected"),
    [
        ([-10, -3, 0, 4, 9], -10, 0),
        ([-10, -3, 0, 4, 9], 9, 4),
        ([0, 10, 20, 30], -1, -1),
        ([0, 10, 20, 30], 31, -1),
    ],
)
def test_boundary_and_out_of_range_cases(values: list[int], target: int, expected: int) -> None:
    fn = load_function_from_env()

    assert fn(values, target) == expected


@pytest.mark.parametrize("invalid_values", [10, object()])
def test_invalid_sequence_inputs_raise(invalid_values: Any) -> None:
    fn = load_function_from_env()

    with pytest.raises(Exception):
        fn(invalid_values, 1)


def test_none_input_is_rejected_or_treated_as_empty_sequence() -> None:
    fn = load_function_from_env()

    try:
        result = fn(None, 1)
    except Exception:
        return

    assert result == -1