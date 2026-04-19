def solution(sentence: str) -> str:
    return " ".join(sentence.split()[::-1])