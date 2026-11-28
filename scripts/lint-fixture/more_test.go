package beautifullintcheck

import (
	"context"
	"os"
	"testing"
)

// helper lacks t.Helper(), which thelper reports.
func helper(t *testing.T) {
	if t == nil {
		return
	}
}

// TestEnv uses os.Setenv and context.Background instead of t.Setenv and t.Context,
// which usetesting reports, and context.WithCancel with defer cancel, which
// fix:testingcontext rewrites.
func TestEnv(t *testing.T) {
	helper(t)
	_ = os.Setenv("A", "1")
	_ = context.Background()
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	_ = ctx
}

// TestSubParallel calls t.Parallel in a subtest without calling it in the parent,
// which tparallel reports.
func TestSubParallel(t *testing.T) {
	for _, name := range []string{"a", "b"} {
		t.Run(name, func(t *testing.T) {
			t.Parallel()
		})
	}
}
