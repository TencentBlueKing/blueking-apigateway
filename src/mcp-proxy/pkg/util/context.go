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
	"context"
	"time"

	"github.com/gin-gonic/gin"

	"mcp_proxy/pkg/constant"
)

// SetBkUserName ...
func SetBkUserName(c *gin.Context, userName string) {
	c.Set(string(constant.BKUserName), userName)
	if c.Request != nil {
		c.Request = c.Request.WithContext(context.WithValue(c.Request.Context(), constant.BKUserName, userName))
	}
}

func SetBkAppCode(c *gin.Context, appCode string) {
	c.Set(string(constant.BkAPPCode), appCode)
	if c.Request != nil {
		c.Request = c.Request.WithContext(context.WithValue(c.Request.Context(), constant.BkAPPCode, appCode))
	}
}

func GetBkAppCode(c *gin.Context) string {
	appCode, ok := c.Get(string(constant.BkAPPCode))
	if !ok {
		return ""
	}
	return appCode.(string)
}

func SetInnerJwtToken(c *gin.Context, jwtToken string) {
	c.Set(string(constant.BkGatewayInnerJWT), jwtToken)
	if c.Request != nil {
		c.Request = c.Request.WithContext(
			context.WithValue(c.Request.Context(), constant.BkGatewayInnerJWT, jwtToken))
	}
}

func SetMcpServerID(c *gin.Context, mcpServerID int) {
	c.Set(string(constant.McpServerID), mcpServerID)
	if c.Request != nil {
		c.Request = c.Request.WithContext(context.WithValue(c.Request.Context(), constant.McpServerID, mcpServerID))
	}
}

func GetMcpServerID(c *gin.Context) int {
	mcpServerID, ok := c.Get(string(constant.McpServerID))
	if !ok {
		return 0
	}
	return mcpServerID.(int)
}

func GetInnerJwtTokenFromContext(ctx context.Context) string {
	jwtToken := ctx.Value(constant.BkGatewayInnerJWT)
	if innerJwt, ok := jwtToken.(string); ok {
		return innerJwt
	}
	return ""
}

func SetBKAPITimeout(c *gin.Context, timeout int) {
	c.Request = c.Request.WithContext(context.WithValue(c.Request.Context(), constant.BKAPITimeoutKey, timeout))
}

func GetBKAPITimeout(ctx context.Context) time.Duration {
	timeout, ok := ctx.Value(constant.BKAPITimeoutKey).(int)
	if !ok {
		// default timeout is 1 minute
		return time.Minute
	}
	return time.Duration(timeout) * time.Second
}
