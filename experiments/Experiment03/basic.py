def solution(values, target):
	left = 0
	right = len(values) - 1

	while left <= right:
		middle = (left + right) // 2
		current = values[middle]

		if current == target:
			return middle

		if current < target:
			left = middle + 1
		else:
			right = middle - 1

	return -1
