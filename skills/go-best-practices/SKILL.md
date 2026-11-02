---
name: go-best-practices
description: >-
  Write idiomatic, robust, maintainable Go. Use whenever you write, review, refactor,
  debug, or explain Go code: packages, functions, types, interfaces, errors, goroutines,
  channels, context, generics, iterators, go.mod, or tests. Trigger on Go, golang, .go
  files, gofmt, go vet, go fix, golangci-lint, context, goroutines, or channels, even
  without the words "best practices".
---

# Go best practices

Distilled from Effective Go, the Go Code Review Comments wiki, the Google Go Style Guide,
the Uber Go Style Guide, and the Go release notes through Go 1.27. Each has a digest in
`references/`. Where they disagree, this file chooses and says why.

## 1. Mindset

- **Write Go-shaped code.** Return errors as values, model absence with the zero value or
  a comma-ok result, compose with embedding and small interfaces, and keep control flow
  visible. Class hierarchies, `Manager` and `Factory` types, getters on every field, and
  exceptions emulated with `panic` are smells.
- **Clarity first, then simplicity, then concision.** Code is read far more than it is
  written. A reader should see what a line does without opening three other files.
- **Application code is not library code.** A library (a module other modules import)
  follows the API rules below strictly. An application stays direct: concrete types,
  explicit parameters, no interface with one implementation, and no dependency-injection
  framework.
- **Let the tools do the work.** `gofmt` owns layout, `go vet` and `golangci-lint` own
  mechanical checks, `go fix` owns modernization, and the race detector owns data races.
  Spend review attention on design.

## 2. Before you hand back code

From the module root, run:

```bash
go fix -diff ./...      # modern idioms for the go version in go.mod
gofmt -l .              # must print nothing
go vet ./...
golangci-lint run       # with lints/golangci.yml from this project, or the repo's own
go test -race ./...
govulncheck ./...       # when dependencies or security-relevant code changed
```

- Fix a finding rather than silencing it. When a lint is wrong for one line, suppress
  that linter only and say why: `//nolint:gosec // G404: jitter, not a secret`.
  `nolintlint` rejects a bare `//nolint`.
- Run `go fix ./...` before a review rather than hand-editing loops into `range` and
  `slices` calls. It only applies changes the `go` line in `go.mod` allows.
- Use `-race` whenever the change touches goroutines, channels, or shared state. A race
  report is a bug, never noise.

## 3. Versions and modules

Read the `go` line in `go.mod` before using a feature from the table. In a new module,
declare the current release (`go 1.27`). In a library, declare the oldest release you test
against, because the `go` line is a minimum for every importer.

| Since | Use | Instead of |
|---|---|---|
| 1.21 | `min`, `max`, `clear`; `slices`, `maps`, `cmp`; `log/slog`; `context.AfterFunc`, `WithoutCancel` | hand loops, `sort.Slice`, `log.Printf` |
| 1.22 | a fresh loop variable per iteration; `for i := range n`; `http.ServeMux` patterns `"GET /items/{id}"` | `x := x` copies, third-party routers for simple routing |
| 1.23 | iterators: `iter.Seq`, `slices.Collect`, `maps.Keys`, `slices.Sorted` | building a slice only to range over it |
| 1.24 | generic type aliases; `t.Context()`, `b.Loop()`, `t.Chdir`; `os.Root`; `omitzero`; `tool` lines in `go.mod`; `strings.SplitSeq`; `runtime.AddCleanup`; `crypto/rand.Text` | `context.WithCancel` in tests, `for i := 0; i < b.N; i++`, `tools.go`, `SetFinalizer` |
| 1.25 | `sync.WaitGroup.Go`; `testing/synctest`; `http.CrossOriginProtection`; container-aware `GOMAXPROCS` | `wg.Add(1)` plus `defer wg.Done()`, sleeping in tests, hand-rolled CSRF checks |
| 1.26 | `new(expr)`; `errors.AsType[T]`; the modernizers in `go fix` | `ptr(v)` helpers, `var target *T; errors.As(err, &target)` |
| 1.27 | generic methods; `encoding/json/v2`; the `uuid` package; the `goroutineleak` profile | free functions that exist only to add a type parameter, third-party UUID modules |

- Pin developer tools with `go get -tool golang.org/x/vuln/cmd/govulncheck` and run them with
  `go tool govulncheck`. Don't add a `tools.go` file with blank imports.
- Commit `go.sum`. Run `go mod tidy` after any import change. Add a `toolchain` line only
  when the build needs a newer toolchain than the `go` line.
- Every dependency costs build time, review time, and supply-chain exposure. Check the
  standard library first, and don't add a framework, ORM, assertion library, or
  dependency-injection container unless the module already uses one.
- Avoid `golang.org/x/exp` when the standard library now has the same function
  (`slices`, `maps`, `constraints` became `cmp.Ordered`). The `exptostd` linter finds them.

## 4. Names and declarations

| Item | Form | Example |
|---|---|---|
| Exported / unexported | `MixedCaps` / `mixedCaps` | `ParseConfig`, `parseLine` |
| Initialisms | one case throughout | `userID`, `HTTPClient`, `ServeHTTP` |
| Packages | short, lowercase, one word, no underscores | `bytes`, `httptest` |
| Receivers | one or two letters, the same on every method | `func (c *Client)` |
| Interfaces with one method | the method name plus `er` | `Reader`, `Notifier` |
| Sentinel errors / error types | `Err` prefix / `Error` suffix | `ErrNotFound`, `PathError` |

- Package names supply context, so don't repeat them: `http.Client`, not
  `http.HTTPClient`; `user.Load`, not `user.LoadUser`. Avoid `util`, `common`, `helpers`,
  `models`, and `misc`. Name a package after what it provides.
- No `Get` prefix on getters: `Owner()` and `SetOwner()`. Use `Fetch` or `Load` when the
  call does real work, such as I/O.
- Short names for small scopes (`i`, `r`, `buf`), longer names as the distance between
  declaration and use grows. Never `this` or `self`.
- Use `var x T` for the zero value and `x := value` for anything else. Keep variables in
  the narrowest scope, including `if err := f(); err != nil`.
- Name fields in composite literals, except in a small local test table.
- Don't shadow predeclared identifiers (`len`, `new`, `error`, `min`, `max`, `clear`) or
  package names (`url := url.Parse(...)` breaks the next call).
- Use `any`, not `interface{}`.
- A function that formats like `fmt.Printf` ends in `f`, so `go vet` checks its verbs.
- Order a file as: the main type, its constructor, exported methods, unexported methods,
  then helpers. Group related `const` and `var` declarations.
- An enum is a named type with `iota` constants. Start at `iota + 1` when the zero value
  must mean "unset", and give it a `String` method (or run `stringer`).

## 5. Functions and control flow

- **Return early.** Handle the error or the uncommon case first and keep the happy path at
  the left margin. No `else` after a `return`.
- **No Boolean parameters in exported signatures.** `Render(true)` is unreadable at the
  call site and can't grow a third mode. Use a named type, an options struct, or two
  functions.
- **Options structs** for three or more optional settings; pass them by value and make the
  zero value mean "defaults". Use functional options (`WithTimeout(d)`) only in a library
  whose constructor must stay compatible as options grow.
- **Naked returns** only in a function short enough to see the named results.
- **`defer` releases resources** right after acquisition succeeds. Check the error from
  `Close` on anything you wrote to:

```go
func writeReport(path string, data []byte) (err error) {
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer func() { err = errors.Join(err, f.Close()) }()
	_, err = f.Write(data)
	return err
}
```

- **`new(expr)` replaces pointer helpers.** Write `Limit: new(10)`, not a `ptr(10)` or
  `intPtr` helper. `go fix` rewrites the helpers for you.
- **Iterators for sequences callers stream.** Return `iter.Seq[T]` or `iter.Seq2[K, V]`
  when the caller may stop early or the data is large. Return a slice when the caller
  needs `len`, indexing, or a second pass.

```go
func (s *Store) Active() iter.Seq[User] {
	return func(yield func(User) bool) {
		for _, u := range s.users {
			if u.Active && !yield(u) {
				return
			}
		}
	}
}

type User struct{ Active bool }
type Store struct{ users []User }
```

- Use `slices` and `maps` for searching, sorting, cloning, and comparing:
  `slices.Contains`, `slices.SortFunc(xs, func(a, b T) int { return cmp.Compare(a.K, b.K) })`,
  `slices.Sorted(maps.Keys(m))`. Sorting map keys gives output a stable order, because Go
  randomizes map iteration on purpose.

## 6. Types, interfaces, and generics

- **Accept interfaces, return concrete types.** A function takes the smallest interface
  it needs (`io.Reader`, not `*os.File`) and returns a struct pointer callers can use in
  full.
- **Define an interface beside its consumer**, not beside its implementation, and only once
  a second implementation or a real test double exists. A package that exports an
  interface and its only implementation is Java in Go syntax.
- **Keep interfaces small:** one to three methods. Compose bigger ones from smaller ones
  (`io.ReadWriteCloser`).
- **Never take or store a pointer to an interface.**
- **Assert an implementation at compile time** when the relationship matters:
  `var _ http.Handler = (*Server)(nil)`.
- **Receivers:** pointer receivers when the method mutates, the struct holds a lock or is
  large, or any other method needs one. Don't mix pointer and value receivers on one type
  (`recvcheck` flags it).
- **Make the zero value useful** where that's safe: `var buf bytes.Buffer` and
  `var mu sync.Mutex` work without a constructor. When it can't be, unexport the type's
  fields and provide `New`.
- **Embedding is composition, not inheritance.** Embedding exports every promoted method.
  Don't embed a type in an exported struct only to save typing, and never embed
  `sync.Mutex` in an exported struct, because `Lock` becomes part of your API.
- **Strong types for units and IDs.** `time.Duration`, `time.Time`, and named types like
  `type OrderID string` stop callers mixing values. Prefer `uuid.UUID` from the standard
  library for UUIDs.
- **Generics** when several types would otherwise repeat the same algorithm or container
  code: `func Index[S ~[]E, E comparable](s S, v E) int`. Don't use type parameters to
  dodge an interface that has methods; an interface with methods is already polymorphic.
  Since Go 1.27, methods can take their own type parameters, so a transform like
  `func (l List[T]) Map[U any](f func(T) U) List[U]` is a method; interface methods still
  can't be generic.
- Use `~T` constraints so named types work, and `cmp.Ordered` or `comparable` before
  inventing a constraint.

## 7. Errors and panics

| Situation | Use |
|---|---|
| Absence is normal (`map` lookup, cache miss) | comma-ok: `v, ok := m[k]` |
| The caller may act on what failed | an `error` value |
| A bug or broken invariant inside your code | `panic` with a message that has the values |

- **Check every error.** Ignore one only with a comment that says why it's safe:
  `_ = conn.SetDeadline(t) // best effort; the read below reports a dead conn`.
- **Handle an error once.** Return it with context, or log it and stop, never both. Logging
  at every level writes one failure five times.
- **Add context that callers lack**, lowercase, no trailing punctuation, no "failed to":
  `fmt.Errorf("load config %s: %w", path, err)`.
- **`%w` or `%v` is an API choice.** `%w` lets callers match the cause with `errors.Is`
  and makes the cause part of your contract. Use `%v` when the cause is an internal detail
  you may change.
- **Match with `errors.Is` and `errors.AsType`.** Never compare `err.Error()` strings, and
  never use `==` on an error that might be wrapped.

```go
func describe(err error) string {
	if pe, ok := errors.AsType[*fs.PathError](err); ok {
		return "path problem: " + pe.Path
	}
	if errors.Is(err, fs.ErrNotExist) {
		return "missing"
	}
	return "other"
}
```

- **Exported functions return the `error` interface,** never `*MyError`. A nil `*MyError`
  stored in an `error` is not `nil`, and the caller's `err != nil` check fires.
- **Sentinels** (`var ErrNotFound = errors.New("not found")`) for conditions callers test
  for. **Error types** (`type ParseError struct{ Line int; Err error }` with `Unwrap`) when
  callers need fields. Export only what callers can act on.
- **Combine independent errors** with `errors.Join`, for example when closing several
  resources.
- **No in-band sentinels.** Don't return `-1`, `""`, or `nil, nil` to mean "failed" or
  "not found"; return `ok bool` or an error.
- **`panic` is for programmer errors:** impossible states, broken invariants, or invalid
  constant input to a `Must` function at package initialization (`regexp.MustCompile`).
  A library never panics on caller input, and never uses `recover` for control flow. A
  server may recover at the request boundary to log and return 500; `net/http` already
  does.
- **`os.Exit` and `log.Fatal` only in `main`.** Have `main` call `run() error` so deferred
  cleanup runs and tests can call `run`.

## 8. Context and concurrency

- **`ctx context.Context` is the first parameter** of every function that blocks, does
  I/O, or calls something that does. Don't store it in a struct (`containedctx`), and
  don't replace a caller's context with `context.Background()` (`contextcheck`).
- **Cancel what you derive:** `ctx, cancel := context.WithTimeout(ctx, d)` is followed by
  `defer cancel()`. Use `context.WithoutCancel` for work that must outlive the request,
  such as an audit write, and `context.WithCancelCause` when the reason matters.
- **Context values** carry request-scoped data such as a trace ID, never optional
  parameters. Key them with an unexported type.
- **Prefer synchronous APIs.** Let the caller add concurrency. A function that starts a
  goroutine and returns hides a lifetime the caller can't see.
- **Every goroutine has an owner, a stop signal, and a wait.** No fire-and-forget. Start
  goroutines with `wg.Go` or `errgroup.Group.Go`, so the wait can't be forgotten:

```go
func fetchAll(ctx context.Context, urls []string) ([][]byte, error) {
	g, ctx := errgroup.WithContext(ctx)
	g.SetLimit(8)
	bodies := make([][]byte, len(urls))
	for i, u := range urls {
		g.Go(func() error {
			b, err := fetch(ctx, u)
			if err != nil {
				return fmt.Errorf("fetch %s: %w", u, err)
			}
			bodies[i] = b
			return nil
		})
	}
	return bodies, g.Wait()
}

var client = &http.Client{Timeout: 10 * time.Second}

func fetch(ctx context.Context, url string) ([]byte, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, err
	}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	return io.ReadAll(resp.Body)
}
```

- **Channels transfer ownership; mutexes protect state.** Pick whichever makes the code
  shorter. Keep the mutex next to the fields it guards, keep critical sections a few lines
  long, and never call a caller's function or block on I/O while holding a lock.
- **Channels:** the sender closes, once. Declare direction in signatures (`<-chan T`,
  `chan<- T`). Unbuffered or size one by default; a bigger buffer needs a stated reason.
  Every blocking send or receive also selects on `ctx.Done()`.
- **Don't copy values that contain a lock or an atomic** (`go vet` copylocks). Use typed
  atomics (`atomic.Int64`, `atomic.Pointer[T]`) for a lone counter or flag, and
  `sync.OnceValue` or `sync.OnceFunc` for lazy initialization.
- **No goroutines in `init`.** Expose `Start`, `Close`, or `Shutdown`, and give background
  loops a context.
- **Find leaks.** Test concurrent code with `go test -race`, use `testing/synctest` for
  code that waits on time, and inspect `pprof.Lookup("goroutineleak")` when goroutine
  counts grow.

## 9. Data, I/O, and boundaries

- **Slices:** a nil slice is a valid empty slice; test with `len(s) == 0`. Preallocate
  with `make([]T, 0, n)` when `n` is known. Copy (`slices.Clone`, `maps.Clone`) a slice or
  map at an API boundary when retaining it would share mutable state.
- **Maps:** a nil map reads fine and panics on write. Iteration order is random, so sort
  keys before output, hashing, or golden files.
- **Time:** `time.Duration` for spans, `time.Time` for instants, both at API boundaries.
  A field such as `TimeoutSeconds int` is a bug waiting for a unit mix-up; if a wire format
  forces one, put the unit in the name.
- **Strings:** `strings.Builder` or `fmt.Fprintf` for repeated construction, `strconv`
  for conversions, `strings.Cut` and `strings.CutPrefix` for splitting once.
- **JSON:** use `omitzero` rather than `omitempty` for structs, `time.Time`, and values
  whose zero value is meaningful. New code that needs strict decoding (duplicate keys,
  invalid UTF-8, case-sensitive names) uses `encoding/json/v2`. Since Go 1.27,
  `encoding/json` runs on the v2 engine, so don't assert on its error text.
- **Files from untrusted names:** open them through `os.OpenRoot(dir)` so `../` and
  symlinks can't escape the directory.
- **Randomness:** `crypto/rand` for anything secret (`rand.Text()` for tokens);
  `math/rand/v2` for everything else. Never seed a global generator.
- **HTTP servers:** set `ReadHeaderTimeout` on `http.Server`, shut down with
  `srv.Shutdown(ctx)` under a deadline, register routes as `mux.HandleFunc("GET
  /items/{id}", h)` and read `r.PathValue("id")`, and wrap state-changing browser
  endpoints in `http.NewCrossOriginProtection()`.
- **HTTP clients:** never use the default client without a timeout for outbound calls,
  build requests with `http.NewRequestWithContext`, and always close the response body.
- **Configuration** is read once in `main` and passed down. Don't read environment
  variables or flags inside libraries or request handlers.
- **Finalizers:** use `runtime.AddCleanup`, not `runtime.SetFinalizer`, and never for
  anything a `Close` method should do.

## 10. Logging and observability

- Use `log/slog` for operational logs. The message is a constant; variable data goes in
  attributes: `logger.InfoContext(ctx, "order shipped", "order_id", id)`. `sloglint` keeps
  attribute style consistent.
- Pass a `*slog.Logger` to the component that logs, or use `slog.Default()` in an
  application. Libraries mostly return errors and don't log at all.
- Never log credentials, tokens, or personal data. Implement `slog.LogValuer` on types
  that hold secrets so they print redacted.
- Use `slog.DiscardHandler` in tests and benchmarks that don't inspect logs.

## 11. Tests

- **Test the public behavior.** Prefer `package foo_test` so tests use the API the way
  callers do. Use internal tests only for logic with no public way in.
- **Table-driven tests** when cases share one flow. Name each case, run it with `t.Run`,
  and use `t.Parallel()` when cases are independent. Since Go 1.22, the loop variable is
  fresh per iteration, so no `tc := tc`.
- **Failure messages** name the call, the input, what you got, and what you wanted, in
  that order: `t.Errorf("Parse(%q) = %v, want %v", in, got, want)`. Use `go-cmp`'s
  `cmp.Diff` for structs; don't add an assertion library.
- Use `t.Helper()` in helpers, `t.Cleanup` for teardown, `t.Context()` for a context
  that cancels when the test ends, `t.TempDir()` and `t.Chdir()` for files, and
  `t.Setenv` for environment variables.
- **Errors** are checked with `errors.Is` or `errors.AsType`, not by comparing text.
- **Time and concurrency:** wrap tests that use timers, tickers, or `time.Sleep` in
  `synctest.Test(t, func(t *testing.T) { ... })` so they run on a fake clock and can't
  flake.
- **HTTP:** test handlers with `httptest.NewRecorder` and clients against
  `httptest.NewServer`. Don't mock `http.Client`.
- **Benchmarks** use `for b.Loop() { ... }`, which keeps the compiler from deleting the
  work and excludes setup from timing. Compare runs with `benchstat`.
- **Fuzz** parsers and decoders of untrusted input with `func FuzzX(f *testing.F)`.
- **Examples** (`func ExampleParse()` with an `// Output:` comment) are tests and
  documentation at once.
- Real dependencies beat mocks: use a real temporary directory, an in-process server,
  or a database in a container (`testcontainers-go`) rather than an interface added only
  for mocking.

## 12. Documentation

- Every exported name has a doc comment that is a full sentence starting with the name:
  `// Parse reads a config file and reports the first invalid key.`
- Say what the signature can't: preconditions, which errors callers can match, whether
  the type is safe for concurrent use, and who owns returned slices and maps.
- The package comment sits above the `package` clause in one file, usually `doc.go`:
  `// Package config loads ...`.
- Doc comments support headings (`# Errors`), lists, and links (`[Client.Do]`,
  `[io.Reader]`). Use them; `go doc` and pkg.go.dev render them.
- Mark retired APIs with a `// Deprecated: use X instead.` paragraph. Add
  `//go:fix inline` to a deprecated function that is a one-line wrapper, so `go fix`
  rewrites callers for you.
- Comments explain why, not what. No commented-out code; version control remembers it.

## 13. Project layout

- Start with one package at the module root. Add packages when a second, separate purpose
  appears, not to mirror layers (`models`, `services`, `controllers`).
- Put commands in `cmd/<name>/main.go` when a module has more than one binary.
- Use `internal/` for packages other modules must not import. It is the only
  visibility boundary above the package.
- Don't create `pkg/`. It adds a path segment and says nothing.
- No package-level mutable state and no `init` side effects beyond registering with the
  standard library (`image.RegisterFormat`, `sql.Register`). Pass dependencies in.

## 14. Final checklist

- `go fix -diff`, `gofmt -l`, `go vet`, `golangci-lint run`, and `go test -race` are clean.
- Every error is checked, wrapped with useful context or returned once, and matched with
  `errors.Is` or `errors.AsType`.
- Every goroutine has an owner, stops on cancel, and is awaited; context flows from the
  caller.
- Interfaces are small and declared where they are used; exported functions return
  concrete types and the `error` interface.
- No Boolean parameters, `Get` prefixes, stuttering names, or `util` packages in the API.
- Output that iterates a map sorts the keys first.
- The code uses what the `go` line allows: `range` over integers and iterators,
  `min`/`max`, `slices`, `maps`, `new(expr)`, `wg.Go`, `t.Context()`, `b.Loop()`.
- Exported names have doc comments; tests cover success, failure, and edge cases.

## References

Read these when you need the reasoning behind a rule or a full checklist.

- `references/effective-go.md` (https://go.dev/doc/effective_go): language idioms, naming,
  embedding, interfaces, and goroutines.
- `references/code-review-comments.md` (https://go.dev/wiki/CodeReviewComments): the
  review checklist the Go team uses.
- `references/google-go-style.md` (https://google.github.io/styleguide/go/): clarity,
  package design, errors, tests, and when not to abstract.
- `references/uber-go-style.md` (https://github.com/uber-go/guide): defensive API design,
  errors, time, goroutine lifetime, and performance.
- `references/concurrency-patterns.md`: goroutine lifetime, pipelines, cancellation,
  worker pools, and shutdown.
- `references/modern-go.md` (https://go.dev/doc/devel/release): what each release from
  Go 1.21 to Go 1.27 added, and what `go fix` rewrites.
