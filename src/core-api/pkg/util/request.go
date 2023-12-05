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
	"io"
	"net/http"

	"github.com/gin-gonic/gin"
)

// RequestIDKey ...
const RequestIDKey = "request_id"

// InstanceIDKey ...
const InstanceIDKey = "instance_id"

const BkGatewayJWTIssuerKey = "bk_gateway_jwt_issuer"

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

// SetRequestID set the request id to context
func SetRequestID(c *gin.Context, requestID string) {
	c.Set(RequestIDKey, requestID)
}

// SetBkGatewayIssuer set the bk gateway issuer to context
func SetBkGatewayIssuer(c *gin.Context, issuer string) {
	c.Set(BkGatewayJWTIssuerKey, issuer)
}

// GetBkGatewayIssuer get the bk gateway issuer from context
func GetBkGatewayIssuer(c *gin.Context) string {
	return c.GetString(BkGatewayJWTIssuerKey)
}

// GetInstanceID get the request id from context
func GetInstanceID(c *gin.Context) string {
	return c.GetString(InstanceIDKey)
}

// SetInstanceID set the request id to context
func SetInstanceID(c *gin.Context, instanceID string) {
	c.Set(InstanceIDKey, instanceID)
}
