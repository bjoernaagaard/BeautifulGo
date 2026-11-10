#!/bin/sh
# Verifies skills/go-review/assets/golangci.yml and checks that every linter it enables
# reports a violation in scripts/lint-fixture.
set -eu

root=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
config=$root/skills/go-review/assets/golangci.yml
fixture=$root/scripts/lint-fixture

golangci-lint config verify --config "$config"

status=0
output=$(cd "$fixture" && golangci-lint run --config "$config" \
	--uniq-by-line=false --max-issues-per-linter 0 --max-same-issues 0 ./...) || status=$?
if [ "$status" -gt 1 ]; then
	printf '%s\n' "$output" >&2
	echo "golangci-lint failed with exit code $status" >&2
	exit 1
fi

enabled=$(golangci-lint linters --config "$config" |
	sed -n '/^Enabled by your configuration linters:/,/^$/p' | sed '1d;/^$/d' | cut -d: -f1)
missing=""
for linter in $enabled; do
	printf '%s\n' "$output" | grep -q "^\* $linter:" || missing="$missing $linter"
done

if [ -n "$missing" ]; then
	printf '%s\n' "$output" >&2
	echo "linters with no finding:$missing" >&2
	exit 1
fi
echo "all $(printf '%s\n' "$enabled" | wc -l | tr -d ' ') enabled linters report a fixture violation"
