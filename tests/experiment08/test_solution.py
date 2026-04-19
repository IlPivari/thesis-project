from __future__ import annotations

from pathlib import Path

import pytest

from tests._shared import load_function_from_env


def test_counts_lines_in_an_empty_file(tmp_path: Path) -> None:
    fn = load_function_from_env()
    file_path = tmp_path / "empty.txt"
    file_path.write_text("", encoding="utf-8")

    assert fn(file_path) == 0


def test_counts_a_trailing_partial_line(tmp_path: Path) -> None:
    fn = load_function_from_env()
    file_path = tmp_path / "partial.txt"
    file_path.write_text("alpha\nbeta\ngamma", encoding="utf-8")

    assert fn(file_path) == 3


def test_counts_blank_lines_and_windows_newlines(tmp_path: Path) -> None:
    fn = load_function_from_env()
    file_path = tmp_path / "windows.txt"
    file_path.write_bytes(b"alpha\r\n\r\nbeta\r\n")

    assert fn(file_path) == 3


def test_accepts_path_objects(tmp_path: Path) -> None:
    fn = load_function_from_env()
    file_path = tmp_path / "path-object.txt"
    file_path.write_text("uno\ndue\ntre\nquattro\n", encoding="utf-8")

    assert fn(file_path) == 4


def test_missing_file_raises_file_not_found_error(tmp_path: Path) -> None:
    fn = load_function_from_env()

    with pytest.raises(FileNotFoundError):
        fn(tmp_path / "missing.txt")


def test_directory_input_raises_os_error(tmp_path: Path) -> None:
    fn = load_function_from_env()
    directory_path = tmp_path / "folder"
    directory_path.mkdir()

    with pytest.raises(OSError):
        fn(directory_path)