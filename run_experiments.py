from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
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
    return MetricResult(ok=ok, details={"seconds": end - start, "error": error})


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
        details={
            "cmd": cmd[:3] + ["<file>", function_name, "<args>", "<kwargs>"] ,
            "seconds": res.seconds,
            "stdout": _short(res.stdout),
            "stderr": _short(res.stderr),
        },
    )


def _metric_pytest(file_path: Path, function_name: str, test_dir: Path) -> MetricResult:
    env = os.environ.copy()
    env["TARGET_FILE"] = str(file_path)
    env["TARGET_FUNCTION"] = function_name

    cmd = [_python(), "-m", "pytest", str(test_dir)]
    res = _run(cmd, env=env, cwd=ROOT)
    return MetricResult(
        ok=res.ok,
        details={
            "cmd": cmd,
            "seconds": res.seconds,
            "stdout": _short(res.stdout),
            "stderr": _short(res.stderr),
        },
    )


def _metric_coverage(file_path: Path, function_name: str, test_dir: Path, data_file: Path) -> MetricResult:
    env = os.environ.copy()
    env["TARGET_FILE"] = str(file_path)
    env["TARGET_FUNCTION"] = function_name
    env["COVERAGE_FILE"] = str(data_file)

    # If coverage is configured with parallel mode, it will create data files with
    # extra suffixes (pid/machine/random). We need to combine them back into the
    # base file before exporting a report.
    for p in [data_file, *data_file.parent.glob(data_file.name + ".*")]:
        try:
            p.unlink()
        except FileNotFoundError:
            pass

    cmd_run = [_python(), "-m", "coverage", "run", "--branch", "-m", "pytest", str(test_dir)]
    run_res = _run(cmd_run, env=env, cwd=ROOT)
    if not run_res.ok:
        return MetricResult(
            ok=False,
            details={
                "cmd": cmd_run,
                "seconds": run_res.seconds,
                "returncode": run_res.returncode,
                "stdout": _short(run_res.stdout),
                "stderr": _short(run_res.stderr),
            },
        )

    cmd_combine = [_python(), "-m", "coverage", "combine"]
    combine_res = _run(cmd_combine, env=env, cwd=ROOT)
    if not combine_res.ok:
        return MetricResult(
            ok=False,
            details={
                "run": {"cmd": cmd_run, "seconds": run_res.seconds, "returncode": run_res.returncode},
                "combine": {
                    "cmd": cmd_combine,
                    "seconds": combine_res.seconds,
                    "returncode": combine_res.returncode,
                    "stdout": _short(combine_res.stdout),
                    "stderr": _short(combine_res.stderr),
                },
            },
        )

    json_out = data_file.with_suffix(data_file.suffix + ".json")
    cmd_json = [_python(), "-m", "coverage", "json", "--data-file", str(data_file), "-o", str(json_out)]
    json_res = _run(cmd_json, env=env, cwd=ROOT)
    pct = None
    if json_res.ok and json_out.exists():
        try:
            cov = json.loads(json_out.read_text(encoding="utf-8"))
            pct = cov.get("totals", {}).get("percent_covered")
        except Exception:
            pct = None

    return MetricResult(
        ok=json_res.ok,
        details={
            "run": {
                "cmd": cmd_run,
                "seconds": run_res.seconds,
                "returncode": run_res.returncode,
                "stdout": _short(run_res.stdout),
                "stderr": _short(run_res.stderr),
            },
            "combine": {
                "cmd": cmd_combine,
                "seconds": combine_res.seconds,
                "returncode": combine_res.returncode,
                "stdout": _short(combine_res.stdout),
                "stderr": _short(combine_res.stderr),
            },
            "json": {
                "cmd": cmd_json,
                "seconds": json_res.seconds,
                "returncode": json_res.returncode,
                "stdout": _short(json_res.stdout),
                "stderr": _short(json_res.stderr),
            },
            "percent_covered": pct,
            "coverage_json": str(json_out),
        },
    )


def _metric_ruff(file_path: Path) -> MetricResult:
    cmd = [_python(), "-m", "ruff", "check", str(file_path)]
    res = _run(cmd, cwd=ROOT)
    return MetricResult(ok=res.ok, details={"cmd": cmd, "seconds": res.seconds, "stdout": _short(res.stdout)})


def _metric_mypy(file_path: Path) -> MetricResult:
    cmd = [_python(), "-m", "mypy", str(file_path)]
    res = _run(cmd, cwd=ROOT)
    return MetricResult(ok=res.ok, details={"cmd": cmd, "seconds": res.seconds, "stdout": _short(res.stdout)})


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
    return MetricResult(
        ok=ok,
        details={
            "cc": {"cmd": cmd_cc, "seconds": res_cc.seconds, "stdout": _short(res_cc.stdout), "stderr": _short(res_cc.stderr)},
            "mi": {"cmd": cmd_mi, "seconds": res_mi.seconds, "stdout": _short(res_mi.stdout), "stderr": _short(res_mi.stderr)},
            "cc_max": cc_max,
            "mi_value": mi,
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
    metrics["test"] = _metric_pytest(file_path, function_name, test_dir)

    cov_data = ROOT / f".coverage.{experiment_id}.{variant}"
    metrics["coverage"] = _metric_coverage(file_path, function_name, test_dir, cov_data)

    metrics["lint"] = _metric_ruff(file_path)
    metrics["type_checking"] = _metric_mypy(file_path)
    metrics["complexity"] = _metric_radon(file_path)
    metrics["basic_security"] = _metric_bandit(file_path)

    return VariantResult(variant=variant, file=str(file_path), metrics=metrics)


def _print_summary(exp: ExperimentResult) -> None:
    print(f"\n== {exp.experiment_id} — {exp.title} ==")

    def fmt_ok(v: bool) -> str:
        return "OK" if v else "FAIL"

    metric_names = [
        "syntax",
        "execution",
        "test",
        "coverage",
        "lint",
        "type_checking",
        "complexity",
        "basic_security",
    ]

    for metric in metric_names:
        b = exp.results["basic"].metrics[metric]
        a = exp.results["advanced"].metrics[metric]

        extra = ""
        if metric == "coverage":
            b_pct = b.details.get("percent_covered")
            a_pct = a.details.get("percent_covered")
            if b_pct is not None or a_pct is not None:
                extra = f"  (basic={b_pct}%, advanced={a_pct}%)"
        if metric == "complexity":
            b_cc = b.details.get("cc_max")
            a_cc = a.details.get("cc_max")
            if b_cc is not None or a_cc is not None:
                extra = f"  (cc_max basic={b_cc}, advanced={a_cc})"
        if metric == "basic_security":
            b_issues = b.details.get("issues")
            a_issues = a.details.get("issues")
            if b_issues is not None or a_issues is not None:
                extra = f"  (issues basic={b_issues}, advanced={a_issues})"

        print(f"- {metric:14} basic={fmt_ok(b.ok):4} | advanced={fmt_ok(a.ok):4}{extra}")


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
            "coverage": shutil.which("coverage"),
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
