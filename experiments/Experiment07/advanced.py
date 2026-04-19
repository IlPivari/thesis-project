def solution(sentence: str) -> str:
    """Reverse word order while preserving the original whitespace layout."""
    if not sentence:
        return sentence

    parts: list[tuple[bool, str]] = []
    start = 0
    in_space = sentence[0].isspace()

    for index in range(1, len(sentence)):
        current_is_space = sentence[index].isspace()
        if current_is_space != in_space:
            parts.append((in_space, sentence[start:index]))
            start = index
            in_space = current_is_space

    parts.append((in_space, sentence[start:]))

    words = [text for is_space, text in parts if not is_space]
    if len(words) < 2:
        return sentence

    words.reverse()
    word_index = 0
    rebuilt: list[str] = []

    for is_space, text in parts:
        if is_space:
            rebuilt.append(text)
        else:
            rebuilt.append(words[word_index])
            word_index += 1

    return "".join(rebuilt)