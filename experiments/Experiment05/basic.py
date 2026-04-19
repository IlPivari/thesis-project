import re


def solution(text: str) -> dict[str, int]:
    words = re.findall(r"\b\w+\b", text.lower())
    frequencies: dict[str, int] = {}

    for word in words:
        frequencies[word] = frequencies.get(word, 0) + 1

    return frequencies