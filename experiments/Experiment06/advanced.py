def solution(a: int, b: int) -> int:
    """Return the greatest common divisor of two integers.

    The implementation uses the Euclidean algorithm and normalizes negative
    inputs so the result is always non-negative. By convention,
    ``solution(0, 0)`` returns ``0``.
    """
    if isinstance(a, bool) or isinstance(b, bool):
        raise TypeError("Boolean values are not valid integer inputs")

    if not isinstance(a, int) or not isinstance(b, int):
        raise TypeError("solution expects two integers")

    a = abs(a)
    b = abs(b)

    if a == 0:
        return b
    if b == 0:
        return a

    while b != 0:
        a, b = b, a % b

    return a