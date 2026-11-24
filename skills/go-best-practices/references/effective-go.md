# Effective Go (digest)

Source: https://go.dev/doc/effective_go

Effective Go is the Go team's original tutorial on writing clear, idiomatic Go. The page says it was written in 2009 and has not been updated much since, so it knows nothing about modules, generics, iterators, or `log/slog`. Read this digest when you need the reasoning behind a naming, interface, embedding, or concurrency choice. `modern-go.md` lists what each release since the source changed; follow it where the two differ.

## Formatting and comments

- Run `gofmt` and accept its output. Do not argue about layout, because the tool settles it for every Go program.
- Use `//` line comments. Block comments `/* */` appear mostly as package comments, inside an expression, or to disable a large block of code.
- Every exported name gets a doc comment that starts with the name, for example `// Compile parses a regular expression and returns...`. Then `go doc` output reads well.
- Write one package comment above the `package` clause. For a large package it can be a long overview, and for a small package a sentence is enough.
- A comment on a grouped `const` or `var` block can describe the whole group, and a single declaration can still carry its own comment.
- Since Go 1.19, doc comments support headings, lists, and links, and `gofmt` reformats them.

## Names

- The package name is the context for every exported name, so a caller writes `bufio.Reader`, not `bufio.BufReader`. Choose short, lowercase, single word package names, and do not use underscores or mixedCaps.
- The package name is the base of its directory, so `encoding/base64` is `base64`, not `encoding_base64`. You do not need to avoid collisions up front, because importers can rename an import.
- Do not use `import .` outside rare test cases.
- Getters do not get a `Get` prefix. A field `owner` has a getter `Owner()` and a setter `SetOwner()`.
- A one method interface is named after the method plus `er`, for example `Reader`, `Writer`, `Formatter`, or `Stringer`. Keep the canonical names `Read`, `Write`, `Close`, `Flush`, and `String` for methods with the canonical meaning and signature.
- Use `MixedCaps` or `mixedCaps` for multiword names. Visibility is set by the first letter, so there is nothing else to configure.

## Semicolons and control structures

- Go inserts semicolons at line ends, so an opening brace must sit on the same line as `if`, `for`, `switch`, or `func`.
- Omit the `else` when the `if` body ends in `return`, `break`, `continue`, or `goto`. The success path then runs down the page without indentation.
- An `if` and a `switch` can start with a short statement, such as `if err := f(); err != nil`. Use it to keep a variable in the smallest scope.
- Go has only `for`. It covers C style loops, `while` style loops, and `range` over slices, arrays, strings, maps, and channels. Ranging over a string yields runes and decodes UTF-8.
- To use only the index, write `for i := range x`. To use only the value, write `for _, v := range x`.
- `switch` has no automatic fall through, cases can be lists, and a `switch` without an expression tests `true`. The expressionless form is the idiomatic replacement for a long `if-else` chain.
- Use a type switch (`switch v := x.(type)`) to branch on the dynamic type of an interface value.
- The comma-ok form `v, ok := x.(T)` avoids a panic when the type is wrong.


## Functions

- A function can return several values. The usual pair is a result and an `error`, and the error comes last.
- Named results document what a function returns, and they are the only way a `defer` can change a result. Use naked returns only in short functions.
- `defer` runs when the surrounding function returns. Put `defer f.Close()` right after the successful `Open`, so the close sits next to the open.
- The arguments of a deferred call are evaluated when the `defer` statement runs, not when the call runs. Deferred calls run last in, first out.

## Data allocation

- `new(T)` returns a pointer to a zeroed `T`. Since Go 1.26 `new(expr)` also accepts a value and returns a pointer to a copy of it. `make` creates only slices, maps, and channels, and it returns an initialized value, not a pointer.
- Design types so the zero value is ready to use. `sync.Mutex` and `bytes.Buffer` work without setup, and a struct made of such fields keeps that property.
- A composite literal with field names (`&File{fd: fd, name: name}`) allocates and initializes in one step. Taking the address of a composite literal is fine and common.
- Arrays are values. Assigning or passing one copies it, so Go code uses slices almost everywhere.
- A slice is a view onto an array with a length and a capacity. Slices are references, so a function that changes elements of a slice argument changes the caller's data.
- `append` may return a new slice, so always assign the result: `s = append(s, x)`.
- Maps are references too. A lookup of a missing key returns the zero value, so use `v, ok := m[k]` to tell absent from zero. To use a map as a set, use `map[T]bool` or `map[T]struct{}`.
- `delete(m, k)` is safe when the key is absent.
- Print with `fmt`. `%v` is the default format, `%+v` adds field names, `%#v` is Go syntax, `%T` is the type, and `%q` quotes a string. Implement `String() string` to control `%v`, and never call `fmt.Sprintf("%s", x)` inside `x.String()`, which recurses forever.

## Initialization

- Constants are created at compile time, and `iota` numbers a group. Give an enum a named type and, when it is printed, a `String` method.
- Package level variables can be initialized by any expression, and Go orders them by dependency.
- Each file can have `init` functions. They run after all variable declarations. Use them to verify or repair state that cannot be expressed as a declaration, and avoid them otherwise, because they make behavior depend on import order and make tests harder to write.

## Methods

- Methods can be defined on any named type that is not a pointer or an interface, not only structs.
- Value receivers get a copy, and pointer receivers can change the receiver. The rule of thumb in the text is that value methods can be called on both values and pointers, while pointer methods can only be called on addressable values.
- Pick a pointer receiver when the method changes the value, when the value is large, or when other methods of the type already use one. Keep one choice for the whole type.

## Interfaces and other types

- An interface is satisfied implicitly. A type does not declare that it implements anything, so the interface can live in the package that uses it and the implementing package need not import it.
- Interfaces in Go are small. Most have one or two methods, which is why `io.Reader` and `io.Writer` combine with so many types.
- If a type exists only to implement an interface and has no other exported methods, Effective Go says to export only the constructor and have it return the interface, as `crc32.NewIEEE` returns a `hash.Hash32`. In all other cases, later guides (Code Review Comments and Google style) say to return the concrete type, and the skill follows them.
- To check at compile time that a type implements an interface, assign to the blank identifier: `var _ json.Marshaler = (*RawMessage)(nil)`. Do this only when no other code already forces the check.
- An interface value that holds a nil pointer is not nil. Return the `error` interface, not a concrete error pointer, to avoid this trap.
- Conversions between types with the same underlying type are cheap and legal, so a named slice type can borrow another type's methods by conversion, as `sort.Sort(Sequence(s))` does.
- A type switch with `case Stringer:` branches on behavior and not only on concrete types.

```go
type Stringer interface{ String() string }

func describe(v any) string {
	switch x := v.(type) {
	case Stringer:
		return x.String()
	case error:
		return x.Error()
	default:
		return "unknown"
	}
}
```

## The blank identifier

- Assigning to `_` discards a value. Never discard an error to silence a compiler complaint, and say why when you must.
- Import for side effects with `import _ "net/http/pprof"`. Only `main` packages and tests should do it.
- To silence an unused import or variable while developing, assign it to `_`, then remove the line before you commit.

## Embedding

- Embedding puts one type inside another without a field name, and the outer type gets the inner methods. When a promoted method runs, its receiver is the inner type, not the outer one, so there is no virtual dispatch.
- Embed an interface in a struct to take the interface's method set and override only some methods. Embed a struct to reuse its methods and fields.
- An outer name shadows an inner name at a shallower depth. Two names at the same depth conflict only if the program uses them.
- Embedding is composition. It is not subclassing, so avoid it when the inner type's methods should not be part of the outer type's API.

## Concurrency

- The slogan is "Do not communicate by sharing memory; instead, share memory by communicating." Pass data over a channel so only one goroutine owns it at a time. Use a mutex when guarding a small piece of shared state is simpler.
- Start a goroutine with `go f()`. It costs little, and it exits when the function returns. Nothing else stops it, so give each one a way to finish.
- An unbuffered channel synchronizes sender and receiver. A buffered channel works as a counting semaphore, and a send blocks only when the buffer is full.
- Receiving from a closed channel returns the zero value at once, so use `v, ok := <-ch` or `range ch` to detect the close. Only the sender closes a channel.
- A channel of channels lets a request carry its own reply channel.
- Parallelism and concurrency are different. Splitting work across goroutines does not make it faster unless the work can run at once.
- A leaky buffer pattern uses a buffered channel as a free list. It is a performance tool, so measure before using it.

Changes since the text was written:

- Use `context.Context` to cancel work. Effective Go predates it, and the rule today is to pass `ctx` as the first parameter and stop every goroutine when it is canceled.
- `errgroup` from `golang.org/x/sync/errgroup` joins goroutines and returns the first error.

## Iterators

Effective Go has no section on iterators, because they arrived in Go 1.23. Know these facts when you meet them.

- `iter.Seq[V]` is `func(yield func(V) bool)`, and `iter.Seq2[K, V]` yields pairs. A `for range` loop over such a function runs the loop body as `yield`.
- The iterator must stop calling `yield` once it returns false.
- Standard library helpers include `slices.Values`, `slices.Collect`, `slices.Sorted`, `maps.Keys`, `strings.SplitSeq`, and `strings.Lines`.

```go
func evens(n int) func(yield func(int) bool) {
	return func(yield func(int) bool) {
		for i := 0; i < n; i += 2 {
			if !yield(i) {
				return
			}
		}
	}
}
```

## Errors

- An error is a value of the built in `error` interface, which has one method, `Error() string`. Callers test it, wrap it, and return it like any value.
- Error strings should say which package or operation failed, for example `image: unknown format`. Today's rule is to lowercase the message and add the operation, since callers join messages with `: `.
- Define an error type when callers need fields from it. `*os.PathError` carries `Op`, `Path`, and `Err`, and the caller can print the whole thing or inspect the parts.
- Use `panic` only for unrecoverable states such as a bug. A library should return an error and not panic on bad input.
- `recover` works only inside a deferred function. A package can use panic and recover internally, and it must convert the panic to an `error` before returning to callers.
- Since Go 1.13 `fmt.Errorf` with `%w` wraps an error. Match with `errors.Is` and `errors.AsType`.

```go
func isPathError(err error) bool {
	_, ok := errors.AsType[*fs.PathError](err)
	return ok
}
```

## A web server and what to skip

- The text ends with a small web server that uses a channel as a handler. Read it for the idiom of a handler type with a method, and do not copy its package layout.
- Parts of the document that are out of date and safe to ignore include the `godoc` command and the GOPATH setup. Use modules and `go doc`.
- Generics arrived in Go 1.18. The text recommends interfaces for polymorphism, and that still holds when an interface with methods fits. Use type parameters when the same algorithm applies to many element types.
