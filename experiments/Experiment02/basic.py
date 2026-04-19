def solution(n):
	if n < 2:
		return []

	primes = []

	for candidate in range(2, n + 1):
		is_prime = True

		for divisor in range(2, int(candidate ** 0.5) + 1):
			if candidate % divisor == 0:
				is_prime = False
				break

		if is_prime:
			primes.append(candidate)

	return primes
