from __future__ import annotations

from pathlib import Path
from collections.abc import Iterable

import pytest

from tests._shared import load_function_from_env


TOTAL_NUMBERS = 2_000
TEST_NUMBERS_PATH = Path(__file__).with_name("test_numbers.txt")


def _permutation_1_to_2000() -> list[int]:
    raw_numbers = TEST_NUMBERS_PATH.read_text(encoding="utf-8")
    return [int(value) for value in raw_numbers.split(",") if value.strip()]


def _generator(values: list[int]) -> Iterable[int]:
    for value in values:
        yield value


def test_sorts_a_permutation_of_integers_from_1_to_2000() -> None:
    fn = load_function_from_env()

    result = fn(_permutation_1_to_2000())

    assert result == list(range(1, TOTAL_NUMBERS + 1))


def test_accepts_any_iterable_of_valid_values() -> None:
    fn = load_function_from_env()

    result = fn(_generator(_permutation_1_to_2000()))

    assert result == list(range(1, TOTAL_NUMBERS + 1))


@pytest.mark.parametrize(
    "numbers",
    [
        list(range(1, TOTAL_NUMBERS)),
        list(range(1, TOTAL_NUMBERS + 2)),
    ],
)
def test_rejects_inputs_with_the_wrong_number_of_values(numbers: list[int]) -> None:
    fn = load_function_from_env()

    with pytest.raises(ValueError):
        fn(numbers)
