from __future__ import annotations

import pytest

from tests._shared import load_function_from_env


def test_addition_happy_path() -> None:
    fn = load_function_from_env()
    assert fn(2, 3) == 5


def test_addition_negative() -> None:
    fn = load_function_from_env()
    assert fn(-10, 3) == -7


def test_addition_type_error() -> None:
    fn = load_function_from_env()
    with pytest.raises(Exception):
        fn("2", 3)
