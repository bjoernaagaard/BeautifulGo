package fleet

import (
	"context"
	"crypto/rand"
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"time"
)

type requestIDKey struct{}

// NewServer returns an HTTP server for the API of m on addr.
func NewServer(addr string, m *Monitor) *http.Server {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /status", m.handleStatus)
	mux.HandleFunc("GET /summary", m.handleSummary)
	mux.HandleFunc("POST /targets", withRequestID(m.handleAdd))
	mux.HandleFunc("POST /check", withRequestID(m.handleCheck))
	return &http.Server{
		Addr:              addr,
		Handler:           http.NewCrossOriginProtection().Handler(mux),
		ReadHeaderTimeout: 5 * time.Second,
		WriteTimeout:      5 * time.Second,
	}
}

func withRequestID(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		id := r.Header.Get("X-Request-ID")
		if id == "" {
			id = rand.Text()
		}
		next(w, r.WithContext(context.WithValue(r.Context(), requestIDKey{}, id)))
	}
}

func (m *Monitor) handleStatus(w http.ResponseWriter, r *http.Request) {
	id := r.Context().Value(requestIDKey{}).(string)
	m.logger.DebugContext(r.Context(), "status requested", "request_id", id)
	m.writeJSON(r.Context(), w, http.StatusOK, m.Results())
}

func (m *Monitor) handleSummary(w http.ResponseWriter, r *http.Request) {
	m.writeJSON(r.Context(), w, http.StatusOK, m.Summary())
}

func (m *Monitor) handleAdd(w http.ResponseWriter, r *http.Request) {
	body, err := io.ReadAll(r.Body)
	if err != nil {
		http.Error(w, "read body", http.StatusBadRequest)
		return
	}
	var t Target
	if err := json.Unmarshal(body, &t); err != nil {
		http.Error(w, "decode target", http.StatusBadRequest)
		return
	}
	if ve, ok := errors.AsType[*ValidationError](m.Add(t)); ok {
		http.Error(w, ve.Reason, http.StatusUnprocessableEntity)
		return
	}
	w.WriteHeader(http.StatusCreated)
}

func (m *Monitor) handleCheck(w http.ResponseWriter, r *http.Request) {
	m.CheckAll(r.Context())
	m.writeJSON(r.Context(), w, http.StatusOK, m.Summary())
}

func (m *Monitor) writeJSON(ctx context.Context, w http.ResponseWriter, code int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	if err := json.NewEncoder(w).Encode(v); err != nil {
		m.logger.WarnContext(ctx, "write response", "error", err)
	}
}
