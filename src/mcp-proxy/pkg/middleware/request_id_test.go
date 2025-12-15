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

package middleware

import (
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"

	"mcp_proxy/pkg/constant"
	"mcp_proxy/pkg/util"
)

func TestRequestID_WithExistingRequestID(t *testing.T) {
	gin.SetMode(gin.TestMode)

	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

	existingRequestID := "existing-request-id-12345"
	c.Request.Header.Set(constant.BkGatewayRequestIDKey, existingRequestID)

	middleware := RequestID()
	middleware(c)

	// Should use the existing request ID
	requestID := util.GetRequestIDFromContext(c.Request.Context())
	assert.Equal(t, existingRequestID, requestID)
}

func TestRequestID_GeneratesNewRequestID(t *testing.T) {
	gin.SetMode(gin.TestMode)

	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

	// No request ID header set

	middleware := RequestID()
	middleware(c)

	// Should generate a new request ID
	requestID := util.GetRequestIDFromContext(c.Request.Context())
	assert.NotEmpty(t, requestID)
	// UUID4 hex format check (32 hex characters without dashes)
	assert.Len(t, requestID, 32)
}

func TestRequestID_MultipleCalls(t *testing.T) {
	gin.SetMode(gin.TestMode)

	// Test that multiple requests get different request IDs
	requestIDs := make(map[string]bool)

	for i := 0; i < 10; i++ {
		w := httptest.NewRecorder()
		c, _ := gin.CreateTestContext(w)
		c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

		middleware := RequestID()
		middleware(c)

		requestID := util.GetRequestIDFromContext(c.Request.Context())
		assert.NotEmpty(t, requestID)

		// Ensure uniqueness
		assert.False(t, requestIDs[requestID], "Request ID should be unique")
		requestIDs[requestID] = true
	}
}
