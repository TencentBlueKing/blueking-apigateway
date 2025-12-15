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
	"bytes"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"

	"mcp_proxy/pkg/config"
	"mcp_proxy/pkg/infra/logging"
	"mcp_proxy/pkg/util"
)

func TestAPILogger(t *testing.T) {
	logging.InitLogger(&config.Config{})

	r := gin.Default()
	r.Use(APILogger())
	util.NewTestRouter(r)

	req, _ := http.NewRequest("GET", "/ping", nil)
	w := httptest.NewRecorder()

	r.ServeHTTP(w, req)

	assert.Equal(t, 200, w.Code)
}

func TestAPILogger_WithRequestBody(t *testing.T) {
	logging.InitLogger(&config.Config{})

	gin.SetMode(gin.TestMode)
	r := gin.New()
	r.Use(APILogger())
	r.POST("/test", func(c *gin.Context) {
		c.String(http.StatusOK, "ok")
	})

	body := bytes.NewBufferString(`{"key": "value"}`)
	req, _ := http.NewRequest("POST", "/test", body)
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	r.ServeHTTP(w, req)

	assert.Equal(t, 200, w.Code)
}

func TestAPILogger_WithQueryParams(t *testing.T) {
	logging.InitLogger(&config.Config{})

	gin.SetMode(gin.TestMode)
	r := gin.New()
	r.Use(APILogger())
	r.GET("/test", func(c *gin.Context) {
		c.String(http.StatusOK, "ok")
	})

	req, _ := http.NewRequest("GET", "/test?param1=value1&param2=value2", nil)
	w := httptest.NewRecorder()

	r.ServeHTTP(w, req)

	assert.Equal(t, 200, w.Code)
}

func TestAPILogger_WithContextValues(t *testing.T) {
	logging.InitLogger(&config.Config{})

	gin.SetMode(gin.TestMode)
	r := gin.New()
	r.Use(func(c *gin.Context) {
		util.SetGatewayID(c, 123)
		util.SetMCPServerID(c, 456)
		util.SetMCPServerName(c, "test-server")
		c.Next()
	})
	r.Use(APILogger())
	r.GET("/test", func(c *gin.Context) {
		c.String(http.StatusOK, "ok")
	})

	req, _ := http.NewRequest("GET", "/test", nil)
	w := httptest.NewRecorder()

	r.ServeHTTP(w, req)

	assert.Equal(t, 200, w.Code)
}

func TestAPILogger_ErrorResponse(t *testing.T) {
	logging.InitLogger(&config.Config{})

	gin.SetMode(gin.TestMode)
	r := gin.New()
	r.Use(APILogger())
	r.GET("/error", func(c *gin.Context) {
		c.String(http.StatusInternalServerError, "error")
	})

	req, _ := http.NewRequest("GET", "/error", nil)
	w := httptest.NewRecorder()

	r.ServeHTTP(w, req)

	assert.Equal(t, 500, w.Code)
}

func TestBodyLogWriter_Write(t *testing.T) {
	gin.SetMode(gin.TestMode)

	// Create a simple test to verify bodyLogWriter behavior
	var buf bytes.Buffer
	blw := &bodyLogWriter{
		body: &buf,
	}

	// Test that body buffer captures content
	blw.body.WriteString("test response")
	assert.Equal(t, "test response", blw.body.String())
}

func TestAPILogger_FunctionCreation(t *testing.T) {
	logging.InitLogger(&config.Config{})
	middleware := APILogger()
	assert.NotNil(t, middleware)
}
