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
	"context"
	"core/pkg/cacheimpls"
	"core/pkg/config"
	"core/pkg/database"
	"core/pkg/database/dao"
	"core/pkg/logging"
	"core/pkg/util"
	"io"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/agiledragon/gomonkey/v2"
	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
)

const testPublicKey = `
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAnzyis1ZjfNB0bBgKFMSv
vkTtwlvBsaJq7S5wA+kzeVOVpVWwkWdVha4s38XM/pa/yr47av7+z3VTmvDRyAHc
aT92whREFpLv9cj5lTeJSibyr/Mrm/YtjCZVWgaOYIhwrXwKLqPr/11inWsAkfIy
tvHWTxZYEcXLgAXFuUuaS3uF9gEiNQwzGTU1v0FqkqTBr4B8nW3HCN47XUu0t8Y0
e+lf4s4OxQawWD79J9/5d3Ry0vbV3Am1FtGJiJvOwRsIfVChDpYStTcHTCMqtvWb
V6L11BWkpzGXSW4Hv43qa+GSYOD2QU68Mb59oSk2OB+BtOLpJofmbGEGgvmwyCI9
MwIDAQAB
-----END PUBLIC KEY-----
`

const testJwtToken = "eyJhbGciOiJSUzUxMiIsImtpZCI6InRlc3QiLCJ0eXAiOiJKV1QiLCJpYXQiOjE1NjA0ODMxMTZ9.eyJpc3MiOiJBUElHVyIsImFwcCI6eyJhcHBfY29kZSI6ImFwaWd3LXRlc3QiLCJ2ZXJpZmllZCI6dHJ1ZX0sInVzZXIiOnsidXNlcm5hbWUiOiJhZG1pbiJ9LCJleHAiOjE4NzI3NjgyNzksIm5iZiI6MTU2MDQ4MzExNn0.Me5NMNx6-Hqc5gfqxhWT0rrROrr-d-W-nvnCtptEinqwoRTQ-8KB6ZNro8Xr12k8hLgcfgRa9GjN5XT5XNXdaj2ThuIU7VdcdpXl1ynxKDAOhd5iPDds0O2ecC-jE_l8wWBGrcUUIeiNBNaUv6v6qnQMDPJbqxjU28gf7GA7stR8nsjpux_LL2MyOY27-e-_9bbh_eE1DudjkBc4vj78pgSSUJ-7bXT5-MpLFgsdrGtof2t0k2pP9bRNvGlH1HuK087PCQFRCmHb414OJ8CKyBYhzKXtG2ibPfsBFjaoU0Fq_tiv_eByAB1ACObIddRMq43JCs4vMqGcsn3Em5a-Lg"

func TestBkGatewayJWTAuthMiddleware(t *testing.T) {
	logging.InitLogger(&config.Config{})

	database.DefaultDBClient = database.NewDBClient(&config.Database{})

	r := gin.Default()
	r.Use(BkGatewayJWTAuthMiddlewareV1())
	util.NewTestRouter(r)

	req, _ := http.NewRequest("GET", "/ping", nil)
	w := httptest.NewRecorder()

	r.ServeHTTP(w, req)

	assert.Equal(t, http.StatusUnauthorized, w.Code)

	// request with invalid X-Bkapi-Jwt
	patches := gomonkey.NewPatches()

	patches.ApplyFunc(
		cacheimpls.GetGatewayByName,
		func(ctx context.Context, name string) (gateway dao.Gateway, err error) {
			return dao.Gateway{ID: 1}, nil
		},
	)
	patches.ApplyFunc(
		cacheimpls.GetJWTPublicKey,
		func(ctx context.Context, gatewayID int64) (string, error) {
			return testPublicKey, nil
		},
	)

	req2, _ := http.NewRequest("GET", "/ping", nil)
	req2.Header.Set(BkGatewayJWTHeaderKey, "test")
	w2 := httptest.NewRecorder()
	r.ServeHTTP(w2, req2)
	assert.Equal(t, http.StatusUnauthorized, w.Code)
	defer w2.Result().Body.Close()
	response, err := io.ReadAll(w2.Result().Body)
	assert.NoError(t, err)

	assert.Contains(t, string(response), "token contains an invalid number of segment")

	// request with valid X-Bkapi-Jwt
	patches.ApplyFunc(
		cacheimpls.GetGatewayByName,
		func(ctx context.Context, name string) (gateway dao.Gateway, err error) {
			return dao.Gateway{ID: 1}, nil
		},
	)
	patches.ApplyFunc(
		cacheimpls.GetJWTPublicKey,
		func(ctx context.Context, gatewayID int64) (string, error) {
			return testPublicKey, nil
		},
	)

	req3, _ := http.NewRequest("GET", "/ping", nil)
	req3.Header.Set(BkGatewayJWTHeaderKey, testJwtToken)
	w3 := httptest.NewRecorder()
	r.ServeHTTP(w3, req3)
	defer w3.Result().Body.Close()
	response, err = io.ReadAll(w3.Result().Body)
	assert.NoError(t, err)
	assert.Equal(t, http.StatusOK, w3.Code)
	assert.Contains(t, string(response), "pong")
}
