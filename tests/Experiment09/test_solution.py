from __future__ import annotations

import pytest

from tests._shared import load_function_from_env


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("", True),
        ("Nessuna parentesi da controllare in questa frase.", True),
        ("([]){}", True),
        ("if (items[2] == values[{index: 3}[\"index\"]]) { return ready; }", True),
        (")apertura mancante(", False),
        ("([)]", False),
        ("funzione(alpha, beta[gamma)", False),
        ("testo finale con chiusura inattesa ]", False),
    ],
)
def test_validates_bracket_sequences(text: str, expected: bool) -> None:
    fn = load_function_from_env()

    assert fn(text) is expected


def test_handles_nested_brackets_across_multiple_lines() -> None:
    fn = load_function_from_env()
    text = (
        "def render(data):\n"
        "    return {\n"
        "        'title': config['labels'][0],\n"
        "        'items': [\n"
        "            format_item(entry, meta=(entry['id'], entry['tags'][0]))\n"
        "            for entry in data\n"
        "        ],\n"
        "    }\n"
    )

    assert fn(text) is True


def test_rejects_unclosed_openings_in_large_text() -> None:
    fn = load_function_from_env()
    balanced_block = (
        "report(section[0], {value: (current + offset)})\\n"
        "while (queue[head] != markers[{slot: 1}[\"slot\"]]) { consume(queue[head]); }\\n"
    )
    text = (balanced_block * 250) + "final_check(pending_items[3]"

    assert fn(text) is False


def test_handles_large_balanced_input_with_mixed_content() -> None:
    fn = load_function_from_env()
    chunk = (
        "function alpha(row) { return [row[0], {meta: (row[1] + row[2])}, row[(3 + 4) % 5]]; }\\n"
        "if (alpha_set[index] == beta_map[{slot: 2}[\"slot\"]]) { output.push(result[index]); }\\n"
        "notes: controllo(parziale[step], blocco{interno}) e verifica finale.\\n"
    )
    text = chunk * 400

    assert fn(text) is True