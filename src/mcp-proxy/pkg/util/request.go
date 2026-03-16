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

package util

import (
	"bytes"
	"context"
	"errors"
	"io"
	"net/http"

	"github.com/gin-gonic/gin"

	"mcp_proxy/pkg/constant"
)

// RequestIDKey ...
const RequestIDKey = "request_id"

// InstanceIDKey ...
const InstanceIDKey = "instance_id"

// ErrNilRequestBody ...
var ErrNilRequestBody = errors.New("request Body is nil")

// ReadRequestBody will return the body in []byte, without change the origin body
func ReadRequestBody(r *http.Request) ([]byte, error) {
	if r.Body == nil {
		return nil, ErrNilRequestBody
	}

	body, err := io.ReadAll(r.Body)
	r.Body = io.NopCloser(bytes.NewReader(body))
	return body, err
}

// GetRequestID return the request id from context
func GetRequestID(c *gin.Context) string {
	return c.GetString(RequestIDKey)
}

// GetRequestIDFromContext retrieves the request ID from the context.
func GetRequestIDFromContext(ctx context.Context) string {
	if requestID, ok := ctx.Value(constant.RequestID).(string); ok {
		return requestID
	}
	// Fallback: also check bare string key for backward compatibility with gin.Context.Set
	if requestID, ok := ctx.Value(RequestIDKey).(string); ok {
		return requestID
	}
	return ""
}

// SetRequestID set the request id to context
// nolint:staticcheck
func SetRequestID(c *gin.Context, requestID string) {
	c.Set(RequestIDKey, requestID)
	if c.Request != nil {
		c.Request = c.Request.WithContext(
			context.WithValue(c.Request.Context(), constant.RequestID, requestID))
	}
}

// XRequestIDKey is the context key for the full-chain X-Request-ID
const XRequestIDKey = "x_request_id"

// GetXRequestID return the x_request_id from gin context
func GetXRequestID(c *gin.Context) string {
	return c.GetString(XRequestIDKey)
}

// GetXRequestIDFromContext retrieves the X-Request-ID from the context
func GetXRequestIDFromContext(ctx context.Context) string {
	if xRequestID, ok := ctx.Value(constant.XRequestID).(string); ok {
		return xRequestID
	}
	return ""
}

// SetXRequestID set the x_request_id to context
// nolint:staticcheck
func SetXRequestID(c *gin.Context, xRequestID string) {
	c.Set(XRequestIDKey, xRequestID)
	if c.Request != nil {
		c.Request = c.Request.WithContext(
			context.WithValue(c.Request.Context(), constant.XRequestID, xRequestID))
	}
}

// GetInstanceID get the request id from context
func GetInstanceID(c *gin.Context) string {
	return c.GetString(InstanceIDKey)
}

// SetInstanceID set the request id to context
func SetInstanceID(c *gin.Context, instanceID string) {
	c.Set(InstanceIDKey, instanceID)
}
