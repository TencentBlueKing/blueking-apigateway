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
	"fmt"
	"time"

	"github.com/gin-gonic/gin"

	"mcp_proxy/pkg/cacheimpls"
	"mcp_proxy/pkg/util"
)

// MCPServerPermissionMiddleware ...
func MCPServerPermissionMiddleware() func(c *gin.Context) {
	return func(c *gin.Context) {
		// 获取mcp server id and appCode
		id := util.GetMCPServerID(c)
		appCode := util.GetBkAppCode(c)
		permission, err := cacheimpls.GetMCPServerPermission(c, appCode, id)
		if err != nil {
			util.BadRequestErrorJSONResponse(c, err.Error())
			c.Abort()
			return
		}

		// 判断权限是否有效
		if !permission.Expires.After(time.Now()) {
			util.ForbiddenJSONResponse(c,
				fmt.Sprintf("appCode[%s] to call mcp server[%s] permission is expired", appCode,
					c.Param("name")))
			c.Abort()
			return
		}
		c.Next()
	}
}
