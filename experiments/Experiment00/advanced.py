from __future__ import annotations


def solution(a: int, b: int) -> int:
    if not isinstance(a, int) or not isinstance(b, int):
        raise TypeError("a and b must be int")
    return a + b
