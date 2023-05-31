/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
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

	"core/pkg/util"
)

func TestRequestID(t *testing.T) {
	// request with no request_id
	req, _ := http.NewRequest("GET", "/ping", nil)
	w := httptest.NewRecorder()

	r := gin.Default()

	r.Use(RequestID())
	r.GET("/ping", func(c *gin.Context) {
		requestID := util.GetRequestID(c)
		assert.NotNil(t, requestID)
		assert.Len(t, requestID, 32)
		c.String(200, "pong")
	})

	r.ServeHTTP(w, req)

	// request with X-Request-Id
	req2, _ := http.NewRequest("GET", "/ping2", nil)
	originRID := "11111111111111111111111111111111"
	req2.Header.Set(RequestIDHeaderKey, originRID)
	w2 := httptest.NewRecorder()
	r.GET("/ping2", func(c *gin.Context) {
		requestID := util.GetRequestID(c)
		assert.NotNil(t, requestID)
		assert.Equal(t, originRID, requestID)
		c.String(200, "pong")
	})

	r.ServeHTTP(w2, req2)
}
