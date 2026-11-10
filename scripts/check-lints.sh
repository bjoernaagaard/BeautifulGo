#!/bin/sh
# Verifies skills/go-review/assets/golangci.yml and checks that each linter reports its violation in lints/check.
set -eu

root=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
config=$root/skills/go-review/assets/golangci.yml

golangci-lint config verify --config "$config"
status=0
output=$(cd "$root/lints/check" && golangci-lint run --config "$config" \
	--uniq-by-line=false --max-issues-per-linter 0 --max-same-issues 0 ./...) || status=$?
if [ "$status" -gt 1 ]; then
	printf '%s\n' "$output" >&2
	echo "golangci-lint failed with exit code $status" >&2
	exit 1
fi

missing=""
for linter in bodyclose containedctx errcheck errorlint forcetypeassert gosec modernize noctx nolintlint revive staticcheck unused; do
	printf '%s\n' "$output" | grep -q "^\* $linter:" || missing="$missing $linter"
done

if [ -n "$missing" ]; then
	printf '%s\n' "$output" >&2
	echo "linters with no finding:$missing" >&2
	exit 1
fi
echo "lint fixture reports the expected findings"
