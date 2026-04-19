from __future__ import annotations

from numbers import Real
from typing import Any


def _validate_item(item: Any, index: int) -> dict[str, Any]:
	if not isinstance(item, dict):
		raise TypeError(f"items[{index}] must be a dictionary")

	return item


def _normalize_sort_value(value: Any) -> tuple[int, str, Any]:
	if value is None:
		return (1, "none", None)

	if isinstance(value, bool):
		return (0, "bool", value)

	if isinstance(value, Real) and not isinstance(value, bool):
		return (0, "number", value)

	if isinstance(value, str):
		return (0, "string", value)

	raise TypeError(
		"sort values must be None, numbers, booleans, or strings"
	)


def solution(
	items: list[dict[str, Any]],
	sort_key: str,
	reverse: bool = False,
) -> list[dict[str, Any]]:
	"""Return a new list of dictionaries sorted by a single dictionary key.

	The function validates inputs, preserves the original list, and keeps the
		ordering stable for items with equal sort values.
	"""
	if not isinstance(items, list):
		raise TypeError("items must be a list")

	if not isinstance(sort_key, str):
		raise TypeError("sort_key must be a string")

	if not sort_key:
		raise ValueError("sort_key must be a non-empty string")

	if not isinstance(reverse, bool):
		raise TypeError("reverse must be a boolean")

	decorated_items: list[tuple[tuple[int, str, Any], dict[str, Any]]] = []
	value_kind: str | None = None

	for index, raw_item in enumerate(items):
		item = _validate_item(raw_item, index)
		normalized_value = _normalize_sort_value(item.get(sort_key))
		current_kind = normalized_value[1]

		if current_kind != "none":
			if value_kind is None:
				value_kind = current_kind
			elif current_kind != value_kind:
				raise TypeError("sort values must all share the same comparable type")

		decorated_items.append((normalized_value, item))

	decorated_items.sort(key=lambda entry: entry[0], reverse=reverse)
	return [item for _, item in decorated_items]
