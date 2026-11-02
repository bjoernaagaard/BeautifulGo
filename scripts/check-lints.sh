#!/bin/sh
set -eu

root=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
config=$root/lints/golangci.yml
check=$root/lints/check

golangci-lint config verify --config "$config" >/dev/null
output=$(cd "$check" && golangci-lint run --config "$config" ./... || true)

printf '%s\n' "$output" | grep -q 'errcheck'
printf '%s\n' "$output" | grep -q 'ignored'
printf '%s\n' "$output" | grep -q 'error-strings'
echo "lint fixture reports the expected findings"
