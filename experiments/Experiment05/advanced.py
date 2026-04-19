import unicodedata
from collections import Counter


def solution(text: str) -> dict[str, int]:
	"""Count word frequencies in a text after case and punctuation normalization.

	The function:
	- normalizes case with ``casefold()`` for robust case-insensitive matching;
	- replaces Unicode punctuation with spaces to avoid merging adjacent words;
	- splits on whitespace and returns a plain dictionary of frequencies.

	Complexity is O(n) in the length of the input text.
	"""
	if not isinstance(text, str):
		raise TypeError("text must be a string")

	if not text or text.isspace():
		return {}

	normalized_chars: list[str] = []
	for char in text.casefold():
		if unicodedata.category(char).startswith("P"):
			normalized_chars.append(" ")
		else:
			normalized_chars.append(char)

	words = "".join(normalized_chars).split()
	return dict(Counter(words))
