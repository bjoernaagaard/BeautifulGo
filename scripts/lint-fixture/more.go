package beautifullintcheck

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"log/slog"
	"net/http"
	"os"

	"golang.org/x/exp/maps"
)

// NotFound is a sentinel without the Err prefix, which errname reports.
var NotFound = errors.New("not found")

// Color is an enum that Paint switches on without every case, which exhaustive reports.
type Color int

// The colors.
const (
	Red Color = iota + 1
	Green
)

// Paint misses Green in its switch.
func Paint(c Color) string {
	switch c {
	case Red:
		return "red"
	}
	return ""
}

// Keys uses golang.org/x/exp/maps where the standard library has maps, which exptostd reports.
func Keys(m map[string]int) []string {
	return maps.Keys(m)
}

// Nest grows a context inside a loop, which fatcontext reports.
func Nest(ctx context.Context, keys []string) context.Context {
	for _, k := range keys {
		ctx = context.WithValue(ctx, ctxKey{}, k)
	}
	return ctx
}

type ctxKey struct{}

// Background drops the caller's context, which contextcheck reports.
func Background(ctx context.Context) error {
	return work(context.Background())
}

func work(ctx context.Context) error { return ctx.Err() }

// Single is an interface with one method and one implementation in this package,
// which iface reports as identical to Other.
type Single interface{ Do() }

// Other has the same method set as Single, which iface reports.
type Other interface{ Do() }

// Mixed has pointer and value receivers, which recvcheck reports.
type Mixed struct{ n int }

// Get uses a value receiver.
func (m Mixed) Get() int { return m.n }

// Set uses a pointer receiver.
func (m *Mixed) Set(n int) { m.n = n }

// Wasted assigns a value that is overwritten before use, which wastedassign and
// ineffassign report.
func Wasted() int {
	x := 1
	x = 2
	return x
}

// Swallow returns nil when err is not nil, which nilerr reports.
func Swallow() error {
	_, err := os.Stat("x")
	if err != nil {
		return nil
	}
	return errors.New("present")
}

// Rows leaks sql.Rows and skips rows.Err, which sqlclosecheck and rowserrcheck report.
func Rows(ctx context.Context, db *sql.DB) error {
	rows, err := db.QueryContext(ctx, "select 1")
	if err != nil {
		return err
	}
	for rows.Next() {
	}
	return nil
}

// Log uses a dynamic message and mixed arguments, which sloglint reports.
func Log(ctx context.Context, msg string) {
	slog.InfoContext(ctx, msg, slog.Int("a", 1), "b", 2)
}

// Convert converts an int to int, which unconvert reports.
func Convert(n int) int {
	return int(n)
}

// Method uses a string literal for an HTTP method, which usestdlibvars reports.
func Method(ctx context.Context) (*http.Request, error) {
	return http.NewRequestWithContext(ctx, "GET", "https://example.com", nil)
}

func scale(n, factor int) int {
	if n < 0 {
		return 0
	}
	return n
}

// UseAlways calls scale, whose factor parameter is unused, which unparam reports.
func UseAlways(a, b int) int { return scale(a, a) + scale(b, b) }

// Seperate is misspelled, which misspell reports.
func Seperate() {}

// Shadowed has a switch with one case, which gocritic singleCaseSwitch reports.
func Shadowed(v int) bool {
	switch {
	case v > 0:
		return true
	}
	return false
}

// Printf passes a string to %d, which govet printf reports.
func Printf() string {
	return fmt.Sprintf("%d", "x")
}
