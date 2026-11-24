---
name: go-review
description: >-
  Review existing Go code for correctness, API design, errors, concurrency, security, and
  maintainability, and write a prioritized report where every finding cites the rule it
  breaks and shows the fix. Use for a review, audit, critique, grade, or check of a .go
  file, package, module, diff, or pull request, or when the user asks what is wrong with
  their Go or how to make it more idiomatic, even if they don't say "review".
---

# Go review

Review Go code against the rules in the `go-best-practices` skill and report what to
change. The output is a review, not a rewrite. Change code only when the user asks.

## 1. Set the scope

- **What to read.** Review exactly what the user named: a file, a package, a module, or a
  diff. For a diff, read each changed function in full and anything the change can break,
  such as callers of a changed signature.
- **Library or application.** A module that other modules import, or a package outside
  `internal/` and `cmd/` with exported API, is a library and is held to the API rules
  strictly. An application gets the simplicity rules instead: concrete types, no
  speculative interfaces, configuration from `main`.
- **Go version.** Read the `go` line in `go.mod`. Don't recommend a feature the module
  can't use; when an upgrade would remove a whole class of findings, say so once under
  Consider.
- State all three assumptions in the report's opening paragraph.

## 2. Run the tools first

From the module root, run the commands in section 1 of `go-best-practices`, and fold the
results into the report. When the module has no golangci-lint config, pass `--config` with
this skill's `assets/golangci.yml`.

Don't paste raw tool output. Group repeated warnings into one finding and skip findings
that don't matter for this code. If a tool can't run (no network, no config, a build
error), say which and why, and review by reading.

## 3. What to look for, in priority order

The first group is where real bugs live.

**Correctness**

- Reachable panics: an unchecked type assertion `v.(T)`, a write to a nil map, an index
  or slice without a length check, a nil pointer from a function that returns `nil, nil`.
- A data race: shared state written without a lock, a loop that appends to a slice from
  several goroutines, a map read and written concurrently.
- Goroutine leaks: no owner, no stop signal, or no wait; a send on a channel nobody reads
  after the caller returned; a missing `wg.Wait` or `g.Wait`.
- Context misuse: a derived context whose `cancel` is never called, `context.Background()`
  inside a request path, a context stored in a struct, a blocking call that ignores
  `ctx.Done()`, a canceled call recorded as an outcome, or a per-request timeout on an
  operation that retries or falls back.
- Resource leaks: a file, response body, or `sql.Rows` that isn't closed, or is closed
  only on the happy path; `defer` inside a loop over many items; a `time.Ticker` that a
  long-lived goroutine still holds after its work is done.
- Values that must agree, such as a total and its parts, read under separate lock
  acquisitions.
- Copied locks and atomics (a value receiver on a type with a `sync.Mutex`), and a typed
  nil pointer returned as `error`.
- Unbounded input: `io.ReadAll` on a request body without `http.MaxBytesReader`, file
  paths from users opened without `os.Root`, `math/rand` used for a token.

**Everything else**

Check each rule in `go-best-practices` whose `check` column in
`go-best-practices/references/rules.md` says `reader`; the tools in section 2 report the
rest. Hold a library to the API rules strictly. Report the rewrites `go fix -diff ./...`
proposes as one Consider finding, and flag what no tool rewrites:
`for i := 0; i < b.N; i++`, `t.Cleanup(cancel)` in tests, `time.Sleep` in tests, and a
`tools.go` file.

The `go-best-practices` skill and its `references/` folder hold the full rules and their
reasoning. Read the relevant reference when a finding needs a rule you're unsure of.

## 4. Write the report

Use the structure in `assets/review-template.md`.

- **Must fix:** a bug, a race, a leak, a reachable panic, a swallowed error, a security
  hole, or an API mistake that becomes a breaking change once published.
- **Should fix:** code that works but has a real cost, such as errors callers can't
  inspect, code that is hard to test, or a confusing API.
- **Consider:** naming, modernization, and local polish.

Rules for each finding:

- Cite the line a tool reports. For a reader finding, cite the line of the faulty
  expression, such as the type assertion or the call whose result leaks, not the line that
  registers, wraps or returns it; use `whole file` only when no line fits.
- Cite the rule by its id in `rules.md`, such as `6.error-is`, and the linter or analyzer
  when a tool reported it.
- Show the fix as Go code, limited to the lines that change.
- Group repeats into one finding that lists every location.
- Respect intent. A deliberate, documented choice that is not a bug goes under Consider
  with the trade-off, never under Must fix.
- Keep it proportionate. Five to ten findings is enough for a short file. Don't hide a
  real bug among style notes.
- The "What is already good" section is required, with two to four specific points.

## 5. Offer the lint configuration

If the module has no `.golangci.yml`, end the report by suggesting the bundled
`assets/golangci.yml`, and name two or three findings from the review that it would have
caught, with the linter that catches each.
