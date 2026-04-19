def solution(items, sort_key, reverse=False):
	"""Return a list of dictionaries sorted by the given key."""
	return sorted(items, key=lambda item: item[sort_key], reverse=reverse)
