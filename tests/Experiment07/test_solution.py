from __future__ import annotations

import re

import pytest

from tests._shared import load_function_from_env


def _expected_reversed_text(text: str) -> str:
    if text == "":
        return ""

    parts = re.findall(r"\s+|\S+", text)
    words = [part for part in parts if not part.isspace()]
    if len(words) < 2:
        return text

    reversed_words = iter(reversed(words))
    rebuilt: list[str] = []
    for part in parts:
        rebuilt.append(part if part.isspace() else next(reversed_words))
    return "".join(rebuilt)


def test_reverses_words_in_a_simple_sentence() -> None:
    fn = load_function_from_env()

    assert fn("alpha beta gamma") == "gamma beta alpha"


@pytest.mark.parametrize(
    "text",
    [
        "  alpha   beta  gamma  ",
        "\talpha\tbeta\n\ngamma  delta\n",
        "  parola  ",
        " \t\n  ",
        "uno\u00a0due   tre",
    ],
)
def test_preserves_existing_whitespace_layout(text: str) -> None:
    fn = load_function_from_env()

    assert fn(text) == _expected_reversed_text(text)


def test_handles_large_text_with_mixed_whitespace() -> None:
    fn = load_function_from_env()

    chunk = (
        "alpha   beta\tgamma\n"
        "delta  epsilon\t\tzeta\n"
        "eta theta   iota kappa\tlambda\n"
        "mu  nu xi\tomicron\n"
        "pi rho   sigma tau\tupsilon\n"
        "phi  chi psi\tomega\n"
    )
    text = chunk * 200

    assert fn(text) == _expected_reversed_text(text)