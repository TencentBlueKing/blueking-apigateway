package server

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"

	"operator/pkg/config"
	"operator/pkg/constant"
)

func TestPprofRequiresBasicAuth(t *testing.T) {
	gin.SetMode(gin.TestMode)

	s := NewServer(nil, nil, nil, nil)
	cfg := &config.Config{
		HttpServer: config.HttpServer{
			AuthPassword: "secret",
		},
	}
	err := s.Run(context.Background(), cfg)
	if err != nil {
		t.Fatalf("Run() error = %v", err)
	}

	w := httptest.NewRecorder()
	req := httptest.NewRequest(http.MethodGet, "/debug/pprof/", nil)
	s.mux.ServeHTTP(w, req)
	if w.Code != http.StatusUnauthorized {
		t.Fatalf("GET /debug/pprof/ without auth status = %d, want %d", w.Code, http.StatusUnauthorized)
	}

	w = httptest.NewRecorder()
	req = httptest.NewRequest(http.MethodGet, "/debug/pprof/", nil)
	req.SetBasicAuth(constant.ApiAuthAccount, "secret")
	s.mux.ServeHTTP(w, req)
	if w.Code != http.StatusOK {
		t.Fatalf("GET /debug/pprof/ with auth status = %d, want %d", w.Code, http.StatusOK)
	}
}
