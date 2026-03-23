/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
 * Licensed under the MIT License (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 *
 *     http://opensource.org/licenses/MIT
 *
 * Unless required by applicable law or agreed to in writing, software distributed under
 * the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * We undertake not to change the open source license (MIT license) applicable
 * to the current version of the project delivered to anyone in the future.
 */

// Package sentry is the sentry for the whole project
package sentry

import (
	"errors"
	"fmt"
	"net/http"
	"runtime/debug"
	"time"

	sentry "github.com/getsentry/sentry-go"
	"github.com/gin-gonic/gin"

	"mcp_proxy/pkg/config"
)

var s sentryState

// sentryState holds the runtime state of sentry integration.
type sentryState struct {
	enabled bool
}

// Init initializes the sentry SDK (sentry-go only, raven-go removed).
func Init(cfg config.Sentry) error {
	if cfg.DSN != "" {
		err := sentry.Init(sentry.ClientOptions{
			Dsn:              cfg.DSN,
			AttachStacktrace: true,
		})
		if err != nil {
			return fmt.Errorf("init sentry fail: %w", err)
		}
		s.enabled = true
	}
	return nil
}

// Enabled returns whether sentry is enabled.
func Enabled() bool {
	return s.enabled
}

// Flush waits until the underlying transport sends any buffered events to
// the Sentry server, blocking for at most the given timeout.
// It should be called before the process exits.
func Flush(timeout time.Duration) {
	if s.enabled {
		sentry.Flush(timeout)
	}
}

// ReportToSentry reports an error event to sentry with tags, extra data and fingerprint.
func ReportToSentry(message string, tags map[string]string, extra map[string]interface{}) {
	if !s.enabled {
		return
	}

	ev := sentry.NewEvent()
	ev.Message = message
	ev.Level = sentry.LevelError
	ev.Timestamp = time.Now()

	if len(tags) > 0 {
		ev.Tags = tags
	}
	if len(extra) > 0 {
		ev.Extra = extra
	}

	sentry.CaptureEvent(ev)
}

// Recovery returns a Gin middleware that recovers from panics and reports them to Sentry.
// This replaces the old raven-go based gin-gonic/contrib/sentry.Recovery.
func Recovery() gin.HandlerFunc {
	return func(c *gin.Context) {
		defer func() {
			if rval := recover(); rval != nil {
				// Build a human-readable message
				var err error
				switch v := rval.(type) {
				case error:
					err = v
				case string:
					err = errors.New(v)
				default:
					err = fmt.Errorf("%v", v)
				}

				// Capture to Sentry with request context
				if hub := sentry.GetHubFromContext(c.Request.Context()); hub != nil {
					hub.RecoverWithContext(c.Request.Context(), rval)
				} else {
					hub = sentry.CurrentHub().Clone()
					hub.Scope().SetRequest(c.Request)
					hub.Scope().SetTag("endpoint", c.Request.RequestURI)
					hub.Scope().SetExtra("stacktrace", string(debug.Stack()))
					hub.CaptureException(err)
				}

				c.AbortWithStatus(http.StatusInternalServerError)
			}
		}()

		// Clone hub per request so scopes don't leak between requests
		hub := sentry.CurrentHub().Clone()
		hub.Scope().SetRequest(c.Request)
		c.Request = c.Request.WithContext(sentry.SetHubOnContext(c.Request.Context(), hub))

		c.Next()
	}
}
