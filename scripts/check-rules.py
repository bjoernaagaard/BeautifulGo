#!/usr/bin/env python3
"""Check the rule table against the skills and against the tools it names.

Usage: check-rules.py [table.md]   (default skills/go-best-practices/references/rules.md)
"""
import re
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
skills = root / "skills"
config = skills / "go-review/assets/golangci.yml"
CHECK_FORMS = re.compile(r"(lint|vet|fix):([A-Za-z0-9_]+)|compiler|reader")


def table_rows(text):
    """Yield (id, check cell) for each data row of the Markdown table."""
    for line in text.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if line.startswith("|") and len(cells) == 4 and cells[0] not in ("id",) and not set(cells[0]) <= {"-"}:
            yield cells[0], cells[2]


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
            elif match[1] and match[2] not in known[match[1]]:
                errors.append(f"{rule_id}: {match[1]}:{match[2]} is not reported by the tool")
    errors += [f"{name}: `{ref}` has no row in the rule table" for name, ref in referenced if ref not in seen]
    return errors


def run(*command):
    return subprocess.run(command, capture_output=True, text=True, check=True).stdout


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
    rows = list(table_rows(table.read_text()))
    errors = rule_errors(rows, sections, known, referenced)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"{len(rows)} rules match the skills and the tools")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
