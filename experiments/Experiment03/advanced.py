from bisect import bisect_left
from collections.abc import Sequence
from typing import Any


def solution(values: Sequence[Any], target: Any) -> int:
	"""Return the index of target in a sorted sequence, or -1 if absent.

	The function uses ``bisect_left`` to perform binary search in
	$O(\log n)$ time. It handles empty inputs explicitly and safely checks
	whether the insertion point actually contains the requested value.
	"""
	if not values:
		return -1

	index = bisect_left(values, target)

	if index == len(values):
		return -1

	return index if values[index] == target else -1
