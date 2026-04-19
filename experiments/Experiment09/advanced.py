def solution(text: str) -> bool:
    """Return True if brackets in text are balanced, otherwise False.

    The function supports round, square, and curly brackets and uses a
    stack-based approach with linear time complexity.
    Non-bracket characters are ignored so the function remains robust even
    when the input contains additional text.
    """
    matching_opening = {
        ")": "(",
        "]": "[",
        "}": "{",
    }
    opening_brackets = set(matching_opening.values())
    stack: list[str] = []

    for char in text:
        if char in opening_brackets:
            stack.append(char)
            continue

        if char in matching_opening:
            if not stack:
                return False

            expected_opening = matching_opening[char]
            last_opening = stack.pop()
            if last_opening != expected_opening:
                return False

    return len(stack) == 0