def solution(n):
	if n < 2:
		return

	yield 2

	if n < 3:
		return

	sieve_size = ((n - 3) // 2) + 1
	sieve = bytearray(b"\x01") * sieve_size
	limit = int(n ** 0.5)
	max_index = (limit - 3) // 2

	for index in range(max_index + 1):
		if not sieve[index]:
			continue

		prime = 2 * index + 3
		start = (prime * prime - 3) // 2
		sieve[start::prime] = b"\x00" * (((sieve_size - start - 1) // prime) + 1)

	for index, is_prime in enumerate(sieve):
		if is_prime:
			yield 2 * index + 3
