def solution(list1, list2):
    result = []
    seen = set()

    for item in list1 + list2:
        if item not in seen:
            seen.add(item)
            result.append(item)

    return result