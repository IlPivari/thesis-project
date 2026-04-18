from __future__ import annotations

import importlib.util
import os
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType


@dataclass(frozen=True)
class TargetSpec:
    file_path: Path
    function_name: str


def load_target_from_env() -> TargetSpec:
    target_file = os.environ.get("TARGET_FILE")
    if not target_file:
        raise RuntimeError("Missing env var TARGET_FILE")

    function_name = os.environ.get("TARGET_FUNCTION", "solution")
    return TargetSpec(file_path=Path(target_file), function_name=function_name)


def load_module_from_path(path: Path) -> ModuleType:
    if not path.exists():
        raise FileNotFoundError(str(path))

    spec = importlib.util.spec_from_file_location(path.stem, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not import from: {path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_function_from_env():
    target = load_target_from_env()
    module = load_module_from_path(target.file_path)

    fn = getattr(module, target.function_name, None)
    if fn is None:
        raise AttributeError(f"Function '{target.function_name}' not found in {target.file_path}")
    return fn
