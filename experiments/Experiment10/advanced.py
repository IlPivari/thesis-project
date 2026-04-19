"""Advanced Fibonacci sequence generator.

This module exposes a single public function, ``solution``, which returns
the first ``n`` Fibonacci numbers while handling invalid inputs explicitly.
"""


def solution(n):
    """Return the first ``n`` values of the Fibonacci sequence.

    The sequence starts with ``0, 1``. For example:
    - ``solution(0)`` returns ``[]``
    - ``solution(1)`` returns ``[0]``
    - ``solution(5)`` returns ``[0, 1, 1, 2, 3]``

    Args:
        n: Number of Fibonacci values to generate.

    Returns:
        A list containing the first ``n`` Fibonacci numbers.

    Raises:
        TypeError: If ``n`` is not an integer or is a boolean value.
        ValueError: If ``n`` is negative.
    """
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError("n must be an integer")

    if n < 0:
        raise ValueError("n must be greater than or equal to 0")

    if n == 0:
        return []

    sequence = []
    current, following = 0, 1

    for _ in range(n):
        sequence.append(current)
        current, following = following, current + following

    return sequence