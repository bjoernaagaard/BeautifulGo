# Uber Go style guide (digest)

Source: https://github.com/uber-go/guide/blob/master/style.md

The Uber guide is the style document Uber's Go teams use. It is a list of short rules, each
with a "bad" and a "good" example, and most rules exist to prevent a bug seen in a large
codebase. Read this digest when you design an exported API, decide how to copy or share data
across a boundary, name errors, or start a goroutine. The guide was written for Go 1.12 to
1.15 era code. Where a newer release replaces its advice, the section says so.

## Interfaces and receivers

- Do not use a pointer to an interface. An interface value already holds a type and a data
  pointer. Pass the interface by value.
- Verify at compile time that a type implements an interface when the link matters for callers:
  `var _ http.Handler = (*Handler)(nil)`.
- The zero value of `sync.Mutex` and `sync.RWMutex` is valid, so `new(sync.Mutex)` is not
  needed. Declare `var mu sync.Mutex` or a field `mu sync.Mutex`.
- Do not embed a mutex in an exported struct. Embedding exports `Lock` and `Unlock` as part of
  the API. Use a named field `mu sync.Mutex`.

```go
var _ http.Handler = (*Handler)(nil)

type Handler struct{}

func (h *Handler) ServeHTTP(w http.ResponseWriter, r *http.Request) {}

type SMap struct {
	mu   sync.Mutex // guards data
	data map[string]string
}
```

## Data at boundaries

- Slices and maps hold pointers to their data. Copy them when you receive them if you keep
  them, and when you return them if they are internal state. Use `slices.Clone` and
  `maps.Clone` (Go 1.21) in place of the loops and `append([]T(nil), s...)` forms in the guide.
- Prefer `var s []int` over `s := []int{}`. A nil slice is a valid empty slice. Test with
  `len(s) == 0`, not `s == nil`. Do not return `[]int{}` to mean "none", and note that a nil
  slice encodes as `null` in `encoding/json` while an empty one encodes as `[]`;
  `encoding/json/v2` encodes both as `[]`.
- A nil map reads fine and panics on write. Create maps with `make`. Give `make` a capacity hint
  when you know the size.
- Specify slice capacity with `make([]T, 0, n)` when `n` is known. It avoids repeated growth.
- Use `time.Time` for instants and `time.Duration` for spans. When an API can't, such as JSON,
  put the unit in the name (`IntervalMillis`). Use `t.Add` for calendar-free arithmetic and
  `AddDate` for calendar days.
- Add field tags (`json:"name"`) to any struct that is marshaled. The tag keeps the wire name
  stable when the field is renamed.
- Start enums at one when the zero value should not be a valid choice. Start at zero when the
  zero value is a sensible default.

```go
type Op int

const (
	Add Op = iota + 1
	Subtract
	Multiply
)

type Driver struct {
	trips []string
}

func (d *Driver) SetTrips(trips []string) { d.trips = slices.Clone(trips) }
func (d *Driver) Trips() []string         { return slices.Clone(d.trips) }
```

## Errors

- Choose the error form by what callers need. If callers do not match the error and the message
  is fixed, use `errors.New`. If it needs data, use `fmt.Errorf`. If callers match it, use a
  sentinel `var ErrX = errors.New("x")`. If callers need fields, use a custom type.
- Name exported sentinel errors with the prefix `Err` and error types with the suffix `Error`.
  Unexported ones use `err` and `Error` the same way.
- Wrap with `fmt.Errorf("...: %w", err)` when callers should match the cause. Use `%v` to hide
  the cause. Keep the context short and drop "failed to", because layers of it pile up
  (`failed to a: failed to b: failed to c`). Write `new store: ...`.
- Handle each error once. The choices are to return it, to log it and continue, to match it and
  degrade, or to wrap and return. Logging and returning the same error writes it at every
  level.
- Use a checked type assertion: `t, ok := i.(string)`. The single-value form panics.
- Match error types with `errors.AsType`, not the guide's `errors.As` target form.
- Use `errors.Join` (Go 1.20) to return several independent errors.
- Do not panic in production code. Return errors. Panic only for programmer bugs, such as an
  impossible state. `Must` helpers for constant input at start-up are the usual exception. In
  tests, call `t.Fatal` and `t.FailNow`, not `panic`.
- Call `os.Exit` or `log.Fatal` only in `main`, and only once. Put the logic in `run() error`,
  so deferred calls run and the logic can be tested.

```go
var ErrNotFound = errors.New("not found")

type ParseError struct {
	Line int
	Err  error
}

func (e *ParseError) Error() string { return fmt.Sprintf("line %d: %v", e.Line, e.Err) }
func (e *ParseError) Unwrap() error { return e.Err }

func openStore(name string) (*os.File, error) {
	f, err := os.Open(name)
	if err != nil {
		return nil, fmt.Errorf("open store: %w", err) // *fs.PathError already names the file
	}
	return f, nil
}
```

## Concurrency

- Do not fire and forget goroutines. Every goroutine needs a predictable stop time, or a way to
  be told to stop. Wait for it to exit. Use a `sync.WaitGroup` (or `wg.Go` since Go 1.25), a
  `done` channel, or a context. See `concurrency-patterns.md`.
- Do not start goroutines in `init()`. Expose an object with `Start`/`Close` or `Shutdown`
  methods so the caller controls the lifetime.
- Channels should have a size of one or none. Any larger size needs a reason and a way to
  say what happens when the buffer fills.
- Defer to clean up resources: unlock, close, cancel. The cost is small, and the cleanup is next
  to the acquire. Skip `defer` only in a hot loop where a measurement shows its cost.
- The guide recommends `go.uber.org/atomic` for type-safe atomics. Since Go 1.19, use
  `sync/atomic` types (`atomic.Bool`, `atomic.Int64`, `atomic.Pointer[T]`) instead.
- Run tests with the race detector.

## Globals, init, and names

- Avoid mutable globals. Pass the dependency in, for example a `now func() time.Time` field
  that a test replaces.
- Avoid `init()`. When you must use it, make it deterministic, free of other `init` ordering,
  free of environment, working directory, and arguments, and free of I/O. Compute the value in
  a helper and assign it to the variable.
- Prefix unexported top-level `var` and `const` with `_` so they are not confused with a local
  (`_defaultPort`). Unexported error values use `err`. This rule is Uber's own and many other
  style guides do not use it.
- Use `MixedCaps` for function names. Test function names may use underscores to group cases,
  such as `TestMyFunction_WhatIsBeingTested`.

## Declarations and control flow

- Reduce nesting. Handle errors and special cases first, then return early. Drop an `else` when
  the `if` body ends in a return.
- Use `var x T` when you want the zero value, and `:=` when you assign. Inside a function
  `var` is for a zero value or for a declaration that must be wide.
- Reduce scope: `if err := f(); err != nil { ... }` keeps `err` out of the rest of the
  function. Do not do it when the value is needed later.
- Avoid naked parameters. A call such as `printInfo("foo", true, true)` hides meaning. Use a
  comment (`/* isLocal */ true`) or, better, a custom type, since the guide's comment form
  still can't be checked by the compiler.
- Use `&T{}` in place of `new(T)` for structs, to match how a literal with fields looks. Since
  Go 1.26 use `new(expr)` for a pointer to a non-struct value.
- Use field names when initializing structs. Omit zero-value fields unless they carry meaning in
  the context. A test table with two or three fields is the exception.
- Format strings passed to a `Printf`-style function should be constants so `go vet` can check
  them. Name wrappers with a trailing `f` (`Wrapf`) so vet checks them too.
- Use `strconv` over `fmt` for converting primitives. It is faster and allocates less.

## Patterns

- Table tests suit the case where the cases share one flow. Name each case with a `name` field and
  `t.Run`. Avoid branching inside the loop. If cases need different logic, split the table or
  write separate tests. A table with several conditional fields (`shouldCallX`,
  `expectCallY`) is a sign to split.
- Use `t.Parallel()` when cases are independent.
- Functional options suit a public constructor that has three or more optional arguments
  and is likely to gain more. Define an unexported `options` struct, an `Option`
  interface with an unexported `apply` method, and `WithX` functions. Pass options as a final
  variadic argument. Do not use closures-as-options without the interface when you want to
  compare or print them.

```go
type options struct {
	cache  bool
	logger *slog.Logger
}

type Option interface{ apply(*options) }

type optionFunc func(*options)

func (f optionFunc) apply(o *options) { f(o) }

func WithCache(on bool) Option {
	return optionFunc(func(o *options) { o.cache = on })
}

func Open(addr string, opts ...Option) *Conn {
	o := options{logger: slog.Default()}
	for _, opt := range opts {
		opt.apply(&o)
	}
	return &Conn{addr: addr, opts: o}
}

type Conn struct {
	addr string
	opts options
}
```

## Lint

- The guide asks teams to run `errcheck`, `goimports`, `revive`, `govet`, and `staticcheck`.
  Run them in CI with `golangci-lint`. Fix the finding instead of silencing it, and keep the
  list short enough that everyone trusts it.
- Run `go fix -diff ./...` as well. It covers modern replacements for many older forms the
  guide shows, such as `interface{}` and loop variable copies.
