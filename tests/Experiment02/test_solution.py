from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pytest

from tests._shared import load_function_from_env


def _normalize_primes(value: Any) -> list[int]:
	if isinstance(value, list):
		return value

	if isinstance(value, Iterable) and not isinstance(value, (str, bytes, bytearray)):
		return list(value)

	raise TypeError("solution must return an iterable of integers")


def test_returns_primes_up_to_n_inclusive() -> None:
	fn = load_function_from_env()

	assert _normalize_primes(fn(10)) == [2, 3, 5, 7]


def test_returns_empty_for_values_below_two() -> None:
	fn = load_function_from_env()

	assert _normalize_primes(fn(1)) == []
	assert _normalize_primes(fn(0)) == []


def test_handles_small_prime_boundaries() -> None:
	fn = load_function_from_env()

	assert _normalize_primes(fn(2)) == [2]
	assert _normalize_primes(fn(3)) == [2, 3]


def test_includes_upper_bound_when_prime() -> None:
	fn = load_function_from_env()

	assert _normalize_primes(fn(13)) == [2, 3, 5, 7, 11, 13]


def test_excludes_upper_bound_when_not_prime() -> None:
	fn = load_function_from_env()

	assert _normalize_primes(fn(20)) == [2, 3, 5, 7, 11, 13, 17, 19]


def test_no_duplicates_and_sorted_output() -> None:
	fn = load_function_from_env()

	out = _normalize_primes(fn(50))

	assert out == sorted(out)
	assert len(out) == len(set(out))


def test_negative_input_returns_empty() -> None:
	fn = load_function_from_env()

	assert _normalize_primes(fn(-10)) == []


@pytest.mark.parametrize("invalid_value", [None, "10", 10.5, object()])
def test_invalid_input_raises(invalid_value: Any) -> None:
	fn = load_function_from_env()

	with pytest.raises(Exception):
		_normalize_primes(fn(invalid_value))