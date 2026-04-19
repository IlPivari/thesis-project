def solution(text: str) -> bool:
    """Return True if text is a palindrome, ignoring letter casing.

    The function is case-insensitive and supports Unicode-aware comparisons
    through ``str.casefold()``. Non-string inputs raise ``TypeError``.
    Empty strings and single-character strings are considered palindromes.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    normalized_text = text.casefold()
    return normalized_text == normalized_text[::-1]