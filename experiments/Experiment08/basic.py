def solution(file_path: str) -> int:
    with open(file_path, "r", encoding="utf-8") as file:
        return sum(1 for _ in file)