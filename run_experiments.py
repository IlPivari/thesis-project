from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
import ast
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Literal


ROOT = Path(__file__).resolve().parent
EXPERIMENTS_DIR = ROOT / "experiments"
TESTS_DIR = ROOT / "tests"
MANIFEST_PATH = ROOT / "experiments_manifest.json"
RESULTS_DIR = ROOT / "results"

Variant = Literal["basic", "advanced"]


@dataclass
class CommandResult:
    ok: bool
    returncode: int
    stdout: str
    stderr: str
    seconds: float


@dataclass
class MetricResult:
    ok: bool
    score: float
    details: dict[str, Any]


@dataclass
class VariantResult:
    variant: Variant
    file: str
    metrics: dict[str, MetricResult]


@dataclass
class ExperimentResult:
    experiment_id: str
    title: str
    function_name: str
    results: dict[Variant, VariantResult]


def _run(cmd: list[str], env: dict[str, str] | None = None, cwd: Path | None = None) -> CommandResult:
    effective_env = os.environ.copy()
    effective_env["PYTHONDONTWRITEBYTECODE"] = "1"
    if env:
        effective_env.update(env)

    start = time.perf_counter()
    completed = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        env=effective_env,
        text=True,
        capture_output=True,
    )
    end = time.perf_counter()
    return CommandResult(
        ok=completed.returncode == 0,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        seconds=end - start,
    )


def _python() -> str:
    return sys.executable


def _short(s: str, max_chars: int = 1200) -> str:
    s = s.strip()
    if len(s) <= max_chars:
        return s
    return s[: max_chars - 30] + "\n... [truncated] ..."


def _load_manifest() -> list[dict[str, Any]]:
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    experiments = data.get("experiments")
    if not isinstance(experiments, list):
        raise ValueError("Invalid manifest: missing 'experiments' list")
    return experiments


def _experiment_paths(experiment_id: str) -> tuple[Path, Path]:
    exp_dir = EXPERIMENTS_DIR / experiment_id
    test_dir = TESTS_DIR / experiment_id
    if not test_dir.exists():
        lower_test_dir = TESTS_DIR / experiment_id.lower()
        if lower_test_dir.exists():
            test_dir = lower_test_dir
    return exp_dir, test_dir


def _validate_experiment_folder(exp_dir: Path) -> None:
    if not exp_dir.exists():
        raise FileNotFoundError(str(exp_dir))

    files = sorted([p.name for p in exp_dir.iterdir() if p.is_file()])
    expected = ["advanced.py", "basic.py"]
    if files != expected:
        raise RuntimeError(
            f"{exp_dir} must contain only {expected} (found: {files})"
        )


def _metric_syntax(file_path: Path) -> MetricResult:
    start = time.perf_counter()
    try:
        source = file_path.read_text(encoding="utf-8")
        compile(source, str(file_path), "exec")
        ok = True
        error = ""
    except SyntaxError as e:
        ok = False
        error = f"{e.msg} (line {e.lineno}, col {e.offset})"
    except Exception as e:  # pragma: no cover
        ok = False
        error = repr(e)
    end = time.perf_counter()
    return MetricResult(ok=ok, score=10.0 if ok else 0.0, details={"seconds": end - start, "error": error})


def _metric_smoke_run(file_path: Path, function_name: str, smoke_call: dict[str, Any]) -> MetricResult:
    args = smoke_call.get("args", [])
    kwargs = smoke_call.get("kwargs", {})

    code = (
        "import importlib.util, json, sys;"
        "from pathlib import Path;"
        "p=Path(sys.argv[1]); fn_name=sys.argv[2];"
        "spec=importlib.util.spec_from_file_location(p.stem, str(p));"
        "m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m);"
        "fn=getattr(m, fn_name);"
        "args=json.loads(sys.argv[3]); kwargs=json.loads(sys.argv[4]);"
        "out=fn(*args, **kwargs);"
        "print(repr(out))"
    )

    cmd = [_python(), "-c", code, str(file_path), function_name, json.dumps(args), json.dumps(kwargs)]
    res = _run(cmd, cwd=ROOT)
    return MetricResult(
        ok=res.ok,
        score=10.0 if res.ok else 0.0,
        details={
            "cmd": cmd[:3] + ["<file>", function_name, "<args>", "<kwargs>"] ,
            "seconds": res.seconds,
            "stdout": _short(res.stdout),
            "stderr": _short(res.stderr),
        },
    )


def _metric_documentation(file_path: Path, function_name: str) -> MetricResult:
    """Check whether the target function contains a non-empty docstring.

    This is intentionally AST-based to avoid executing user code.
    """

    start = time.perf_counter()
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))
    except Exception as e:
        end = time.perf_counter()
        return MetricResult(
            ok=False,
            score=0.0,
            details={"seconds": end - start, "error": repr(e)},
        )

    doc: str | None = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
            doc = ast.get_docstring(node)
            break

    ok = bool(doc and doc.strip())
    end = time.perf_counter()
    preview = ""
    if doc:
        preview = doc.strip().replace("\r\n", "\n")
        preview = preview[:300]

    return MetricResult(
        ok=ok,
        score=10.0 if ok else 0.0,
        details={
            "seconds": end - start,
            "has_docstring": ok,
            "docstring_len": len(doc.strip()) if doc else 0,
            "docstring_preview": preview,
        },
    )


def _parse_pytest_counts(output: str) -> dict[str, int]:
    """Best-effort parser for pytest summary line.

    Expects a tail like: '3 passed, 1 failed, 1 error in 0.12s'
    Returns dict with keys: passed, failed, error, skipped, xfailed, xpassed.
    Missing keys default to 0.
    """

    counts = {"passed": 0, "failed": 0, "error": 0, "skipped": 0, "xfailed": 0, "xpassed": 0}
    # Look across the full output; the summary is usually at the end.
    for key in list(counts.keys()):
        m = re.search(rf"(\d+)\s+{key}", output)
        if m:
            counts[key] = int(m.group(1))
    return counts


def _score_tests_from_output(stdout: str, stderr: str, returncode: int) -> tuple[float, dict[str, Any]]:
    text = (stdout or "") + "\n" + (stderr or "")
    counts = _parse_pytest_counts(text)
    total = counts["passed"] + counts["failed"] + counts["error"] + counts["xpassed"]

    # If pytest didn't print a standard summary, fall back to OK/KO.
    if total <= 0:
        score = 10.0 if returncode == 0 else 0.0
    else:
        score = 10.0 * (counts["passed"] / total)

    details = {"counts": counts, "total": total}
    return score, details


def _metric_pytest(file_path: Path, function_name: str, test_dir: Path) -> MetricResult:
    env = os.environ.copy()
    env["TARGET_FILE"] = str(file_path)
    env["TARGET_FUNCTION"] = function_name

    cmd = [_python(), "-m", "pytest", str(test_dir)]
    res = _run(cmd, env=env, cwd=ROOT)

    score, score_details = _score_tests_from_output(res.stdout, res.stderr, res.returncode)
    return MetricResult(
        ok=res.ok,
        score=score,
        details={
            "cmd": cmd,
            "seconds": res.seconds,
            "stdout": _short(res.stdout),
            "stderr": _short(res.stderr),
            **score_details,
        },
    )


def _metric_ruff(file_path: Path) -> MetricResult:
    cmd = [_python(), "-m", "ruff", "check", str(file_path)]
    res = _run(cmd, cwd=ROOT)
    return MetricResult(
        ok=res.ok,
        score=10.0 if res.ok else 0.0,
        details={"cmd": cmd, "seconds": res.seconds, "stdout": _short(res.stdout), "stderr": _short(res.stderr)},
    )


def _metric_mypy(file_path: Path) -> MetricResult:
    cmd = [_python(), "-m", "mypy", str(file_path)]
    res = _run(cmd, cwd=ROOT)
    return MetricResult(
        ok=res.ok,
        score=10.0 if res.ok else 0.0,
        details={"cmd": cmd, "seconds": res.seconds, "stdout": _short(res.stdout), "stderr": _short(res.stderr)},
    )


def _complexity_score_from_cc(cc_max: float | int | None) -> float | None:
    if cc_max is None:
        return None

    if cc_max <= 2:
        return 10.0
    if cc_max <= 4:
        return 8.0
    if cc_max <= 6:
        return 6.0
    if cc_max <= 8:
        return 4.0
    if cc_max <= 10:
        return 2.0
    return 0.0


def _complexity_score_from_mi(mi_value: float | int | None) -> float | None:
    if mi_value is None:
        return None

    return max(0.0, min(10.0, float(mi_value) / 10.0))


def _metric_radon(file_path: Path) -> MetricResult:
    cmd_cc = [_python(), "-m", "radon", "cc", "-j", str(file_path)]
    res_cc = _run(cmd_cc, cwd=ROOT)
    cc_max = None
    if res_cc.ok:
        try:
            data = json.loads(res_cc.stdout)
            blocks = data.get(str(file_path), [])
            if blocks:
                cc_max = max(b.get("complexity", 0) for b in blocks)
        except Exception:
            cc_max = None

    cmd_mi = [_python(), "-m", "radon", "mi", "-j", str(file_path)]
    res_mi = _run(cmd_mi, cwd=ROOT)
    mi = None
    if res_mi.ok:
        try:
            data = json.loads(res_mi.stdout)
            mi = data.get(str(file_path), {}).get("mi")
        except Exception:
            mi = None

    ok = res_cc.ok and res_mi.ok

    # Complexity scoring (0..10): combine worst-block cyclomatic complexity
    # with maintainability index, keeping CC slightly dominant for short files.
    score: float
    cc_score = _complexity_score_from_cc(cc_max)
    mi_score = _complexity_score_from_mi(mi)
    if cc_score is not None and mi_score is not None:
        score = round((0.6 * cc_score) + (0.4 * mi_score), 2)
    elif cc_score is not None:
        score = cc_score
    elif mi_score is not None:
        score = mi_score
    else:
        score = 10.0 if ok else 0.0

    return MetricResult(
        ok=ok,
        score=score,
        details={
            "cc": {"cmd": cmd_cc, "seconds": res_cc.seconds, "stdout": _short(res_cc.stdout), "stderr": _short(res_cc.stderr)},
            "mi": {"cmd": cmd_mi, "seconds": res_mi.seconds, "stdout": _short(res_mi.stdout), "stderr": _short(res_mi.stderr)},
            "cc_max": cc_max,
            "cc_score": cc_score,
            "mi_value": mi,
            "mi_score": mi_score,
            "weights": {"cc": 0.6, "mi": 0.4},
        },
    )


def _metric_bandit(file_path: Path) -> MetricResult:
    cmd = [_python(), "-m", "bandit", "-q", "-f", "json", str(file_path)]
    res = _run(cmd, cwd=ROOT)

    issues = None
    sev_counts: dict[str, int] = {}
    if res.stdout.strip():
        try:
            data = json.loads(res.stdout)
            results = data.get("results", [])
            issues = len(results)
            for r in results:
                sev = str(r.get("issue_severity", "UNKNOWN"))
                sev_counts[sev] = sev_counts.get(sev, 0) + 1
        except Exception:
            issues = None

    tool_ok = res.returncode in (0, 1)
    ok = tool_ok and (issues == 0)
    return MetricResult(
        ok=ok,
        score=10.0 if ok else 0.0,
        details={
            "cmd": cmd,
            "seconds": res.seconds,
            "returncode": res.returncode,
            "issues": issues,
            "severity_counts": sev_counts,
            "stdout": _short(res.stdout),
            "stderr": _short(res.stderr),
        },
    )


def _metric_performance(file_path: Path, function_name: str, smoke_call: dict[str, Any]) -> MetricResult:
    """Measure average time per call (seconds) in a separate process.

    Uses the manifest smoke_call args/kwargs. The scoring is computed later, relative
    between basic/advanced (fastest gets 10).
    """

    args = smoke_call.get("args", [])
    kwargs = smoke_call.get("kwargs", {})

    code = """\
import importlib.util
import json
import sys
import time
from pathlib import Path

p = Path(sys.argv[1])
fn_name = sys.argv[2]

spec = importlib.util.spec_from_file_location(p.stem, str(p))
m = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(m)

fn = getattr(m, fn_name)
args = json.loads(sys.argv[3])
kwargs = json.loads(sys.argv[4])

# Warm-up
fn(*args, **kwargs)

loops = 1
target = 0.25
max_loops = 1_000_000

while True:
    t0 = time.perf_counter()
    for _ in range(loops):
        fn(*args, **kwargs)
    elapsed = time.perf_counter() - t0
    if elapsed >= target or loops >= max_loops:
        break
    loops *= 2

avg = elapsed / loops
print(avg)
"""

    cmd = [_python(), "-c", code, str(file_path), function_name, json.dumps(args), json.dumps(kwargs)]
    res = _run(cmd, cwd=ROOT)
    avg_s = None
    if res.ok:
        try:
            avg_s = float(res.stdout.strip().splitlines()[-1])
        except Exception:
            avg_s = None

    return MetricResult(
        ok=res.ok and (avg_s is not None),
        # score will be assigned later after comparing variants
        score=0.0,
        details={
            "cmd": cmd[:3] + ["<file>", function_name, "<args>", "<kwargs>"],
            "seconds": res.seconds,
            "avg_seconds_per_call": avg_s,
            "stdout": _short(res.stdout),
            "stderr": _short(res.stderr),
        },
    )


def _evaluate_variant(
    *,
    experiment_id: str,
    title: str,
    variant: Variant,
    file_path: Path,
    function_name: str,
    smoke_call: dict[str, Any],
    test_dir: Path,
) -> VariantResult:
    metrics: dict[str, MetricResult] = {}

    # Keep experiment folders clean (the thesis constraint is: only 2 files per experiment).
    # Some tools/import flows can generate bytecode cache; remove it before each run.
    pycache = file_path.parent / "__pycache__"
    if pycache.exists() and pycache.is_dir():
        shutil.rmtree(pycache, ignore_errors=True)

    metrics["syntax"] = _metric_syntax(file_path)
    metrics["execution"] = _metric_smoke_run(file_path, function_name, smoke_call)
    metrics["documentation"] = _metric_documentation(file_path, function_name)
    metrics["test"] = _metric_pytest(file_path, function_name, test_dir)

    metrics["lint"] = _metric_ruff(file_path)
    metrics["type_checking"] = _metric_mypy(file_path)
    metrics["complexity"] = _metric_radon(file_path)
    metrics["basic_security"] = _metric_bandit(file_path)
    metrics["performance"] = _metric_performance(file_path, function_name, smoke_call)

    return VariantResult(variant=variant, file=str(file_path), metrics=metrics)


def _print_summary(exp: ExperimentResult) -> None:
    print(f"\n== {exp.experiment_id} — {exp.title} ==")

    metric_names = [
        "syntax",
        "execution",
        "documentation",
        "test",
        "lint",
        "type_checking",
        "complexity",
        "basic_security",
        "performance",
    ]

    for metric in metric_names:
        b = exp.results["basic"].metrics[metric]
        a = exp.results["advanced"].metrics[metric]

        extra = ""
        if metric == "complexity":
            b_cc = b.details.get("cc_max")
            a_cc = a.details.get("cc_max")
            b_mi = b.details.get("mi_value")
            a_mi = a.details.get("mi_value")
            if b_cc is not None or a_cc is not None or b_mi is not None or a_mi is not None:
                extra = (
                    "  ("
                    f"cc_max basic={b_cc}, advanced={a_cc}; "
                    f"mi basic={b_mi}, advanced={a_mi}"
                    ")"
                )
        if metric == "basic_security":
            b_issues = b.details.get("issues")
            a_issues = a.details.get("issues")
            if b_issues is not None or a_issues is not None:
                extra = f"  (issues basic={b_issues}, advanced={a_issues})"
        if metric == "performance":
            b_t = b.details.get("avg_seconds_per_call")
            a_t = a.details.get("avg_seconds_per_call")
            if b_t is not None or a_t is not None:
                extra = f"  (avg_s/call basic={b_t}, advanced={a_t})"

        print(f"- {metric:14} basic={b.score:4.1f}/10 | advanced={a.score:4.1f}/10{extra}")


def main() -> int:
    if not MANIFEST_PATH.exists():
        print(f"Missing manifest: {MANIFEST_PATH}", file=sys.stderr)
        return 2

    RESULTS_DIR.mkdir(exist_ok=True)

    experiments = _load_manifest()
    all_results: list[ExperimentResult] = []

    for exp in experiments:
        experiment_id = str(exp["id"])
        title = str(exp.get("title", experiment_id))
        function_name = str(exp.get("function_name", "solution"))
        smoke_call = exp.get("smoke_call", {"args": [], "kwargs": {}})

        exp_dir, test_dir = _experiment_paths(experiment_id)
        _validate_experiment_folder(exp_dir)
        if not test_dir.exists():
            raise FileNotFoundError(f"Missing test dir: {test_dir}")

        basic_file = exp_dir / "basic.py"
        advanced_file = exp_dir / "advanced.py"

        basic = _evaluate_variant(
            experiment_id=experiment_id,
            title=title,
            variant="basic",
            file_path=basic_file,
            function_name=function_name,
            smoke_call=smoke_call,
            test_dir=test_dir,
        )
        advanced = _evaluate_variant(
            experiment_id=experiment_id,
            title=title,
            variant="advanced",
            file_path=advanced_file,
            function_name=function_name,
            smoke_call=smoke_call,
            test_dir=test_dir,
        )

        exp_result = ExperimentResult(
            experiment_id=experiment_id,
            title=title,
            function_name=function_name,
            results={"basic": basic, "advanced": advanced},
        )

        # Assign relative performance scores (fastest gets 10, slower scales by ratio).
        b_perf = exp_result.results["basic"].metrics["performance"]
        a_perf = exp_result.results["advanced"].metrics["performance"]
        b_t = b_perf.details.get("avg_seconds_per_call")
        a_t = a_perf.details.get("avg_seconds_per_call")
        if isinstance(b_t, (int, float)) and isinstance(a_t, (int, float)) and b_t > 0 and a_t > 0:
            best = min(float(b_t), float(a_t))
            b_perf.score = min(10.0, 10.0 * best / float(b_t))
            a_perf.score = min(10.0, 10.0 * best / float(a_t))
        else:
            b_perf.score = 10.0 if b_perf.ok else 0.0
            a_perf.score = 10.0 if a_perf.ok else 0.0

        all_results.append(exp_result)
        _print_summary(exp_result)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = RESULTS_DIR / f"results_{ts}.json"
    payload = {
        "timestamp": ts,
        "python": sys.version,
        "tooling": {
            "ruff": shutil.which("ruff"),
            "mypy": shutil.which("mypy"),
            "radon": shutil.which("radon"),
            "bandit": shutil.which("bandit"),
        },
        "results": [asdict(r) for r in all_results],
    }
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nSaved detailed results to: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
