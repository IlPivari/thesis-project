from __future__ import annotations

import pytest

from tests._shared import load_function_from_env


@pytest.mark.parametrize(
    ("count", "expected"),
    [
        (0, []),
        (1, [0]),
        (2, [0, 1]),
        (7, [0, 1, 1, 2, 3, 5, 8]),
    ],
)
def test_generates_expected_fibonacci_prefix(count: int, expected: list[int]) -> None:
    fn = load_function_from_env()

    assert fn(count) == expected


def test_generates_a_longer_sequence_with_correct_recurrence() -> None:
    fn = load_function_from_env()
    count = 250

    result = fn(count)

    assert len(result) == count
    assert result[:10] == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
    assert result[-1] == 4880197746793002076754294951020699004973287771475874

    for index in range(2, count):
        assert result[index] == result[index - 1] + result[index - 2]


@pytest.mark.parametrize("count", [-1, -8, -25])
def test_rejects_negative_lengths(count: int) -> None:
    fn = load_function_from_env()

    with pytest.raises(ValueError):
        fn(count)


@pytest.mark.parametrize("count", [True, False])
def test_rejects_boolean_lengths(count: bool) -> None:
    fn = load_function_from_env()

    with pytest.raises(TypeError):
        fn(count)


@pytest.mark.parametrize("count", [3.5, "12", None])
def test_rejects_non_integer_lengths(count: object) -> None:
    fn = load_function_from_env()

    with pytest.raises(TypeError):
        fn(count)