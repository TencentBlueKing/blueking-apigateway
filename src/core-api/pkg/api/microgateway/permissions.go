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

package microgateway

import (
	"database/sql"
	"errors"

	"core/pkg/service"
	"core/pkg/util"

	"github.com/gin-gonic/gin"
)

type queryPermissionSerializer struct {
	BkGatewayName  string `form:"bk_gateway_name" binding:"required" example:"benchmark"`
	BkStageName    string `form:"bk_stage_name" binding:"required" example:"dev"`
	BkResourceName string `form:"bk_resource_name" binding:"required" example:"app_verify"`
	BkAppCode      string `form:"bk_app_code" binding:"required" example:"bk_apigateway"`
}

// QueryPermission will query the permission for app_code from database,
// it include the gateway permission and resource permission
func QueryPermission(c *gin.Context) {
	// query params: bk_gateway_name, bk_resource_name, bk_app_code
	// response body:
	// {
	//   "data": {
	//       "{bk_gateway_name}:-:{bk_app_code}": 1681897413,
	//       "{bk_gateway_name}:{bk_resource_name}:{bk_app_code}": 1681897413,
	//   }
	// }

	var query queryPermissionSerializer
	if err := c.ShouldBindQuery(&query); err != nil {
		util.BadRequestErrorJSONResponse(c, util.ValidationErrorMessage(err))
		return
	}

	svc := service.NewAppPermissionService()
	permissions, err := svc.Query(
		c.Request.Context(),
		util.GetInstanceID(c),
		query.BkGatewayName,
		query.BkStageName,
		query.BkResourceName,
		query.BkAppCode,
	)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			util.NotFoundJSONResponse(c, err.Error())
			return
		} else {
			util.SystemErrorJSONResponse(c, err)
			return
		}
	}
	util.SuccessJSONResponse(c, permissions)
}
