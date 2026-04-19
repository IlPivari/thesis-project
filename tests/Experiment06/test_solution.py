from __future__ import annotations

import pytest

from tests._shared import load_function_from_env


def test_returns_gcd_for_positive_integers() -> None:
    fn = load_function_from_env()

    assert fn(54, 24) == 6


def test_normalizes_negative_inputs() -> None:
    fn = load_function_from_env()

    assert fn(-54, 24) == 6
    assert fn(54, -24) == 6
    assert fn(-54, -24) == 6


def test_zero_inputs_follow_standard_gcd_convention() -> None:
    fn = load_function_from_env()

    assert fn(0, 18) == 18
    assert fn(18, 0) == 18
    assert fn(0, 0) == 0


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        (17, 13, 1),
        (21, 21, 21),
        (462, 1071, 21),
        (123456, 7890, 6),
    ],
)
def test_various_integer_pairs(a: int, b: int, expected: int) -> None:
    fn = load_function_from_env()

    assert fn(a, b) == expected


@pytest.mark.parametrize(
    ("a", "b"),
    [
        (True, 9),
        (False, False),
    ],
)
def test_boolean_inputs_raise_type_error(a: bool, b: bool | int) -> None:
    fn = load_function_from_env()

    with pytest.raises(TypeError):
        fn(a, b)


@pytest.mark.parametrize(
    ("a", "b"),
    [
        (54.0, 24),
        (54, 24.0),
        (144.0, 96.0),
    ],
)
def test_float_inputs_raise_type_error(a: float | int, b: float | int) -> None:
    fn = load_function_from_env()

    with pytest.raises(TypeError):
        fn(a, b)