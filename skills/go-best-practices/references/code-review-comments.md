# Go Code Review Comments (digest)

Source: https://go.dev/wiki/CodeReviewComments

Go Code Review Comments is a wiki page where the Go team collects the small mistakes it flags most often in code review. It is a list of checks and not a full style guide, and it is meant to be read next to Effective Go. Read this digest when a review finding needs the original rule, or before you hand back code that you want to pass review. The wiki was written before generics, iterators, and `slog`. `modern-go.md` lists what each release since the source changed; follow it where the two differ.

## Formatting and comments

- Run `gofmt`. Many teams also run `goimports`, which formats and fixes the import block.
- Comments for declarations are full sentences that start with the name being described and end with a period.
- A package comment is a full sentence that starts with `Package name`, and every exported name has a doc comment.
- Do not write comments that only repeat the code.
- Write comments that a reader can follow without the code open, because `go doc` shows the comment without the body.

## Naming

- Use `MixedCaps` and never underscores in Go names, except in test function names such as `TestFoo_bar` and in generated code.
- Constants use mixed caps like other names, so an unexported limit is `maxLength`, not `MAX_LENGTH` or `MaxLength`.
- Initialisms keep one case. Write `URL` or `url`, never `Url`, and write `ServeHTTP`, `appID`, and `xmlHTTPRequest`.
- Package names are lowercase with no underscores and no plurals, and they should not be generic names like `util`, `common`, or `misc`. The package name is part of every caller's reference, so `chubby.File` needs no `ChubbyFile`.
- Do not use a package name that callers would commonly want as a variable name.
- Receiver names are one or two letters taken from the type, such as `c` for `Client`. Do not use `this`, `self`, or `me`, and use the same name on every method of the type.
- Short names suit small scopes. A one letter name for a loop index or a short-lived reader is fine, and a name used far from its declaration needs more letters.
- Do not add `Get` to getter names. Use `Owner()`, not `GetOwner()`.
- Name a one method interface after the method with an `er` suffix. Keep a method named `Read`, `Write`, `Close`, or `String` only when it has the standard signature and meaning.
- Name variables for what they hold and not for their type. Names like `userSlice` and `nameString` add noise.

## Imports

- Avoid renaming imports unless names collide. If you must rename, rename the one that is the least used in the file or the most local.
- Do not use `import .`, except in a test file that cannot be part of the package under test due to import cycles.
- Group imports into the standard library block first, then other packages, and keep them sorted within each block. `goimports` does this.
- Use `import _` for side effects only in `main` or tests.

## Errors

- Return the `error` interface type. Do not return a concrete error type from an exported function, because a nil concrete pointer in an `error` interface is not nil.
- Do not discard errors with `_`. Handle it, return it, or in the rare case where it is safe to ignore, say why in a comment.
- Error strings are not capitalized unless they begin with a proper noun or an acronym, and they do not end with punctuation, because they are usually printed after other context.
- Handle an error first, return, and keep the normal path at the left. Do not put the normal path in an `else` after a returning `if`.
- Do not `panic` for normal error handling. Use error values and multiple returns.
- Do not use in-band errors such as `-1`, `""`, or `nil` to mean "not found". Return an extra `error` or `ok bool`, so callers cannot forget to check and cannot mistake a valid value for a failure.

Changes since the wiki was written:

- Since Go 1.13, wrap with `fmt.Errorf("...: %w", err)` and match with `errors.Is`. Match types with `errors.AsType`.
- Use `errors.Join` (Go 1.20) to combine independent errors.

## Interfaces

- Go interfaces belong to the package that consumes values of the interface type, not the package that implements them. The implementing package returns a concrete type, so new methods can be added without a refactor.
- Do not define an interface on the implementer side "for mocking". Design the API so tests use the real implementation through its public methods.
- Do not define an interface before it is used. Without a real caller you cannot tell what the interface needs.
- Accept interfaces and return concrete types, for example accept `io.Reader` and return `*Client`.
- Do not use a pointer to an interface. Pass the interface value, which already holds a pointer if needed.

## Receivers and values

- Choose between value and pointer receivers by these rules. Use a pointer if the method changes the receiver, if the struct has a `sync.Mutex` or similar field that must not be copied, if the struct is large, or if other methods already use a pointer. Use a value for small immutable structs, maps, funcs, channels, and basic types.
- Use the same kind on every method of a type when you can.
- Do not pass pointers to strings or interface values to save a few bytes. Pass the value. The exception is a large struct or a value that must be changed.
- If you are unsure, use a pointer receiver.
- Functions that take a `context.Context` take it as the first parameter, named `ctx`. Do not add a `Context` field to a struct type; pass it to each method that needs it. `containedctx` enforces this. The standard library's `*http.Request` is the one accepted exception, kept for compatibility.
- Do not create custom context types or use interfaces other than `context.Context` in function signatures.
- Context values are for request-scoped data that crosses process and API boundaries, and not for passing optional parameters.
- Contexts are immutable, so you can pass the same one to calls that share a deadline, cancellation, or trace data.

## Slices, maps, and zero values

- Declare an empty slice as `var t []string`, which is nil, and not `t := []string{}`, which is non-nil with length zero. Both have length zero and work with `append`, `len`, and `range`.
- Check emptiness with `len(s) == 0` and not `s == nil`. Do not design an API that makes callers tell nil from empty. The exception is encoding, such as JSON, where the two differ.
- Prefer a useful zero value over a constructor, so `var b bytes.Buffer` works.
- Copy a slice or map at an API boundary when keeping the caller's value would share mutable state. Since Go 1.21, use `slices.Clone` and `maps.Clone`.

## Goroutines and concurrency

- When you start a goroutine, make it clear when or whether it exits. Goroutines can block on channel sends or receives, and the garbage collector will not end a blocked goroutine even when no other goroutine can reach the channel. Each blocked goroutine leaks memory.
- Even a goroutine that is not leaked can cause hard to diagnose problems, such as a send on a closed channel panic or a race on data that the caller thinks it still owns.
- Keep concurrent code simple so that goroutine lifetimes are obvious. Where that is not possible, document when and why the goroutines exit.
- Prefer synchronous functions, which return results directly or finish callbacks before returning. They keep goroutines inside a call and make the code easier to reason about and test. Callers can add concurrency by calling the function from their own goroutine.
- Do not copy a value of type `sync.Mutex` or a struct containing one. Use a pointer, and let `go vet` catch copies.

## Tests and failure messages

- Failure messages say what was wrong with enough detail to debug without reading the test. The format is `YourFunc(%v) = %v, want %v`, with the call and input first, then the actual value, then the expected value.
- Use `got` and `want` as names. Print `got` first.
- Put test helpers in `t.Helper()` calls so failure lines point at the caller.
- Table tests are fine when cases share the same flow.

## Language and API details

- Prefer a struct literal with field names for any literal from another package, because adding a field then does not break callers. Positional literals are fine in a small local test table.
- Avoid shadowing predeclared names like `len`, `copy`, `new`, `error`, `min`, `max`, and `clear`. The last three became built in at Go 1.21.

## Other wiki items

- Do not name result parameters only to avoid declaring a variable. Name them when the names document two values of the same type, such as `(lat, lon float64)`, or when a deferred function must change the result.
- Avoid naked returns in functions longer than a few lines, because the reader must scroll to see what is returned.
- Keep lines readable. Go has no fixed line length limit, and the fix for a long line is usually a shorter name or a helper, not a wrapped call.
- Be careful when copying a struct from another package. A type such as `bytes.Buffer` holds a slice that aliases the original, so the copy and the original change each other. Copy only when the type's methods are safe on a copy.
- Use `crypto/rand` and not `math/rand` to generate keys, even for throwaway ones. Since Go 1.24, `rand.Text` from `crypto/rand` returns a text token. For ordinary random numbers use `math/rand/v2`.
- Document concurrency in the comment when it is not obvious, for example that a type is safe for concurrent use or that a method must not be called after `Close`.

## Generic code and newer additions

- The wiki says nothing about type parameters. Use them for algorithms and containers that repeat across element types, and use an interface when the caller supplies behavior through methods.
- Constrain with `cmp.Ordered`, `comparable`, or a `~T` union before you write a new constraint.
- Go 1.27 allows methods to declare their own type parameters. Interface methods still cannot.
- Prefer iterators (`iter.Seq`) when the caller may stop early, and a slice when the caller needs the length or a second pass.
- Use `log/slog` for structured logs, with a constant message and attributes for the data.
