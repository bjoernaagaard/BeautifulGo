#!/usr/bin/env python3
"""Check that every version in the repository agrees with versions.toml.

Without arguments it needs no network. With --upstream it also asks go.dev and GitHub
what has moved since the record was written, prints one line per moved item, and exits 1.
"""
import json
import re
import subprocess
import sys
import tomllib
import urllib.request
from pathlib import Path

root = Path(__file__).resolve().parents[1]

# (file, regular expression with one group, record value the group must equal)
PINS = [
    ("README.md", r"Go (\d+\.\d+) code", "go_minor"),
    ("README.md", r"\| Go (\d+\.\d+) \|", "go_minor"),
    ("README.md", r"golangci-lint (\d+\.\d+) or later \|", "lint_minor"),
    ("README.md", r"need Go (\d+\.\d+)", "go_minor"),
    ("skills/go-best-practices/SKILL.md", r"golangci-lint\]\([^)]*\) (\d+\.\d+) or later", "lint_minor"),
    (".github/workflows/check.yml", r'go-version: "(\d+\.\d+)"', "go_minor"),
    (".github/workflows/check.yml", r"version: v(\d+\.\d+\.\d+)", "lint"),
    ("scripts/check-examples.py", r"go (\d+\.\d+)\\n", "go_minor"),
    ("scripts/lint-fixture/go.mod", r"(?m)^go (\d+\.\d+)$", "go_minor"),
]
GO_PATCH = re.compile(r"\b1\.\d+\.\d+\b")
LINT_VERSION = re.compile(r"golangci.*\bv?2\.\d+\.\d+\b|\bv2\.\d+\.\d+\b")
SCANNED = ("README.md", "skills", "scripts", ".github")
SUFFIXES = {".md", ".yml", ".py", ".sh"}
NOT_DIGESTS = {"rules.md"}  # an index of the rules, not a digest of an upstream file


def derived(record):
    go = record["go"]["release"]
    lint = record["golangci-lint"]["release"]
    return {
        "go_minor": go.rsplit(".", 1)[0],
        "lint": lint,
        "lint_minor": lint.rsplit(".", 1)[0],
    }


def references(source):
    ref = source["reference"]
    return [ref] if isinstance(ref, str) else list(ref)


def check_pin(name, text, pattern, expected):
    """Return (errors, line numbers of the match)."""
    matches = list(re.finditer(pattern, text))
    if len(matches) != 1:
        return [f"{name}: pattern {pattern!r} matches {len(matches)} times, not once"], []
    match = matches[0]
    line = text.count("\n", 0, match.start()) + 1
    if match.group(1) != expected:
        return [f"{name}:{line}: found {match.group(1)}, versions.toml says {expected}"], [line]
    return [], [line]


def stray_versions(name, text, pinned_lines):
    errors = []
    for number, line in enumerate(text.splitlines(), 1):
        if number in pinned_lines:
            continue
        if GO_PATCH.search(line) or LINT_VERSION.search(line):
            errors.append(f"{name}:{number}: version outside versions.toml and the pins: {line.strip()}")
    return errors


def reference_errors(record, existing):
    """`existing` is the set of references/*.md paths on disk."""
    named = set()
    for source in record["source"]:
        named.update(references(source))
    errors = [f"{path}: no [[source]] row in versions.toml" for path in sorted(existing - named)]
    errors += [f"versions.toml: reference {ref} does not exist" for ref in sorted(named - existing)]
    return errors


def moved_items(record, go_latest, go_candidates, lint_latest, upstream_commits):
    """upstream_commits maps (repo, path) to (sha, date). Returns one line per moved item."""
    lines = []
    release = record["go"]["release"]
    if go_latest != release:
        lines.append(f"go: record {release}, upstream {go_latest}")
    lines += [f"go: release candidate {rc} is out" for rc in go_candidates]
    lint = record["golangci-lint"]["release"]
    if lint_latest.removeprefix("v") != lint:
        lines.append(f"golangci-lint: record v{lint}, upstream {lint_latest}")
    for source in record["source"]:
        sha, date = upstream_commits[(source["repo"], source["path"])]
        if sha != source["commit"]:
            lines.append(
                f"{source['repo']} {source['path']}: record {source['commit'][:7]} ({source['date'][:10]}), "
                f"upstream {sha[:7]} ({date[:10]}), digest {', '.join(references(source))}"
            )
    return lines


def newer_candidates(versions, go_minor):
    """The newest rc or beta of each minor above the recorded one."""
    recorded = tuple(int(n) for n in go_minor.split("."))
    best = {}
    for version in versions:
        match = re.fullmatch(r"go(1)\.(\d+)(?:rc|beta)(\d+)", version)
        if match and (1, int(match[2])) > recorded:
            key = (1, int(match[2]))
            best[key] = max(best.get(key, (0, "")), (int(match[3]), version))
    return [best[key][1] for key in sorted(best)]


def fetch_go_versions(url):
    """Version names in the order go.dev lists them, newest first."""
    with urllib.request.urlopen(url, timeout=30) as response:
        return [str(item["version"]) for item in json.load(response)]


def gh_commit(repo, path):
    out = subprocess.run(
        ["gh", "api", f"repos/{repo}/commits?path={path}&per_page=1", "--jq",
         ".[0] | [.sha, .commit.committer.date] | @tsv"],
        capture_output=True, text=True, check=True).stdout
    sha, date = out.split()
    return sha, date


def check_offline(record):
    values = derived(record)
    errors, pinned = [], {}
    for name, pattern, key in PINS:
        text = (root / name).read_text()
        found, lines = check_pin(name, text, pattern, values[key])
        errors += found
        pinned.setdefault(name, set()).update(lines)
    for scanned in SCANNED:
        base = root / scanned
        files = [base] if base.is_file() else [p for p in base.rglob("*") if p.is_file()]
        for path in sorted(files):
            if path.suffix in SUFFIXES or path.name == "go.mod":
                name = str(path.relative_to(root))
                errors += stray_versions(name, path.read_text(), pinned.get(name, set()))
    existing = set()
    for path in root.glob("skills/*/references/*.md"):
        if path.name not in NOT_DIGESTS:
            existing.add(str(path.relative_to(root)))
    return errors + reference_errors(record, existing)


def check_upstream(record):
    go_latest = fetch_go_versions("https://go.dev/dl/?mode=json")[0].removeprefix("go")
    everything = fetch_go_versions("https://go.dev/dl/?mode=json&include=all")
    candidates = newer_candidates(everything, derived(record)["go_minor"])
    lint_latest = subprocess.run(
        ["gh", "api", "repos/golangci/golangci-lint/releases/latest", "--jq", ".tag_name"],
        capture_output=True, text=True, check=True).stdout.strip()
    commits = {(s["repo"], s["path"]): gh_commit(s["repo"], s["path"]) for s in record["source"]}
    return moved_items(record, go_latest, candidates, lint_latest, commits)


def main(argv):
    record = tomllib.loads((root / "versions.toml").read_text())
    problems = check_upstream(record) if "--upstream" in argv else check_offline(record)
    if problems:
        print("\n".join(problems), file=sys.stderr if "--upstream" not in argv else sys.stdout)
        return 1
    print("upstream matches versions.toml" if "--upstream" in argv else "all versions agree with versions.toml")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
