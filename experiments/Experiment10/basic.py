def solution(n):
    if n <= 0:
        return []

    sequence = []
    first, second = 0, 1

    for _ in range(n):
        sequence.append(first)
        first, second = second, first + second

    return sequence