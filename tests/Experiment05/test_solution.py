from __future__ import annotations

from typing import Any

import pytest

from tests._shared import load_function_from_env


def test_counts_repeated_words_case_insensitively() -> None:
    fn = load_function_from_env()

    assert fn("Hello hello HELLO world") == {"hello": 3, "world": 1}


def test_ascii_punctuation_is_ignored_when_counting_words() -> None:
    fn = load_function_from_env()

    text = "red, blue. red! blue? green; red: blue"

    assert fn(text) == {"red": 3, "blue": 3, "green": 1}


def test_empty_and_whitespace_only_text_return_empty_dict() -> None:
    fn = load_function_from_env()

    assert fn("") == {}
    assert fn("   \t\n  ") == {}


def test_alphanumeric_tokens_are_preserved() -> None:
    fn = load_function_from_env()

    text = "version2 beta2 version2 release2026"

    assert fn(text) == {"version2": 2, "beta2": 1, "release2026": 1}


def test_unicode_casefold_is_supported_in_advanced() -> None:
    fn = load_function_from_env()

    assert fn("STRASSE stra\u00dfe") == {"strasse": 2}


def test_greek_final_sigma_is_normalized_in_advanced() -> None:
    fn = load_function_from_env()

    assert fn("\u039f\u03a3 \u03bf\u03c2 \u03bf\u03c3") == {"\u03bf\u03c3": 3}


def test_typographic_ligatures_are_normalized_in_advanced() -> None:
    fn = load_function_from_env()

    assert fn("\ufb03 ffi") == {"ffi": 2}


@pytest.mark.parametrize("invalid_value", [None, 123, 10.5, object()])
def test_invalid_input_raises(invalid_value: Any) -> None:
    fn = load_function_from_env()

    with pytest.raises(Exception):
        fn(invalid_value)