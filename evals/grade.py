#!/usr/bin/env python3
"""Prepare an arm folder for the Go skills eval, or grade one. See evals/README.md."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from collections import Counter
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath
from typing import NamedTuple
from urllib.parse import parse_qs, urlsplit

TASKS = Path(__file__).resolve().parent / "tasks"
KINDS = ("write", "port", "review")
LINE_SLACK = 3
DEFAULT_TIME_LIMIT = 10.0
BUILD_TIME_LIMIT = 600.0
SCORE_KEYS = (
    "buildFailures", "casesPassed", "casesTotal", "lintIssues", "fixDiffLines",
    "portPassed", "portTotal", "reviewFound", "reviewTotal", "reviewFalsePositives",
)

ITEM = b'{"id": 7, "name": "widget", "tags": ["blue", "small"], "stock": 3}'
BODIES = {
    "widget": ITEM,
    "gadget": b'{"id": 12, "name": "gadget", "tags": []}',
    "truncated": b'{"id": 7, "name": "wid',
    "wrong-type": b'{"id": "7", "name": "widget", "tags": []}',
}


class Plan(NamedTuple):
    """What the local test server sends for one request."""

    status: int
    body: bytes
    delay: float = 0.0
    slot: tuple[str, int] | None = None


class RunResult(NamedTuple):
    exit_code: int | None
    stdout: str


class Case(NamedTuple):
    """One run of a program: its inputs and the stdout and exit code it must give."""

    name: str
    stdout: str
    exitCode: int  # noqa: N815 (the cases.json key)
    args: list[str] = []
    stdin: str = ""
    files: dict[str, str] = {}
    timeLimit: float = DEFAULT_TIME_LIMIT  # noqa: N815
    stdoutFormat: str = "text"  # noqa: N815


class Defect(NamedTuple):
    """One seeded defect in a review module, from key.json."""

    file: str
    firstLine: int  # noqa: N815 (the key.json key)
    lastLine: int  # noqa: N815
    defect_class: str


@dataclass
class ModuleScore:
    built: bool
    passed: int = 0
    total: int = 0
    lint: int = 0
    fix: int = 0
    linted: bool = True  # False when golangci-lint gave no report, which counts as a build failure


# Pure decisions.


def plan_response(path: str, query: dict[str, list[str]], hits: int) -> Plan:
    """Decide the response to a GET of path, given how many earlier requests hit it."""
    delay = int(query.get("delay", ["0"])[0]) / 1000
    match path.strip("/").split("/"):
        case ["seq", _key, codes]:
            statuses = [int(code) for code in codes.split(",")]
            status = statuses[min(hits, len(statuses) - 1)]
            body = ITEM if status == 200 else f"status {status}\n".encode()
            return Plan(status, body, delay)
        case ["body", name] if name in BODIES:
            return Plan(200, BODIES[name], delay)
        case ["status", code]:
            return Plan(int(code), f"status {code}\n".encode(), delay)
        case ["slot", group, limit]:
            return Plan(200, b"ok\n", delay, (group, int(limit)))
        case _:
            return Plan(404, b"no route\n", delay)


def substitute(text: str, server: str) -> str:
    return text.replace("{SERVER}", server)


def output_matches(expected: str, actual: str, fmt: str) -> bool:
    if fmt != "json":
        return expected == actual
    try:
        return json.loads(expected) == json.loads(actual)
    except ValueError:
        return False


def case_passed(case: Case, result: RunResult, server: str) -> bool:
    return result.exit_code == case.exitCode and output_matches(
        substitute(case.stdout, server), result.stdout, case.stdoutFormat
    )


def is_changed_line(line: str) -> bool:
    return line[:1] in ("+", "-") and not line.startswith(("+++", "---"))


def count_diff_lines(diff: str) -> int:
    """Count the changed lines in a unified diff, without the file headers."""
    return sum(map(is_changed_line, diff.splitlines()))


def count_lint_issues(report: str) -> int | None:
    try:
        return len(json.loads(report).get("Issues") or [])
    except (ValueError, AttributeError):
        return None


def reject_constant(token: str) -> None:
    raise ValueError(f"invalid JSON constant: {token}")


def parse_findings(data: bytes) -> tuple[list, str | None]:
    """Return (findings, problem). A file that is not a strict UTF-8 JSON list gives no findings and a problem."""
    try:
        findings = json.loads(data.decode("utf-8"), parse_constant=reject_constant)
    except ValueError as err:
        return [], f"not valid JSON: {err}"
    if not isinstance(findings, list):
        return [], "not a JSON list"
    return findings, None


def same_file(reported: str, expected: str) -> bool:
    path = PurePosixPath(reported.replace("\\", "/")).as_posix().removeprefix("./")
    return path == expected or path.endswith("/" + expected)


def finding_matches(finding: object, defect: Defect) -> bool:
    if not isinstance(finding, dict):
        return False
    file, line, summary = finding.get("file"), finding.get("line"), finding.get("summary")
    if not isinstance(file, str) or not isinstance(line, int) or isinstance(line, bool):
        return False
    if not isinstance(summary, str) or not summary.strip():
        return False
    return same_file(file, defect.file) and (
        defect.firstLine - LINE_SLACK <= line <= defect.lastLine + LINE_SLACK
    )


def score_review(findings: list, defects: list[Defect]) -> tuple[int, int]:
    """Return the defects some finding matches, and the findings that match no defect."""
    found = sum(1 for d in defects if any(finding_matches(f, d) for f in findings))
    false_positives = sum(1 for f in findings if not any(finding_matches(f, d) for d in defects))
    return found, false_positives


def summarize(modules: dict[tuple[str, str], ModuleScore], review: list[tuple[int, int, int]]) -> dict:
    def total(kind: str, attr: str) -> int:
        return sum(getattr(m, attr) for (k, _), m in modules.items() if k == kind)

    return {
        "buildFailures": sum(1 for m in modules.values() if not (m.built and m.linted)),
        "casesPassed": total("write", "passed"),
        "casesTotal": total("write", "total"),
        "lintIssues": sum(m.lint for m in modules.values()),
        "fixDiffLines": sum(m.fix for m in modules.values()),
        "portPassed": total("port", "passed"),
        "portTotal": total("port", "total"),
        "reviewFound": sum(found for found, _, _ in review),
        "reviewTotal": sum(n for _, _, n in review),
        "reviewFalsePositives": sum(fp for _, fp, _ in review),
    }


# Files, processes and the network.


def task_dirs(kind: str) -> list[Path]:
    return sorted(p for p in (TASKS / kind).iterdir() if p.is_dir())


def load_cases(path: Path) -> list[Case]:
    cases = []
    for raw in json.loads(path.read_text(encoding="utf-8")):
        cases.append(Case(**raw))
    return cases


def to_defect(raw: dict) -> Defect:
    return Defect(raw["file"], raw["firstLine"], raw["lastLine"], raw["class"])


def load_defects(path: Path) -> list[Defect]:
    return list(map(to_defect, json.loads(path.read_text(encoding="utf-8"))))


def go_env() -> dict[str, str]:
    return {**os.environ, "GOTOOLCHAIN": "local"}


@dataclass
class ServerState:
    lock: threading.Lock = field(default_factory=threading.Lock)
    hits: Counter = field(default_factory=Counter)
    in_flight: Counter = field(default_factory=Counter)


class Handler(BaseHTTPRequestHandler):
    server: TestServer

    def do_GET(self) -> None:  # noqa: N802 (the name http.server calls)
        url = urlsplit(self.path)
        state = self.server.state
        with state.lock:
            hits = state.hits[url.path]
            state.hits[url.path] += 1
        plan = plan_response(url.path, parse_qs(url.query), hits)
        status = plan.status
        if plan.slot:
            group, limit = plan.slot
            with state.lock:
                state.in_flight[group] += 1
                if state.in_flight[group] > limit:
                    status = 429
        try:
            time.sleep(plan.delay)
            self.send_response(status)
            self.send_header("Content-Type", "application/json" if plan.body.startswith(b"{") else "text/plain")
            self.send_header("Content-Length", str(len(plan.body)))
            self.end_headers()
            self.wfile.write(plan.body)
        except OSError:
            pass  # the client gave up, which some cases expect
        finally:
            if plan.slot:
                with state.lock:
                    state.in_flight[plan.slot[0]] -= 1

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        pass


class TestServer(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 128
    state: ServerState


@contextmanager
def serve() -> Iterator[str]:
    server = TestServer(("127.0.0.1", 0), Handler)
    server.state = ServerState()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()


def run_case(command: list[str], case: Case, server: str, env: dict[str, str] | None = None) -> RunResult:
    with tempfile.TemporaryDirectory(prefix="goeval-case-") as work:
        for name, content in case.files.items():
            Path(work, name).write_text(substitute(content, server), encoding="utf-8")
        args = [substitute(a, server) for a in case.args]
        try:
            proc = subprocess.run(
                [*command, *args], input=substitute(case.stdin, server).encode(),
                cwd=work, capture_output=True, env=env, timeout=case.timeLimit,
            )
        except (subprocess.TimeoutExpired, OSError):
            return RunResult(None, "")
        return RunResult(proc.returncode, proc.stdout.decode("utf-8", "replace"))


def go(module: Path, *args: str, timeout: float = BUILD_TIME_LIMIT) -> subprocess.CompletedProcess | None:
    try:
        return subprocess.run(["go", *args], cwd=module, capture_output=True, text=True, env=go_env(), timeout=timeout)
    except (subprocess.TimeoutExpired, OSError):
        return None


def build(module: Path, binary: Path) -> bool:
    if not (module / "go.mod").is_file():
        return False
    proc = go(module, "build", "-race", "-o", str(binary), ".")
    return proc is not None and proc.returncode == 0 and binary.is_file()


def lint(module: Path, config: Path) -> int | None:
    """Count the issues, or return None when golangci-lint gave no report."""
    proc = subprocess.run(
        ["golangci-lint", "run", "--config", str(config), "--output.json.path=stdout",
         "--show-stats=false", "--max-issues-per-linter=0", "--max-same-issues=0", "./..."],
        cwd=module, capture_output=True, text=True, env=go_env(), check=False,
    )
    issues = count_lint_issues(proc.stdout)
    if issues is None:
        print(f"golangci-lint gave no report in {module}: {proc.stderr.strip()}", file=sys.stderr)
    return issues


def fix_diff(module: Path) -> int:
    proc = go(module, "fix", "-diff", "./...")
    return count_diff_lines(proc.stdout) if proc is not None else 0


def grade_module(module: Path, cases: list[Case], binary: Path, server: str, config: Path) -> ModuleScore:
    if not build(module, binary):
        return ModuleScore(built=False, total=len(cases))
    passed = sum(case_passed(c, run_case([str(binary)], c, server), server) for c in cases)
    issues = lint(module, config)
    return ModuleScore(True, passed, len(cases), issues or 0, fix_diff(module), linted=issues is not None)


def grade(arm: Path, config: Path) -> tuple[dict, int]:
    """Return the scores and the number of problems printed on stderr."""
    problems = 0
    modules: dict[tuple[str, str], ModuleScore] = {}
    review: list[tuple[int, int, int]] = []
    with serve() as server, tempfile.TemporaryDirectory(prefix="goeval-bin-") as bins:
        for kind in ("write", "port"):
            for task in task_dirs(kind):
                cases = load_cases(task / "cases.json")
                score = grade_module(arm / kind / task.name, cases, Path(bins, f"{kind}-{task.name}"), server, config)
                modules[kind, task.name] = score
                problems += not score.linted
                print(f"{kind}/{task.name}: built={score.built} linted={score.linted if score.built else 'skipped'} "
                      f"cases={score.passed}/{score.total} lint={score.lint} fix={score.fix}")
    for task in task_dirs("review"):
        defects = load_defects(task / "key.json")
        path = arm / "review" / task.name / "findings.json"
        findings, problem = parse_findings(path.read_bytes()) if path.is_file() else ([], None)
        if problem:
            problems += 1
            print(f"{path}: {problem}, so it scores no findings", file=sys.stderr)
        found, false_positives = score_review(findings, defects)
        review.append((found, false_positives, len(defects)))
        print(f"review/{task.name}: found={found}/{len(defects)} falsePositives={false_positives}")
    return summarize(modules, review), problems


def missing_task_dirs(arm: Path) -> list[str]:
    """Name the folders that --prepare creates and that the arm lacks."""
    return [f"{kind}/{task.name}" for kind in KINDS for task in task_dirs(kind) if not (arm / kind / task.name).is_dir()]


def prepare(arm: Path) -> None:
    if arm.exists() and any(arm.iterdir()):
        sys.exit(f"{arm} is not empty")
    for kind in KINDS:
        for task in task_dirs(kind):
            target = arm / kind / task.name
            target.mkdir(parents=True)
            visible = {"port": task / "source", "review": task / "module"}.get(kind)
            if visible:
                shutil.copytree(visible, target, dirs_exist_ok=True)
    print(f"prepared {arm}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", type=Path, metavar="ARM", help="create the folders an agent writes into")
    mode.add_argument("--arm", type=Path, help="grade the work in this arm folder")
    parser.add_argument("--lint-config", type=Path, help="golangci-lint config, required with --arm")
    args = parser.parse_args()
    if args.prepare:
        prepare(args.prepare.resolve())
        return
    if not args.lint_config or not args.lint_config.is_file():
        parser.error("--arm needs --lint-config with a path to a golangci-lint config file")
    missing = [tool for tool in ("go", "golangci-lint") if shutil.which(tool) is None]
    if missing:
        sys.exit(f"missing tools: {', '.join(missing)}")
    arm = args.arm.resolve()
    if not arm.is_dir():
        sys.exit(f"{arm} is not a folder, so there is nothing to grade")
    absent = missing_task_dirs(arm)
    if absent:
        sys.exit(f"{arm} lacks the task folders {', '.join(absent)}, so it is not a prepared arm")
    scores, problems = grade(arm, args.lint_config.resolve())
    print(json.dumps({key: scores[key] for key in SCORE_KEYS}))
    if problems:
        sys.exit(f"{problems} grading problems, listed above, make these scores incomplete")


if __name__ == "__main__":
    main()
