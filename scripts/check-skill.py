#!/usr/bin/env python3
import re
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
errors = []
skills = sorted((root / "skills").glob("*/SKILL.md"))
if [p.parent.name for p in skills] != ["go-best-practices", "go-port", "go-review"]:
    errors.append("expected go-best-practices, go-port, and go-review")

for skill in skills:
    text = skill.read_text()
    match = re.match(r"\A---\n(.*?)\n---\n(.*)\Z", text, re.S)
    if not match:
        errors.append(f"{skill}: missing frontmatter")
        continue
    front, body = match.groups()
    name = re.search(r"(?m)^name: ([a-z0-9-]+)\s*$", front)
    description = re.search(r"(?m)^description:\s*(.*)$", front)
    if not name or name.group(1) != skill.parent.name:
        errors.append(f"{skill}: name does not match directory")
    if not description or not description.group(1).strip():
        errors.append(f"{skill}: missing description")
    if body.count("\n") > 500:
        errors.append(f"{skill}: body exceeds 500 lines")
    for path in re.findall(r"`((?:references|assets)/[^`\s]+)`", body):
        if not (skill.parent / path).exists():
            errors.append(f"{skill}: missing file {path}")
    prose = re.sub(r"^```.*?^```|`[^`\n]*`", "", body, flags=re.S | re.M)
    for link in re.findall(r"\[[^\]]+\]\(([^)]+)\)", prose):
        if "://" not in link and not (skill.parent / link).exists():
            errors.append(f"{skill}: broken link {link}")

if errors:
    print("\n".join(errors), file=sys.stderr)
    sys.exit(1)
print(f"checked {len(skills)} skills")
