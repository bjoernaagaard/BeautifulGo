#!/bin/sh
# Verifies lints/golangci.yml and checks that each linter reports its violation in lints/check.
set -eu

root=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
config=$root/lints/golangci.yml

golangci-lint config verify --config "$config"
output=$(cd "$root/lints/check" && golangci-lint run --config "$config" \
	--uniq-by-line=false --max-issues-per-linter 0 --max-same-issues 0 ./... || true)

missing=""
for linter in bodyclose containedctx errcheck errorlint forcetypeassert modernize noctx nolintlint revive; do
	printf '%s\n' "$output" | grep -q "^\* $linter:" || missing="$missing $linter"
done

if [ -n "$missing" ]; then
	printf '%s\n' "$output" >&2
	echo "linters with no finding:$missing" >&2
	exit 1
fi
echo "lint fixture reports the expected findings"
