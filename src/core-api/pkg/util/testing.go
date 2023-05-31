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

package util

import (
	"bytes"
	"errors"
	"net/http"
	"net/http/httptest"

	"github.com/gin-gonic/gin"
)

// TestingContent ...
var TestingContent = []byte("Hello, World!")

// NewRequestResponse ...
func NewRequestResponse() (*http.Request, *httptest.ResponseRecorder) {
	r := httptest.NewRequest(http.MethodPost, "/", bytes.NewReader(TestingContent))
	w := httptest.NewRecorder()
	return r, w
}

// NewRequestResponseWithContent ...
func NewRequestResponseWithContent(content []byte) (*http.Request, *httptest.ResponseRecorder) {
	r := httptest.NewRequest(http.MethodPost, "/", bytes.NewReader(content))
	w := httptest.NewRecorder()
	return r, w
}

// TestingEmptyContent ...
var TestingEmptyContent = []byte("")

// NewRequestEmptyResponse ...
func NewRequestEmptyResponse() (*http.Request, *httptest.ResponseRecorder) {
	return NewRequestResponseWithContent(TestingEmptyContent)
}

// error
type errReader int

// Read ...
func (errReader) Read(p []byte) (n int, err error) {
	return 0, errors.New("test error")
}

// NewRequestErrorResponse ...
func NewRequestErrorResponse() (*http.Request, *httptest.ResponseRecorder) {
	r := httptest.NewRequest(http.MethodPost, "/", errReader(0))
	w := httptest.NewRecorder()
	return r, w
}

// NewTestRouter ...
func NewTestRouter(r *gin.Engine) {
	r.GET("/ping", func(c *gin.Context) {
		c.String(200, "pong")
	})
}
