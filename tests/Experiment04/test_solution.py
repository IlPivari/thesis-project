from __future__ import annotations

import pytest

from tests._shared import load_function_from_env


def test_detects_simple_palindrome() -> None:
    fn = load_function_from_env()

    assert fn("anna") is True


def test_detects_non_palindrome() -> None:
    fn = load_function_from_env()

    assert fn("python") is False


def test_empty_and_single_character_strings_are_palindromes() -> None:
    fn = load_function_from_env()

    assert fn("") is True
    assert fn("x") is True


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("abba", True),
        ("abcba", True),
        ("abca", False),
    ],
)
def test_various_exact_case_inputs(text: str, expected: bool) -> None:
    fn = load_function_from_env()

    assert fn(text) is expected


def test_case_insensitive_palindrome_is_supported() -> None:
    fn = load_function_from_env()

    assert fn("Anna") is True


def test_non_string_sequences_are_rejected() -> None:
    fn = load_function_from_env()

    with pytest.raises(TypeError):
        fn(["n", "o", "o", "n"])