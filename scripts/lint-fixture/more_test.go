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
// which usetesting reports.
func TestEnv(t *testing.T) {
	helper(t)
	_ = os.Setenv("A", "1")
	_ = context.Background()
}
