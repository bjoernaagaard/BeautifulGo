---
name: go-port
description: >-
  Port code from C, C++, Python, Java, JavaScript, TypeScript, Rust, or older Go into
  idiomatic modern Go that keeps the original behavior: error values instead of
  exceptions and error codes, typed constants instead of magic strings, small interfaces
  instead of class hierarchies, and ported tests that prove the match. Use for port,
  translate, convert, migrate, rewrite, or modernize requests ("rewrite this in Go",
  "what would this look like in Go"), even if the user doesn't say "port".
---

# Go port

Write the Go a Go developer would have written to solve the same problem, with the same
observable behavior. A line-by-line transliteration keeps every problem the original had
and adds Go's verbosity on top. Port the behavior, not the structure.

## 1. Understand the original first

1. Read the code, its tests, and its callers, if you have them.
2. List the observable behavior: every public function, its inputs and outputs, and every
   way it can fail. Include the quiet parts, where ports go wrong: result order, how ties
   break, empty input, whitespace and case handling, integer limits and overflow, and what
   counts as an error versus a valid edge case.
3. Note what is incidental, meaning things the original does only because of its
   language: manual memory management, out-parameters, `NULL` returns, global state,
   fixed buffers, a class that only groups functions, or `isinstance` checks. Leave those
   habits out of the port.
4. If the original has a bug or an ambiguity, keep its behavior, flag it in the porting
   notes, and let the user decide. A port is not the place to fix things silently.

## 2. Port the tests first

Translate each original test into a Go test before porting the implementation. Keep one
Go test or one table row per original test, with a name that maps back to it
(`TestParse/empty_input` for `test_parse_empty_input`), so a reader can check coverage.
If the original has no tests but runs, compare the port's output with the original's on
the same inputs instead (section 6).

## 3. Design the Go API, then implement it

Decide the packages, types, and signatures from the behavior list, not from the
original's shape. Follow the `go-best-practices` skill for style, and use what the target
module's `go` line allows (iterators, `min`/`max`, `slices`, `maps`, `errors.AsType`).
Where a row below differs from `go-best-practices`, the row wins, because the original's
observable behavior comes first.

### From C and C++

| In the original | In Go |
|---|---|
| `malloc`/`free`, `new`/`delete`, `create`/`destroy` pairs | Values and slices the garbage collector frees; `Close` only for resources with explicit release, such as files, connections, and rows |
| `NULL` meaning "absent" | A comma-ok result, or a nil pointer or slice where nil is already meaningful |
| Error codes, `-1`, `errno` | An `error`; one sentinel (`ErrX`) per code callers test, or an error type with fields |
| Out-parameters (`int *err_line`) | Extra return values, or fields on the error type |
| Flag bitmasks | An options struct with named `bool` fields, or a named integer type with `1 << iota` constants (explicit values when the original's numbers are visible) |
| `char *` plus length | `string` or `[]byte` |
| `strcmp` | `==` for equality; `<` or `strings.Compare` for ordering |
| `strcasecmp` | `strings.EqualFold` for equality; for ordering, compare case-folded strings with the original's folding rules (ASCII only in the C locale) |
| Pointer plus count | A slice |
| Fixed-size buffers | Growing slices and `strings.Builder`; keep a limit only if it is behavior |
| `#define` constants and macros | `const`, typed constants, and functions |
| Global mutable state | A struct the caller creates and owns |
| `strtol` and friends | `strconv.ParseInt` with an explicit bit size; map its `*NumError` to your error |
| Signed overflow (undefined in C) | Go wraps signed integers silently; add a check where the original relied on a range |
| Implicit integer promotion and mixed signed/unsigned arithmetic | Explicit conversions; pick the type the C expression evaluated in, and keep unsigned wraparound with `uint` types |

Don't use `unsafe` or cgo unless the port must call C, and then keep it in one small
package behind a safe API.

### From Python

| In the original | In Go |
|---|---|
| An exception hierarchy | Sentinel errors or error types, matched with `errors.Is` and `errors.AsType` |
| `None` | A comma-ok result, a nil pointer, or the zero value when it can't be confused with data |
| Strings used as a closed set | A named string type with constants and a parse function |
| Dicts or classes used as records | Structs with named fields |
| Dict iteration order (insertion order) | A slice, or a map plus a slice of keys, when order is observable |
| Duck typing, `isinstance` | A small interface, or a type switch |
| Unbounded `int` | A sized integer chosen on purpose, with overflow checked where input is large, or `math/big` |
| Generators and `yield` | `iter.Seq[T]` |
| `sorted(..., key=...)` | `slices.SortStableFunc`; Python's sort is stable, `slices.SortFunc` is not |
| `with` blocks | `defer` right after the acquisition succeeds |
| `//` and `%` (floor toward negative infinity) | Go's `/` and `%` truncate toward zero; adjust when operands can be negative |
| `len(s)`, `s[i]` on `str` (code points) | `len` and indexing count bytes; use `utf8.RuneCountInString` and `for i, r := range s`, or `[]rune(s)` |

### From Java, JavaScript, TypeScript, and Rust

- Java: classes that group static methods become package functions; streams become
  `range` loops or `slices`/`maps` calls; checked exceptions become `error` returns;
  `Optional` becomes comma-ok; inheritance becomes embedding or an interface.
- JavaScript and TypeScript: `null` and `undefined` become comma-ok or the zero value;
  thrown errors become `error` returns; promises become synchronous functions that take a
  `context.Context`, with goroutines only where the original ran work concurrently;
  numbers become a sized integer or `float64`, chosen on purpose; `length` and indexes on
  strings count UTF-16 code units, so convert with `unicode/utf16` where they are observable; union types become an
  interface with a type switch or a struct with a kind field.
- Rust: `Result` becomes `(T, error)`; `Option` becomes comma-ok; traits become small
  interfaces or generic constraints; enums with data become an interface with one type
  per variant; `Drop` becomes `Close` plus `defer`. Lifetimes and ownership annotations
  have no Go equivalent and disappear.
- Older Go: `go fix -diff ./...` previews and `go fix ./...` applies the rewrites for
  `interface{}`, `sort.Slice`, `x := x` loop copies, `wg.Add(1)` with `defer wg.Done()`,
  `errors.As` targets, and pointer helpers. `go fix` also replaces most `io/ioutil`
  calls; replace `ioutil.Discard`, `ioutil.ReadDir` and `b.N` loops by hand (staticcheck
  SA1019 flags the import).

## 4. Keep the port proportionate

Match the original on the inputs it actually receives, and use Go's standard library for
the rest.

- **Don't reimplement the source runtime.** Use `strconv`, `strings`, `unicode`, and
  `time`, not hand-written copies of Python's `strip`, C's `strtol`, or JavaScript's
  `Number` parsing. Where Go differs only on exotic input (Unicode digits, non-ASCII
  whitespace, huge integers), list the difference in the notes instead of coding around
  it.
- **Don't grow the API.** Port the public surface the original has, plus a `String`
  method on enums and errors that implement `error`. Skip functional options, extra
  interfaces, and generic helpers the callers don't need.
- **Keep the algorithm** unless it has a real correctness or performance problem on
  realistic input, and say so in the notes when you change it.
- **Check the size.** Count non-test, non-comment lines. A port from C, C++, or Java
  usually lands near the original's size. A port from Python or JavaScript usually lands
  at one and a half to two and a half times the original, because error handling and
  types are explicit in Go. Much more than that usually means one of the habits above.

Differential testing against the original is worth doing, but a few dozen realistic and
edge-case inputs answer the question. If the original is runnable, add a Go fuzz test
for a parser and compare outputs on its corpus rather than millions of random inputs.

## 5. Optional similarity map

If [`jscpd`](https://github.com/kucherenko/jscpd) 5.4 or later is installed, the experimental `jscpd --compare source/ target/`
(which may need `jscpd --semantic-download` first) pairs functions in the
original with similar functions in the port, which helps you find code you haven't
ported yet. Run it with the same paths and options each time, source first. A similar
pair does not prove the two behave alike; the ported tests decide that.

## 6. Verify

Run the commands in section 1 of `go-best-practices`, and fix everything before
reporting.

Every ported test must pass. If the original's tests can still run, run them too and
compare results on the same inputs.

## 7. Write the porting notes

Write a short `PORTING.md` beside the code that a reviewer can check in a few minutes:

- **API mapping:** a table from each original function or type to its Go equivalent.
- **Test mapping:** each original test and the Go test that covers it.
- **Deliberate differences:** anything that now behaves differently, and why.
- **Preserved quirks:** odd behavior kept on purpose, so nobody fixes it by accident.
- **Verification:** the commands you ran and their results, or a plain statement that a
  command couldn't run.
