//go:build go1.22

package beautifullintcheck

import "crypto/rand"

// TooNewForGo122 calls a Go 1.24 stdlib symbol under a go1.22 constraint, which vet:stdversion reports.
func TooNewForGo122() string {
	return rand.Text()
}
