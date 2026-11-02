# Google Go Style Guide (digest)

Source: https://google.github.io/styleguide/go/ (the guide at /guide, the decisions at /decisions, and the best practices at /best-practices)

Google's Go style guide has three parts. The guide states the principles and is both canonical and normative. The decisions page rules on specific questions such as naming, imports, errors, and tests, and it is normative but not canonical. The best practices page gives advice that is neither, but is common at Google. Read this digest when you must choose between clarity and an abstraction, when you name something, or when you design an error, a test failure message, or a package boundary. The pages were written before iterators, `log/slog` guidance, and generic methods, so the notes that start with "In newer Go" say what changed.

## Principles, in priority order

1. **Clarity.** The reader should see what the code does and why. Put the why in a comment or a descriptive name, and keep the reader's effort low.
2. **Simplicity.** Use the least mechanism that does the job. Prefer a core language construct, then the standard library, then a library from your own codebase, and add a new dependency last.
3. **Concision.** Cut repeated names, boilerplate, and noise so the important part is easy to see.
4. **Maintainability.** Write for the next person who edits the code, and keep the code correct when its callers change.
5. **Consistency.** Match the surrounding package. Consistency within a package beats a second local idiom, and consistency with the wider Go ecosystem beats a private convention.

When two principles conflict, the earlier one wins. The guide also says that the style it describes is about readability, so a rule is not a reason to make code harder to read.

## Formatting and naming

- Run `gofmt`. There is no fixed line length. Do not split a line only to make it shorter. Prefer a refactor, such as a shorter name or a helper.
- Use `MixedCaps` and `mixedCaps`. Do not use underscores, except in test names and generated code. Constants are `MaxLength`, not `MAX_LENGTH`.
- Keep initialisms in one case, as in `URL`, `ID`, and `xmlAPI`.
- Do not repeat the package name in an exported name. Write `db.Load`, not `db.LoadFromDatabase`. Do not repeat the receiver type in a method name, or the type of a variable in its name.
- Function names that return a value are noun like (`Config()`), and functions that do work are verb like (`WriteTo`). Do not use `Get`. If a function does real work or I/O, `Fetch`, `Compute`, or `Load` tells the caller about the cost.
- Package names are short, lowercase, and lack underscores. Avoid `util`, `helper`, `common`, and `model`, because a name should say what the package provides. Split a catch-all package into packages named for their contents, such as `stringset` and `cache`.
- Receiver names are one or two letters and match the type's name. Use the same name on every method.
- Variable name length grows with scope. A name used in one or two lines can be one letter, and a package level name needs a full word.
- Single letter names are fine for conventional uses, such as `r` for an `io.Reader`, `i` for an index, and `T` for a type parameter.
- Test double packages are named after the real package plus `test` (`creditcardtest`), and the doubles inside are named for behavior (`AlwaysCharges`, `AlwaysDeclines`).

## Imports and package layout

- Group imports as the standard library, then other packages, then side effect imports, with blank lines between groups. Sort inside each group. Do not rename an import unless names collide or a generated name is unclear.
- Do not use `import .`. Import a package for side effects only in `main` or tests.
- Keep a package cohesive. A reader should be able to say what the package is for in a sentence, and the test of package size is whether the types need each other. Do not split a package only because it has many files, and do not join unrelated types.
- Global state hurts testing and reuse. A library should not force callers into an API that relies on global mutable state. Provide an instance type, and let `main` own the default instance.
- Avoid registries that rely on `init` in libraries. Let the caller wire things up.

## Errors

- Return `error` as the last result. A function that can fail returns an `error`, and it never returns an in-band value like `-1` or `""`. Return a `bool` for "not found" and an `error` for real failure.
- Do not return a concrete error type from an exported function, because a nil pointer stored in an `error` is not nil.
- Error strings are not capitalized and do not end in punctuation, unless they start with an exported name, a proper noun, or an acronym. A full message shown in a log or a test failure may be capitalized.
- Handle an error where it appears. Do not ignore one without a comment. A rare ignored error needs a stated reason.
- Do not add "failed to" to a message when it only repeats that the call failed. Add what the caller does not know, such as the operation name, and skip details the wrapped error already has, such as the file path.
- Put `%w` at the end of the format string, as in `fmt.Errorf("load settings: %w", err)`, so the message reads from newest context to root cause. A sentinel error is a reasonable exception, because putting it first can show the category.
- Choose `%w` or `%v` on purpose. `%w` makes the cause part of your API, because callers can match it. Use `%v` at a system boundary, such as an RPC or storage layer, when you do not want to expose the cause.
- Use sentinel values or types when callers must branch on a condition, and match with `errors.Is` or `errors.As`. Never branch on the error text.
- Document which sentinel errors or types a function returns, and say whether they are returned directly or wrapped. Document pointer vs value type when callers match with `errors.As`.
- Do not use `panic` for normal errors. Reserve it for API misuse that a caller must fix, and for failed initialization of a required value in a `Must` function. Do not call `log.Fatal` outside `main`. A library should return an error.
- Check program invariants during initialization when failure cannot be repaired, and stop in `main` with a clear message.
- In newer Go, use `errors.AsType[*T](err)` (Go 1.26) in place of `errors.As` with a target variable, and `errors.Join` to combine several errors.

## Functions and declarations

- Use `:=` for a non zero value and `var x T` for the zero value, so a reader sees which one is meant.
- Use field names in struct literals. Positional literals break when a field is added, and they hide meaning. A small local table is the usual exception.
- Omit repeated type names inside a slice or map literal, and omit zero value fields unless they add clarity.
- A nil slice is the preferred empty slice. Do not create one with `[]T{}` unless an encoder needs the difference. Test emptiness with `len(s) == 0`.
- Use size hints (`make([]T, 0, n)`) only when you know the size, or have measured the cost.
- Pass values, not pointers, for small types and for interfaces. Do not pass a pointer to save a few bytes.
- Choose pointer receivers when the method changes the receiver, when the type contains a lock or other uncopyable field, when it is large, or when other methods already use one. Do not mix pointer and value receivers on one type. If in doubt, use a pointer.
- Keep signatures short. When a call needs many optional settings, take an option struct or use variadic functional options, and prefer the struct unless the constructor must stay compatible as options grow. An option struct is a plain value that is easy to read at the call site.
- Do not take boolean flags that change behavior without a name at the call site. Use a named type or a separate function.
- Pass `context.Context` as the first parameter named `ctx`. Do not store it in a struct, and do not invent a custom context type. When a function blocks on a context, it should return `ctx.Err()`, and the doc should say so.
- Use named results only when the names document the values or a deferred function sets the result. Use a naked return only in a short function.
- Prefer a synchronous function. Let callers add concurrency, because a function that returns only after its work is done has a clear lifetime.
- Shadowing is legal and often risky. Do not shadow a package name or a predeclared identifier, and be careful with `err :=` in an inner scope that hides an outer `err`.
- Build strings with `+` for a few pieces, `fmt.Sprintf` for formatting, and `strings.Builder` for piecewise construction in a loop. Use a backtick string for multi line text. Use `%q` to print a string that may contain spaces or be empty.
- Use `any` and not `interface{}`.
- Avoid `reflect` and `unsafe` unless the problem needs them.

## Interfaces, types, and generics

- Interfaces belong in the package that consumes them. The producer returns a concrete type, so it can add methods later without breaking users.
- Do not define an interface before there is a real use. Do not export an interface and its only implementation together, and do not create an interface only to mock one local concrete type.
- Keep interfaces small. An interface of one or two methods is easy to implement, test, and compose.
- Do not use a pointer to an interface.
- Provide a test double package for a library only if users will need it. Otherwise prefer the real implementation with a fake transport or a real in-process server.
- Use generics when the same algorithm or container code would otherwise repeat for many types, and write the concrete version first. Do not use generics to get dynamic behavior that an interface already gives, and do not add a type parameter that has one instantiation.
- Do not add a general purpose API for a single use. A small unexported helper often says more than a generic exported one.
- In newer Go, Go 1.27 lets a method declare its own type parameters, which removes helper functions that existed only for that reason. Interface methods still cannot have type parameters.
- Use type aliases only for migration or when moving a type between packages.
- Copying a struct is safe only if its methods are safe on a copy. A type that holds a `sync.Mutex`, a `bytes.Buffer`, or a slice that aliases the original should be passed by pointer.

## Concurrency

- Make goroutine lifetimes obvious. State when and how each goroutine exits, and wait for it. A goroutine blocked on a channel is never freed by the garbage collector.
- Declare channel direction in signatures where it is known. Document who closes a channel, and only the sender closes.
- Go users assume that read only operations are safe for concurrent use and that mutating operations are not. Document concurrency when a type breaks that assumption, e.g. a read that changes internal state, or a type whose writes are safe for concurrent use.
- Protect shared state with a mutex placed next to the fields it guards, with a comment that names them.
- In newer Go, Go 1.25 added `sync.WaitGroup.Go` and `testing/synctest`, Go 1.22 made loop variables per iteration, and Go 1.27 added the `goroutineleak` profile. Follow those instead of the older patterns the pages show.

## Documentation

- Every exported name has a doc comment, and the first sentence starts with the name and summarizes it. Write full sentences.
- Document what the signature does not say. That includes the meaning of parameters that are not obvious, what the function does on cancellation, whether the result may be modified, who owns a returned slice or map, and which errors can be matched.
- Say when a function has side effects, blocks, or starts a goroutine that the caller must stop. Name the cleanup call that the caller must run.
- Document concurrency safety only when it is not what a reader would assume.
- A package comment starts with `Package name` and says what the package is for. Put a long one in `doc.go`.
- Use runnable `Example` functions as documentation, because the compiler and `go test` check them.
- Do not repeat in a comment what the code already says. Say why.

## Tests

- Test failures name the function, the input, the actual result, and the expected result, in that order. The conventional form is `YourFunc(%v) = %v, want %v`. Use `got` and `want` as variable names, and print `got` first.
- Report differences with `cmp.Diff(want, got)` from `github.com/google/go-cmp/cmp`, and add a note on the direction, for example `(-want +got)`. Do not compare printed text or use `reflect.DeepEqual` when options such as `cmpopts.EquateErrors` or `protocmp` are needed.
- Do not write an assertion helper that hides the failure message. Keep the check in the test function, where the failure line points at the code under test. A helper may do setup and cleanup, call `t.Helper()`, and call `t.Fatal` when setup fails.
- Prefer `t.Error` and `t.Errorf` for a mismatch, so one run shows several failures. Use `t.Fatal` when continuing would be meaningless or misleading. Never call `t.Fatal` or `t.FailNow` from a goroutine the test started. Use `t.Error` there and return.
- Use table driven tests when many cases share the same logic. Put field names in the table rows, give each case a name, and split a test into several functions when the logic differs. Use `t.Run` when you need isolation or filtering. Subtests are not mandatory.
- Test the error semantics and not the error text. Check with `errors.Is` or `errors.AsType`, and compare a message only when the message is the contract.
- Keep setup in the test that needs it. Shared package level setup makes a failure harder to trace.
- Use `t.Cleanup` for teardown. In newer Go, use `t.Context()` (Go 1.24) for a context that ends with the test, `t.TempDir` and `t.Chdir` for files, `b.Loop()` (Go 1.24) in benchmarks, and `synctest.Test` (Go 1.25) for code that waits on timers.
- Design a validation API that other packages call as returning a value or an error that the caller's test can check, and not as a function that takes a `*testing.T`.
- Do not write a test for a concrete type by first adding an interface to mock it. Test through the public API with a real or fake dependency.

## Newer Go and the source

- The three pages do not mention iterators. Return `iter.Seq[T]` or `iter.Seq2[K, V]` when callers stream and may stop early, and a slice when callers need the length or a second pass.
- Use `any` and the `slices`, `maps`, and `cmp` packages in place of `interface{}`, `sort.Slice`, and hand written loops.
- Go 1.26 `new(expr)` removes the need for helper functions that return a pointer to a literal.
- For JSON, Go 1.27 moves `encoding/json` onto `encoding/json/v2`. The pages predate that, so check the error text you assert on.
