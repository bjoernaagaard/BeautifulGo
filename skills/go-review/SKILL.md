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

From the module root, run what is available and fold the results into the report:

```bash
gofmt -l .
go vet ./...
go fix -diff ./...          # modernizations allowed by the go line
golangci-lint run           # the repo's config, else --config <this skill>/assets/golangci.yml
go test -race ./...
govulncheck ./...           # reachable known vulnerabilities in dependencies
```

Don't paste raw tool output. Group repeated warnings into one finding and skip findings
that don't matter for this code. If a tool can't run (no network, no config, a build
error), say which and why, and review by reading.

## 3. What to look for, in priority order

The first two groups are where real bugs live.

**Correctness**

- Reachable panics: an unchecked type assertion `v.(T)`, a write to a nil map, an index
  or slice without a length check, a nil pointer from a function that returns `nil, nil`.
- A data race: shared state written without a lock, a loop that appends to a slice from
  several goroutines, a map read and written concurrently.
- Goroutine leaks: no owner, no stop signal, or no wait; a send on a channel nobody reads
  after the caller returned; a missing `wg.Wait` or `g.Wait`.
- Context misuse: a derived context whose `cancel` is never called, `context.Background()`
  inside a request path, a context stored in a struct, or a blocking call that ignores
  `ctx.Done()`.
- Resource leaks: a file, response body, or `sql.Rows` that isn't closed, or is closed
  only on the happy path; `defer` inside a loop over many items; a ticker that keeps
  firing after its work is done because nobody calls `Stop`.
- Copied locks and atomics (a value receiver on a type with a `sync.Mutex`), and a typed
  nil pointer returned as `error`.
- Unbounded input: `io.ReadAll` on a request body without `http.MaxBytesReader`, file
  paths from users opened without `os.Root`, `math/rand` used for a token.

**Errors**

- An ignored actionable error, including the error from `Close` on a written file.
- An error both logged and returned, or returned without the context a caller needs
  (path, ID, operation).
- `%v` where callers need to match the cause, or `%w` that leaks an internal dependency
  into the API.
- `err.Error()` compared as text, `==` on an error that may be wrapped, or `errors.As`
  with a target variable where `errors.AsType` reads better.
- `panic` for caller input, `log.Fatal` or `os.Exit` outside `main`.

**API and design** (strict for libraries)

- An exported function that returns a concrete error type, or an interface where a
  concrete type would do.
- An interface declared beside its only implementation, a pointer to an interface, or an
  interface with many methods and one caller.
- A Boolean parameter, a `Get` prefix, a stuttering name (`user.UserID`), a `util`
  package, mixed pointer and value receivers, or an exported embedded `sync.Mutex`.
- Bare integers for durations or IDs, or a returned slice or map that aliases internal
  state.
- A third-party type leaking through the exported API when a standard type would do.

**Modern Go** (only what the `go` line allows)

- Code that `go fix` would rewrite: `interface{}`, three-clause loops over an integer,
  `x := x` loop copies, `sort.Slice` on basic types, `wg.Add(1)` with `go` and
  `defer wg.Done()`, hand-written `min`/`max`, pointer helpers instead of `new(expr)`,
  `context.WithCancel` in tests instead of `t.Context()`.
- `for i := 0; i < b.N; i++` instead of `for b.Loop()`, `time.Sleep` in tests instead of
  `testing/synctest`, a `tools.go` file instead of `tool` lines in `go.mod`, and
  `golang.org/x/exp` packages that the standard library now provides.

**Tests and documentation**

- Behavior without a test, tests coupled to unexported details, or assertions on error
  text.
- Concurrent code without a `-race` run, or time-dependent tests that can flake.
- Exported names without a doc comment, or a comment that only restates the name.
- Output whose order depends on map iteration.

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

- Cite a location as `file:line`, or `whole file` when there is no single line.
- Cite the rule and its source so a reader can look it up: a `go-best-practices`
  section, a Code Review Comments heading, a Google or Uber style guide section, a
  `go vet` analyzer, or a linter name such as `errorlint` or `bodyclose`.
- Show the fix as Go code, limited to the lines that change.
- Group repeats into one finding that lists every location.
- Respect intent. A deliberate, documented choice goes under Consider with the trade-off,
  never under Must fix.
- Keep it proportionate. Five to ten findings is enough for a short file. Don't hide a
  real bug among style notes.
- The "What is already good" section is required, with two to four specific points.

## 5. Offer the lint configuration

If the module has no `.golangci.yml`, end the report by suggesting the bundled
`assets/golangci.yml`, and name two or three findings from the review that it would have
caught, with the linter that catches each.
