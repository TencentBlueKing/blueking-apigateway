package client

import (
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync/atomic"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	retry "gopkg.in/h2non/gentleman-retry.v2"
	"gopkg.in/h2non/gentleman.v2"
)

func TestGetReleaseVersionDoesNotOverwriteGlobalRetryEvaluator(t *testing.T) {
	var globalEvaluatorCalls atomic.Int32
	originalEvaluator := retry.Evaluator
	retry.Evaluator = func(err error, res *http.Response, req *http.Request) error {
		globalEvaluatorCalls.Add(1)
		return nil
	}
	t.Cleanup(func() {
		retry.Evaluator = originalEvaluator
	})

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/api/gateway/stage/__apigw_version", r.URL.Path)
		_, _ = w.Write([]byte(`{"publish_id":1,"start_time":"2025-10-22 15:24:57+0800"}`))
	}))
	defer server.Close()

	apisixClient := newTestApisixClient(server.URL, 1, time.Nanosecond)
	resp, err := apisixClient.GetReleaseVersion("gateway", "stage", "1")
	require.NoError(t, err)
	require.NotNil(t, resp)
	assert.Equal(t, int64(1), resp.PublishID)

	_ = retry.Evaluator(
		nil,
		&http.Response{StatusCode: http.StatusOK, Body: io.NopCloser(strings.NewReader(""))},
		httptest.NewRequest(http.MethodGet, "/", nil),
	)
	assert.Equal(t, int32(1), globalEvaluatorCalls.Load())
}

func TestGetReleaseVersionRetriesUntilExpectedPublishID(t *testing.T) {
	var attempts atomic.Int32
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		publishID := attempts.Add(1)
		_, _ = w.Write([]byte(fmt.Sprintf(`{"publish_id":%d}`, publishID)))
	}))
	defer server.Close()

	apisixClient := newTestApisixClient(server.URL, 1, time.Nanosecond)
	resp, err := apisixClient.GetReleaseVersion("gateway", "stage", "2")
	require.NoError(t, err)
	require.NotNil(t, resp)
	assert.Equal(t, int64(2), resp.PublishID)
	assert.Equal(t, int32(2), attempts.Load())
}

func newTestApisixClient(baseURL string, retryCount int, retryInterval time.Duration) *ApisixClient {
	cli := gentleman.New()
	cli.URL(baseURL)

	return &ApisixClient{
		baseClient:           baseClient{client: cli},
		versionProbeCount:    retryCount,
		versionProbeInterval: retryInterval,
	}
}
