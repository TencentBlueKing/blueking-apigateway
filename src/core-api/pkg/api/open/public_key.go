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

package open

import (
	"database/sql"
	"errors"
	"net/http"

	"github.com/gin-gonic/gin"

	"core/pkg/constant"
	"core/pkg/service"
	"core/pkg/util"
)

type queryPublicKeySerializer struct {
	BkGatewayName string `uri:"gateway_name"  binding:"required"  example:"gateway"`
}

// QueryPublicKeyV1 godoc
// @Summary query public key of v1
// @Description query public key of v1
// @Tags open
// @Accept  json
// @Produce  json
// @Header 200 {string} X-Bkapi-Jwt "the bkapi jwt"
// @Param gateway_name path string true "gateway_name"
// @Success 200 {object} util.LegacySuccessResponse "success"
// @Success 400 {object} util.LegacyErrorResponse "Bad Request"
// @Success 401 {object} util.LegacyErrorResponse "Unauthorized"
// @Failure 404 {object} util.LegacyErrorResponse "Not Found"
// @Failure 500 {object} util.LegacyErrorResponse "Internal Server Error"
// @Router /api/v1/open/gateways/{gateway_name}/public_key/ [get]
func QueryPublicKeyV1(c *gin.Context) {
	// uri params: bk_gateway_name or api_name
	// response body:
	// {
	//     "data": {
	//        "public_key": ""
	//     }
	// }

	var query queryPublicKeySerializer
	if err := c.ShouldBindUri(&query); err != nil {
		util.LegacyErrorJSONResponse(c, util.BadRequestError, http.StatusBadRequest, err.Error())
		return
	}
	svc := service.NewGatewayPublicKeyService()

	publicKey, err := svc.GetByGatewayName(c.Request.Context(), query.BkGatewayName)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			util.LegacyErrorJSONResponse(c, util.NotFoundError, http.StatusNotFound, err.Error())
			return
		} else {
			util.LegacyErrorJSONResponse(c, util.SystemError, http.StatusInternalServerError, err.Error())
			return
		}
	}
	util.LegacySuccessJsonResponse(c, gin.H{
		"issuer":     c.GetString(constant.BkGatewayJWTIssuerKey),
		"public_key": publicKey,
	})
}

// QueryPublicKeyV2 godoc
// @Summary query public key of v2
// @Description query public key of v2
// @Tags open
// @Accept  json
// @Produce  json
// @Param gateway_name path string true "gateway_name"
// @Success 200 {object} util.SuccessResponse "success"
// @Failure 400 {object} util.ErrorResponse "Bad Request"
// @Failure 401 {object} util.ErrorResponse "Unauthorized"
// @Failure 404 {object} util.ErrorResponse "Not Found"
// @Failure 500 {object} util.ErrorResponse "Internal Server Error"
// @Router /api/v2/open/gateways/{gateway_name}/public_key/ [get]
func QueryPublicKeyV2(c *gin.Context) {
	// uri params: bk_gateway_name or api_name
	// response body:
	// {
	//     "data": {
	//        "public_key": ""
	//     }
	// }

	var query queryPublicKeySerializer
	if err := c.ShouldBindUri(&query); err != nil {
		util.BadRequestErrorJSONResponse(c, util.ValidationErrorMessage(err))
		return
	}
	svc := service.NewGatewayPublicKeyService()

	publicKey, err := svc.GetByGatewayName(c.Request.Context(), query.BkGatewayName)
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
		"issuer":     c.GetString(constant.BkGatewayJWTIssuerKey),
		"public_key": publicKey,
	})
}
