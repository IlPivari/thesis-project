from __future__ import annotations

from os import PathLike


def solution(file_path: str | PathLike[str]) -> int:
	"""Return the number of lines in a text file.

	The function reads the file incrementally to keep memory usage low and
	counts line separators in binary chunks for better performance on large
	files. A trailing partial line without a final newline is counted as a
	valid line.
	"""
	try:
		with open(file_path, "rb") as file:
			line_count = 0
			last_chunk_ended_with_newline = True

			for chunk in iter(lambda: file.read(1024 * 1024), b""):
				line_count += chunk.count(b"\n")
				last_chunk_ended_with_newline = chunk.endswith(b"\n")

			if line_count == 0:
				return 0 if last_chunk_ended_with_newline else 1

			return line_count if last_chunk_ended_with_newline else line_count + 1
	except FileNotFoundError as exc:
		raise FileNotFoundError(f"File non trovato: {file_path}") from exc
	except PermissionError as exc:
		raise PermissionError(f"Permessi insufficienti per leggere il file: {file_path}") from exc
	except IsADirectoryError as exc:
		raise IsADirectoryError(f"Il percorso indicato non è un file: {file_path}") from exc
	except OSError as exc:
		raise OSError(f"Impossibile leggere il file '{file_path}': {exc}") from exc
