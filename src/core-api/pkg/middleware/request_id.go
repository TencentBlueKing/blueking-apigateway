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
	"github.com/gin-gonic/gin"

	"core/pkg/util"
)

// RequestIDHeaderKey is a key to set the request id in header
const (
	RequestIDHeaderKey = "X-Request-Id"
)

// RequestID add the request_id for each api request
func RequestID() gin.HandlerFunc {
	return func(c *gin.Context) {
		requestID := c.GetHeader(RequestIDHeaderKey)
		if requestID == "" {
			requestID = util.GenUUID4()
		}
		util.SetRequestID(c, requestID)
		c.Writer.Header().Set(RequestIDHeaderKey, requestID)

		c.Next()
	}
}
