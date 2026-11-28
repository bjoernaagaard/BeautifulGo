package beautifullintcheck

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"net/http"
	"reflect"
	"sort"
	"strings"
	"sync"
	"sync/atomic"
	"unsafe"
)

// BadDirective has a space after // in a go:generate directive, which gocheckcompilerdirectives reports.
// go:generate echo hi
func BadDirective() {}

// NonCanonicalHeader uses a non-canonical HTTP header key, which canonicalheader reports.
func NonCanonicalHeader(h http.Header) string {
	return h.Get("content-type")
}

// AppendNonZero appends to a slice created with non-zero length, which makezero reports.
func AppendNonZero() []int {
	s := make([]int, 5)
	return append(s, 1)
}

// MirrorWrite converts a string to []byte for Buffer.Write, which mirror reports.
func MirrorWrite(b *bytes.Buffer) (int, error) {
	return b.Write([]byte("x"))
}

// NilnessErr checks one error and returns an SSA-proven nil error, which nilnesserr reports.
func NilnessErr() error {
	other := unchecked()
	if other != nil {
		return other
	}
	if err := unchecked(); err != nil {
		return other
	}
	return nil
}

// NilNil returns nil value and nil error, which nilnil reports.
func NilNil() (*int, error) {
	return nil, nil
}

// ShadowBuiltin shadows predeclared max, which predeclared reports.
func ShadowBuiltin(max int) int {
	return max
}

// LostCancel discards a cancel func, which vet:lostcancel reports.
func LostCancel(ctx context.Context) {
	_, _ = context.WithCancel(ctx)
}

// ResponseBeforeErrCheck defers Body.Close before checking err, which vet:httpresponse reports.
func ResponseBeforeErrCheck(req *http.Request) error {
	resp, err := http.DefaultClient.Do(req)
	defer resp.Body.Close() //nolint:errcheck // fixture for vet:httpresponse
	if err != nil {
		return err
	}
	return nil
}

type embeddedPart struct{ X int }

// OuterEmbed embeds embeddedPart to exercise fix:embedlit.
type OuterEmbed struct{ embeddedPart }

// BuildOuter uses a redundant nested embedded literal, which fix:embedlit rewrites.
func BuildOuter() OuterEmbed {
	return OuterEmbed{embeddedPart: embeddedPart{X: 1}}
}

// AtomicCounter uses sync/atomic functions on int64, which fix:atomictypes rewrites.
func AtomicCounter() int64 {
	var n int64
	atomic.AddInt64(&n, 1)
	return atomic.LoadInt64(&n)
}

// MyErr is a custom error type for fix:errorsastype.
type MyErr struct{ msg string }

func (e *MyErr) Error() string { return e.msg }

// MatchErr uses errors.As with a target variable, which fix:errorsastype rewrites.
func MatchErr(err error) string {
	var target *MyErr
	if errors.As(err, &target) {
		return target.msg
	}
	return ""
}

// CopyLoopVar copies a range variable unnecessarily, which fix:forvar rewrites.
func CopyLoopVar(xs []int) []func() int {
	var fs []func() int
	for _, x := range xs {
		x := x
		fs = append(fs, func() int { return x })
	}
	return fs
}

//go:fix inline
func oldPair(a, b int) int { return a + b }

// CallInline calls a //go:fix inline wrapper, which fix:inline rewrites.
func CallInline(a, b int) int {
	return oldPair(a, b)
}

// CopyMap copies a map with a loop, which fix:mapsloop rewrites.
func CopyMap(dst, src map[string]int) {
	for k, v := range src {
		dst[k] = v
	}
}

// MinInt computes the smaller of two ints with if/else, which fix:minmax rewrites.
func MinInt(a, b int) int {
	var x int
	if a < b {
		x = a
	} else {
		x = b
	}
	return x
}

func ptrHelper[T any](v T) *T { return &v }

// MakePtr calls a pointer helper, which fix:newexpr rewrites.
func MakePtr(v int) *int {
	return ptrHelper(v)
}

// OmitZeroStruct uses omitempty on a struct field, which fix:omitzero reports.
type OmitZeroStruct struct {
	Inner embeddedPart `json:"inner,omitempty"`
}

// SumRange uses a 3-clause loop, which fix:rangeint rewrites.
func SumRange(n int) int {
	total := 0
	for i := 0; i < n; i++ {
		total += i
	}
	return total
}

// IntType uses reflect.TypeOf(0), which fix:reflecttypefor rewrites.
func IntType() reflect.Type {
	return reflect.TypeOf(0)
}

// ReverseSum iterates a slice backward by index, which fix:slicesbackward rewrites.
func ReverseSum(xs []int) int {
	total := 0
	for i := len(xs) - 1; i >= 0; i-- {
		total += xs[i]
	}
	return total
}

// HasValue searches a slice with a loop, which fix:slicescontains rewrites.
func HasValue(xs []int, want int) bool {
	for _, x := range xs {
		if x == want {
			return true
		}
	}
	return false
}

// SortInts uses sort.Slice on basic ints, which fix:slicessort rewrites.
func SortInts(xs []int) {
	sort.Slice(xs, func(i, j int) bool { return xs[i] < xs[j] })
}

// FieldNames loops over NumField/Field, which fix:stditerators rewrites.
func FieldNames(t reflect.Type) []string {
	var names []string
	for i := 0; i < t.NumField(); i++ {
		names = append(names, t.Field(i).Name)
	}
	return names
}

// ConcatAll uses += in a loop, which fix:stringsbuilder rewrites.
func ConcatAll(xs []string) string {
	out := ""
	for _, x := range xs {
		out += x
	}
	return out
}

// BeforeColon uses strings.Index and slicing, which fix:stringscut rewrites.
func BeforeColon(s string) string {
	idx := strings.Index(s, ":")
	if idx >= 0 {
		return s[:idx]
	}
	return s
}

// StripPrefix uses HasPrefix and TrimPrefix, which fix:stringscutprefix rewrites.
func StripPrefix(s string) (string, bool) {
	if strings.HasPrefix(s, "pre:") {
		return strings.TrimPrefix(s, "pre:"), true
	}
	return s, false
}

// CountParts ranges over strings.Split, which fix:stringsseq rewrites.
func CountParts(s string) int {
	n := 0
	for range strings.Split(s, ",") {
		n++
	}
	return n
}

// ShiftPtr does unsafe uintptr arithmetic, which fix:unsafefuncs rewrites.
func ShiftPtr(p unsafe.Pointer, n uintptr) unsafe.Pointer {
	return unsafe.Pointer(uintptr(p) + n)
}

// RunWG uses wg.Add(1)/go/defer wg.Done(), which fix:waitgroupgo rewrites.
func RunWG() {
	var wg sync.WaitGroup
	wg.Add(1)
	go func() {
		defer wg.Done()
		_ = fmt.Sprint("work")
	}()
	wg.Wait()
}
