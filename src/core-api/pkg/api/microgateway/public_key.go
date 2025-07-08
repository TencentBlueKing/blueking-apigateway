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

package microgateway

import (
	"database/sql"
	"errors"

	"github.com/gin-gonic/gin"

	"core/pkg/service"
	"core/pkg/util"
)

type queryPublicKeySerializer struct {
	BkGatewayName string `form:"bk_gateway_name" binding:"required" example:"benchmark"`
}

// QueryPublicKey will query the public key for gateway from database
func QueryPublicKey(c *gin.Context) {
	// query params: bk_gateway_name
	// response body:
	// {
	//     "data": {
	//        "public_key": ""
	//     }
	// }

	var query queryPublicKeySerializer
	if err := c.ShouldBindQuery(&query); err != nil {
		util.BadRequestErrorJSONResponse(c, util.ValidationErrorMessage(err))
		return
	}

	svc := service.NewGatewayPublicKeyService()
	publicKey, err := svc.Get(c.Request.Context(), util.GetInstanceID(c), query.BkGatewayName)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			util.NotFoundJSONResponse(c, err.Error())
			return
		} else {
			util.SystemErrorJSONResponse(c, err)
			return
		}
	}
	util.SuccessJSONResponse(c, gin.H{
		"public_key": publicKey,
	})
}
