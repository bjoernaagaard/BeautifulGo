package fleet

import "strings"

// Target is one endpoint to watch.
type Target struct {
	Name string `json:"name"`
	URL  string `json:"url"`
}

// ValidationError reports a target that cannot be watched.
type ValidationError struct {
	Name   string
	Reason string
}

func (e *ValidationError) Error() string {
	return "target " + e.Name + ": " + e.Reason
}

func validate(t Target) *ValidationError {
	switch {
	case t.Name == "":
		return &ValidationError{Name: "(unnamed)", Reason: "name is empty"}
	case !strings.HasPrefix(t.URL, "http://") && !strings.HasPrefix(t.URL, "https://"):
		return &ValidationError{Name: t.Name, Reason: "url must use http or https"}
	}
	return nil
}
