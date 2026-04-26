def solution(numbers):
	"""Sort a permutation of the integers 1..2000 using bucket sort.

    Args:
		numbers: Iterable of exactly 2000 distinct integers in the range 1..2000.

    Returns:
		A new sorted list containing the integers from 1 to 2000.
		
	Raises:
		ValueError: If the input does not contain exactly 2000 elements.
	"""
	if len(numbers) != 2000:
		raise ValueError("numbers must contain exactly 2000 values")
	
	result = [0] * 2000
	output = result

	for value in numbers:
		output[value - 1] = value

	return result