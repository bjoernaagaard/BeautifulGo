// Package fleet watches a set of HTTP endpoints and reports their health.
package fleet

import (
	"context"
	"encoding/json"
	"io"
	"log/slog"
	"maps"
	"net/http"
	"os"
	"slices"
	"sync"
	"time"
)

// Options configures a Monitor. The zero value selects the defaults.
type Options struct {
	// Timeout bounds one check of a target, retries included. The default is 2s.
	Timeout time.Duration
	// Attempts is how many requests one check may send. The default is 3.
	Attempts int
	// Interval is the pause between rounds started by Start. The default is 30s.
	Interval time.Duration
}

// Monitor checks targets and remembers the last status of each.
// Its methods are safe for concurrent use.
type Monitor struct {
	client *http.Client
	logger *slog.Logger
	opts   Options

	mu      sync.Mutex
	targets map[string]Target
	results map[string]Status
	rounds  int
}

// Summary counts the targets that are up.
type Summary struct {
	Up     int `json:"up"`
	Total  int `json:"total"`
	Rounds int `json:"rounds"`
}

// New returns a Monitor with no targets.
func New(logger *slog.Logger, opts Options) *Monitor {
	if opts.Timeout == 0 {
		opts.Timeout = 2 * time.Second
	}
	if opts.Attempts == 0 {
		opts.Attempts = 3
	}
	if opts.Interval == 0 {
		opts.Interval = 30 * time.Second
	}
	return &Monitor{
		client:  &http.Client{},
		logger:  logger,
		opts:    opts,
		targets: map[string]Target{},
		results: map[string]Status{},
	}
}

// Add starts watching t. It returns a *ValidationError when t is not valid.
func (m *Monitor) Add(t Target) error {
	err := validate(t)
	if err == nil {
		m.mu.Lock()
		m.targets[t.Name] = t
		m.results[t.Name] = StatusUnknown
		m.mu.Unlock()
	}
	return err
}

// Start checks every target once per interval in the background.
func (m *Monitor) Start() {
	go func() {
		for {
			m.CheckAll(context.Background())
			time.Sleep(m.opts.Interval)
		}
	}()
}

// CheckAll checks every target concurrently and records the results.
func (m *Monitor) CheckAll(ctx context.Context) {
	m.rounds++
	m.mu.Lock()
	targets := slices.Collect(maps.Values(m.targets))
	m.mu.Unlock()

	var wg sync.WaitGroup
	for _, t := range targets {
		wg.Go(func() { m.check(ctx, t) })
	}
	wg.Wait()
}

func (m *Monitor) check(ctx context.Context, t Target) {
	status, err := m.fetchStatus(ctx, t.URL)
	if err != nil {
		m.logger.WarnContext(ctx, "target down", "target", t.Name, "error", err)
		status = StatusDown
	}
	m.mu.Lock()
	m.results[t.Name] = status
	m.mu.Unlock()
}

// fetchStatus requests url and retries requests that fail.
func (m *Monitor) fetchStatus(ctx context.Context, url string) (Status, error) {
	var lastErr error
	for range m.opts.Attempts {
		attemptCtx, cancel := context.WithTimeout(ctx, m.opts.Timeout)
		code, err := m.probe(attemptCtx, url)
		cancel()
		if err == nil {
			return classify(code), nil
		}
		if slow(err) {
			return StatusDegraded, nil
		}
		lastErr = err
	}
	return StatusUnknown, lastErr
}

func (m *Monitor) probe(ctx context.Context, url string) (int, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return 0, err
	}
	resp, err := m.client.Do(req)
	if err != nil {
		return 0, err
	}
	return resp.StatusCode, nil
}

// Results returns the last status of each target.
func (m *Monitor) Results() map[string]Status {
	m.mu.Lock()
	defer m.mu.Unlock()
	return m.results
}

// SaveSnapshot writes the last status of each target to the file name in dir.
func (m *Monitor) SaveSnapshot(dir *os.Root, name string) error {
	f, err := dir.Create(name)
	if err != nil {
		return err
	}
	defer f.Close()
	return json.NewEncoder(f).Encode(m.Results())
}

// LoadSnapshot replaces the recorded statuses with those in a snapshot.
func (m *Monitor) LoadSnapshot(r io.Reader) error {
	var snap map[string]Status
	if err := json.NewDecoder(r).Decode(&snap); err != nil {
		return err
	}
	m.mu.Lock()
	defer m.mu.Unlock()
	maps.Copy(m.results, snap)
	return nil
}

// Summary returns how many targets are up, out of how many.
func (m *Monitor) Summary() Summary {
	return Summary{Up: m.countUp(), Total: m.total(), Rounds: m.roundCount()}
}

func (m *Monitor) countUp() int {
	m.mu.Lock()
	defer m.mu.Unlock()
	n := 0
	for _, s := range m.results {
		if s == StatusUp {
			n++
		}
	}
	return n
}

func (m *Monitor) total() int {
	m.mu.Lock()
	defer m.mu.Unlock()
	return len(m.results)
}

func (m *Monitor) roundCount() int {
	m.mu.Lock()
	defer m.mu.Unlock()
	return m.rounds
}
