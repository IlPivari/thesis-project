from collections.abc import Iterable


def solution(list1, list2):
    """Merge two iterables into a new list preserving order and removing duplicates.

    The function accepts any iterable inputs, returns a new list, and preserves the
    first occurrence of each distinct item across both inputs. Unhashable values are
    supported through a linear fallback check.

    Args:
        list1: First iterable of values.
        list2: Second iterable of values.

    Returns:
        A list containing unique values from both inputs in encounter order.

    Raises:
        TypeError: If either input is not an iterable.
    """
    first_items = _validate_iterable(list1, "list1")
    second_items = _validate_iterable(list2, "list2")

    result = []
    seen_hashable = set()

    for item in first_items:
        _append_unique(item, result, seen_hashable)

    for item in second_items:
        _append_unique(item, result, seen_hashable)

    return result


def _validate_iterable(value, parameter_name):
    if not isinstance(value, Iterable):
        raise TypeError(f"{parameter_name} must be an iterable")

    return list(value)


def _append_unique(item, result, seen_hashable):
    try:
        if item in seen_hashable:
            return
    except TypeError:
        if item in result:
            return
    else:
        seen_hashable.add(item)
        result.append(item)
        return

    result.append(item)