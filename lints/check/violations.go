package beautifullintcheck

import "fmt"

func unchecked() error {
	return fmt.Errorf("disk full")
}

func ignored() {
	_ = unchecked()
}

func BadName() error {
	return fmt.Errorf("Bad name.")
}
