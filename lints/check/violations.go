// Package beautifullintcheck holds one known violation per linter that
// scripts/check-lints.sh expects lints/golangci.yml to report.
package beautifullintcheck

import (
	"context"
	"errors"
	"fmt"
	"io"
	"net/http"
)

// ErrMissing is a sentinel used by the errorlint violation.
var ErrMissing = errors.New("missing")

// Job stores a context, which containedctx reports.
type Job struct {
	ctx context.Context
}

func unchecked() error {
	return fmt.Errorf("disk full")
}

// Ignored drops an error, which errcheck reports.
func Ignored() {
	_ = unchecked()
}

// BadName returns a capitalized error string, which revive reports.
func BadName() error {
	return fmt.Errorf("Bad name.")
}

// Compare tests a possibly wrapped error with ==, which errorlint reports.
func Compare(err error) bool {
	return err == ErrMissing
}

// Fetch has no context and leaks the response body, which noctx and bodyclose report.
func Fetch(url string) (int, error) {
	resp, err := http.Get(url)
	if err != nil {
		return 0, err
	}
	return resp.StatusCode, nil
}

// Name asserts without a comma-ok check, which forcetypeassert reports.
func Name(v any) string {
	return v.(string)
}

// Old uses interface{}, which modernize reports.
func Old(v interface{}) interface{} {
	return v
}

// Quiet has a bare nolint directive, which nolintlint reports.
func Quiet(r io.Reader) {
	r.Read(nil) //nolint
}
