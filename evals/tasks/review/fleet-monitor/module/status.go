package fleet

import (
	"context"
	"fmt"
)

// Status is the health of one target.
type Status int

// The states of a target. StatusUnknown means the target has not been checked yet.
const (
	StatusUnknown Status = iota
	StatusUp
	StatusDegraded
	StatusDown
)

// String returns the lowercase name of s.
func (s Status) String() string {
	switch s {
	case StatusUp:
		return "up"
	case StatusDegraded:
		return "degraded"
	case StatusDown:
		return "down"
	default:
		return "unknown"
	}
}

// ParseStatus returns the Status whose String method returns name.
func ParseStatus(name string) (Status, error) {
	switch name {
	case "up":
		return StatusUp, nil
	case "degraded":
		return StatusDegraded, nil
	case "down":
		return StatusDown, nil
	}
	return StatusUnknown, fmt.Errorf("parse status: unknown name %q", name)
}

// MarshalText implements encoding.TextMarshaler.
func (s Status) MarshalText() ([]byte, error) {
	return []byte(s.String()), nil
}

// UnmarshalText implements encoding.TextUnmarshaler.
func (s *Status) UnmarshalText(text []byte) error {
	v, err := ParseStatus(string(text))
	if err != nil {
		return err
	}
	*s = v
	return nil
}

func classify(code int) Status {
	switch {
	case code >= 200 && code < 300:
		return StatusUp
	case code == 429 || code == 503:
		return StatusDegraded
	default:
		return StatusDown
	}
}

// slow reports whether err means the target did not answer in time.
func slow(err error) bool {
	return err == context.DeadlineExceeded
}
