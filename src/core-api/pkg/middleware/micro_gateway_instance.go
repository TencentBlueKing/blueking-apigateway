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

	"github.com/gin-gonic/gin"

	"core/pkg/cacheimpls"
	"core/pkg/util"
)

// MicroGatewayInstanceMiddleware is the middleware to verify the micro gateway instance by instance id and instance secret
func MicroGatewayInstanceMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		instanceID := c.GetHeader("X-Bk-Micro-Gateway-Instance-Id")
		instanceSecret := c.GetHeader("X-Bk-Micro-Gateway-Instance-Secret")

		if instanceID == "" || instanceSecret == "" {
			util.UnauthorizedJSONResponse(c, "no authorization credentials provided")
			c.Abort()
			return
		}

		// the instance_id in path should equal to the instance_id in header
		instanceIDInPath := c.Params.ByName("micro_gateway_instance_id")
		if instanceID != instanceIDInPath {
			util.UnauthorizedJSONResponse(c, "instance id in header and path not match")
			c.Abort()
			return
		}

		matched, err := cacheimpls.VerifyMicroGatewayCredentials(instanceID, instanceSecret)
		if err != nil {
			err = fmt.Errorf("verify micro_gateway credentials fail, %w", err)
			util.SystemErrorJSONResponse(c, err)
			return
		}

		if !matched {
			util.UnauthorizedJSONResponse(c, "authorization credentials not valid")
			c.Abort()
			return
		}

		util.SetInstanceID(c, instanceID)

		c.Next()
	}
}
