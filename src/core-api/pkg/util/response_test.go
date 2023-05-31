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

package util_test

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"net/http/httptest"

	"core/pkg/util"

	"github.com/gin-gonic/gin"
	. "github.com/onsi/ginkgo/v2"
	"github.com/stretchr/testify/assert"
)

func readResponse(w *httptest.ResponseRecorder) map[string]interface{} {
	var got map[string]interface{}
	err := json.Unmarshal(w.Body.Bytes(), &got)
	assert.NoError(GinkgoT(), err, fmt.Sprintf("the response is: %s", w.Body.String()))
	return got
}

var _ = Describe("Response", func() {
	var c *gin.Context
	// var r *gin.Engine
	var w *httptest.ResponseRecorder
	BeforeEach(func() {
		w = httptest.NewRecorder()
		gin.SetMode(gin.ReleaseMode)
		// gin.DefaultWriter = ioutil.Discard
		c, _ = gin.CreateTestContext(w)
		c.Request, _ = http.NewRequest("POST", "/api/v1/?force=1&debug=1", new(bytes.Buffer))
	})

	// It("BaseJSONResponse", func() {
	// 	util.BaseJSONResponse(c, 200, 10000, "ok", nil)

	// 	assert.Equal(GinkgoT(), 200, w.Code)

	// 	got := readResponse(w)
	// 	assert.Equal(GinkgoT(), 10000, got.Code)
	// 	assert.Equal(GinkgoT(), "ok", got.Message)
	// })
	It("SuccessJSONResponse", func() {
		util.SuccessJSONResponse(c, "ok")
		assert.Equal(GinkgoT(), 200, c.Writer.Status())

		got := readResponse(w)
		assert.Equal(GinkgoT(), "ok", got["data"])
	})

	It("BaseErrorJSONResponse", func() {
		errorCode := "ERROR1"
		util.BaseErrorJSONResponse(c, errorCode, "error", http.StatusBadRequest)
		assert.Equal(GinkgoT(), http.StatusBadRequest, c.Writer.Status())

		got := readResponse(w)
		assert.Equal(GinkgoT(), errorCode, got["error"].(map[string]interface{})["code"])
		assert.Equal(GinkgoT(), "error", got["error"].(map[string]interface{})["message"])
	})

	It("BadRequestErrorJSONResponse", func() {
		util.BadRequestErrorJSONResponse(c, "error")
		assert.Equal(GinkgoT(), 400, c.Writer.Status())

		got := readResponse(w)
		assert.Equal(GinkgoT(), util.BadRequestError, got["error"].(map[string]interface{})["code"])
		assert.Equal(GinkgoT(), "error", got["error"].(map[string]interface{})["message"])
	})

	It("SystemErrorJSONResponse", func() {
		util.SystemErrorJSONResponse(c, errors.New("anError"))
		assert.Equal(GinkgoT(), 500, c.Writer.Status())

		got := readResponse(w)
		assert.Equal(GinkgoT(), util.SystemError, got["error"].(map[string]interface{})["code"])
		assert.Contains(GinkgoT(), got["error"].(map[string]interface{})["message"], "system error")
	})
})
