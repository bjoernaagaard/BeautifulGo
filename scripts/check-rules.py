#!/usr/bin/env python3
"""Check the rule table's shape, its ids, and that its claimed tools fire on scripts/lint-fixture.

Usage: check-rules.py [table.md]   (default skills/go-best-practices/references/rules.md)

The table starts with the exact header line `| id | rule | check | source |` and the
separator line `|---|---|---|---|`. Every other table row needs an id, a rule, a check and
a source. The source starts with guide letters from E W G U L R, or with ours, and may add
an explanation in parentheses. The ids must equal scripts/rule-ids.txt, so adding,
removing or renaming a rule takes an edit there too. Each lint:, vet: and fix: name must
exist in the tool and, except for formatters checked by `golangci-lint fmt`, actually
produce a diagnostic on scripts/lint-fixture.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
skills = root / "skills"
config = skills / "go-review/assets/golangci.yml"
fixture = root / "scripts/lint-fixture"
inventory = root / "scripts/rule-ids.txt"
CHECK_FORMS = re.compile(r"(lint|vet|fix):([A-Za-z0-9_]+)|compiler|reader")
HEADER = "| id | rule | check | source |"
SEPARATOR = "|---|---|---|---|"
RULE_ID = re.compile(r"\d+\.[a-z][a-z0-9-]*")
# The guide letters, or ours, optionally followed by an explanation in parentheses.
SOURCE = re.compile(r"(?:ours|[EWGULR](?: [EWGULR])*)(?: \(.+\))?")


def table_rows(text):
    """Return (rows, errors). A row is (id, check cell); every table line must be well formed."""
    lines = [(number, line) for number, line in enumerate(text.splitlines(), 1) if line.startswith("|")]
    if [line.rstrip() for _, line in lines[:2]] != [HEADER, SEPARATOR]:
        return [], [f"the table must start with the lines {HEADER} and {SEPARATOR}"]
    rows, errors = [], []
    for number, line in lines[2:]:
        cells = [cell.strip() for cell in line.rstrip().removesuffix("|")[1:].split("|")]
        if len(cells) != 4 or not all(cells):
            errors.append(f"line {number}: a row needs a non-empty id, rule, check and source")
        elif not RULE_ID.fullmatch(cells[0]):
            errors.append(f"line {number}: malformed id {cells[0]}")
        elif not SOURCE.fullmatch(cells[3]):
            errors.append(f"line {number}: source {cells[3]!r} is not guide letters or ours")
        else:
            rows.append((cells[0], cells[2]))
    return rows, errors


def inventory_errors(rows, expected):
    ids = {rule_id for rule_id, _ in rows}
    errors = [f"{rule_id}: listed in scripts/rule-ids.txt but has no row" for rule_id in sorted(expected - ids)]
    errors += [f"{rule_id}: has a row but is not listed in scripts/rule-ids.txt" for rule_id in sorted(ids - expected)]
    return errors


def block_names(output, header, split):
    """Names listed under `header`, up to the blank line that ends the list."""
    block = []
    lines = iter(output.splitlines())
    for line in lines:
        if line.strip() == header:
            for entry in lines:
                if not entry.strip():
                    if block:
                        break
                    continue
                block.append(split(entry))
            break
    return set(block)


def rule_errors(rows, sections, known, referenced):
    """known maps 'lint', 'vet' and 'fix' to the set of valid names."""
    errors, seen = [], set()
    claimed = {"lint": set(), "vet": set(), "fix": set()}
    for rule_id, check in rows:
        if rule_id in seen:
            errors.append(f"{rule_id}: duplicate id")
        seen.add(rule_id)
        number = rule_id.split(".", 1)[0]
        if number not in sections:
            errors.append(f"{rule_id}: section {number} is not a SKILL.md section")
        for token in check.split():
            match = CHECK_FORMS.fullmatch(token)
            if not match:
                errors.append(f"{rule_id}: unknown check {token}")
            elif match[1]:
                if match[2] not in known[match[1]]:
                    errors.append(f"{rule_id}: {match[1]}:{match[2]} is not a linter or analyzer the tool has")
                else:
                    claimed[match[1]].add(match[2])
    errors += [f"{name}: `{ref}` has no row in the rule table" for name, ref in referenced if ref not in seen]
    return errors, claimed


def run(*command, cwd=None):
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=True).stdout


def fired_linters():
    proc = subprocess.run(
        ["golangci-lint", "run", "--config", str(config), "--output.json.path=stdout",
         "--show-stats=false", "--uniq-by-line=false", "--max-issues-per-linter=0",
         "--max-same-issues=0", "./..."],
        cwd=fixture, capture_output=True, text=True, check=False,
    )
    if proc.returncode > 1:
        raise RuntimeError(f"golangci-lint failed on {fixture}: {proc.stderr.strip()}")
    data = json.loads(proc.stdout)
    return {issue["FromLinter"] for issue in (data.get("Issues") or [])}


def fired_vet_analyzers():
    proc = subprocess.run(
        ["go", "vet", "-json", "./..."],
        cwd=fixture, capture_output=True, text=True, check=False,
    )
    fired = set()
    dec = json.JSONDecoder()
    text = proc.stdout + "\n" + proc.stderr
    pos = 0
    while pos < len(text):
        idx = text.find("{", pos)
        if idx == -1:
            break
        try:
            obj, end = dec.raw_decode(text, idx)
            pos = end
        except ValueError:
            pos = idx + 1
            continue
        if isinstance(obj, dict):
            for analyzers in obj.values():
                if isinstance(analyzers, dict):
                    for name, diags in analyzers.items():
                        if diags:
                            fired.add(name)
    return fired


def fired_fix_analyzers(names):
    fired = set()
    for name in sorted(names):
        proc = subprocess.run(
            ["go", "fix", f"-{name}", "-diff", "./..."],
            cwd=fixture, capture_output=True, text=True, check=False,
        )
        if proc.stdout.strip() or f"fix: {name}:" in proc.stderr:
            fired.add(name)
    return fired


def fixture_errors(claimed, formatters):
    errors = []
    lint_fired = fired_linters()
    for name in sorted(claimed["lint"] - formatters - lint_fired):
        errors.append(f"lint:{name} is cited in rules.md but did not fire on scripts/lint-fixture")
    vet_fired = fired_vet_analyzers()
    for name in sorted(claimed["vet"] - vet_fired):
        errors.append(f"vet:{name} is cited in rules.md but did not fire on scripts/lint-fixture")
    fix_fired = fired_fix_analyzers(claimed["fix"])
    for name in sorted(claimed["fix"] - fix_fired):
        errors.append(f"fix:{name} is cited in rules.md but did not fire on scripts/lint-fixture")
    return errors


def main(argv):
    table = Path(argv[0]) if argv else skills / "go-best-practices/references/rules.md"
    skill = (skills / "go-best-practices/SKILL.md").read_text()
    sections = set(re.findall(r"(?m)^## (\d+)\.", skill))
    by_colon = lambda entry: entry.split(":")[0].strip()
    by_space = lambda entry: entry.split()[0]
    linters = block_names(run("golangci-lint", "linters", "--config", str(config)),
                          "Enabled by your configuration linters:", by_colon)
    formatters = block_names(run("golangci-lint", "formatters", "--config", str(config)),
                             "Enabled by your configuration formatters:", by_colon)
    known = {
        "lint": linters | formatters,
        "vet": block_names(run("go", "tool", "vet", "help"), "Registered analyzers:", by_space),
        "fix": block_names(run("go", "tool", "fix", "help"), "Registered analyzers:", by_space),
    }
    referenced = []
    for name in ("go-review", "go-port"):
        text = (skills / name / "SKILL.md").read_text()
        referenced += [(name, ref) for ref in re.findall(r"`(\d+\.[a-z][a-z0-9-]*)`", text)]
    rows, errors = table_rows(table.read_text())
    expected = set(inventory.read_text().split())
    claimed = {"lint": set(), "vet": set(), "fix": set()}
    if rows or not errors:  # skip the id checks when the table itself is malformed
        r_errors, claimed = rule_errors(rows, sections, known, referenced)
        errors += inventory_errors(rows, expected) + r_errors
        if not errors:
            errors += fixture_errors(claimed, formatters)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"{len(rows)} rules match scripts/rule-ids.txt; "
          f"{len(claimed['lint'] - formatters)} linters, {len(claimed['vet'])} vet analyzers, and "
          f"{len(claimed['fix'])} fix analyzers verified against scripts/lint-fixture.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
