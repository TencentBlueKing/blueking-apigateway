/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) Tencent. All rights reserved.
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

// Package handler  ...
package handler

import (
	"encoding/json"
	"fmt"
	"net/http"

	"github.com/gin-gonic/gin"

	"operator/pkg/apis/open/serializer"
	"operator/pkg/biz"
	"operator/pkg/utils"
)

// ApigwList 查询 apigw 当前环境的资源列表
func (r *ResourceHandler) ApigwList(c *gin.Context) {
	var req serializer.ApigwListRequest
	if err := c.ShouldBind(&req); err != nil {
		utils.BadRequestErrorJSONResponse(c, utils.ValidationErrorMessage(err))
		return
	}
	resp := make(serializer.ApigwListInfo)
	if req.Resource.ID != 0 || req.Resource.Name != "" {
		apigwResource, err := biz.GetApigwResource(
			c,
			r.committer,
			req.GatewayName,
			req.StageName,
			req.Resource.Name,
			req.Resource.ID,
		)
		if err != nil {
			utils.BaseErrorJSONResponse(
				c,
				utils.SystemError,
				fmt.Sprintf("apigw list err:%+v", err.Error()),
				http.StatusOK,
			)
			return
		}
		by, err := json.Marshal(apigwResource)
		if err != nil {
			utils.BaseErrorJSONResponse(
				c,
				utils.SystemError,
				fmt.Sprintf("apigw list err:%+v", err.Error()),
				http.StatusOK,
			)
			return
		}
		_ = json.Unmarshal(by, &resp)
		utils.SuccessJSONResponse(c, resp)
		return
	}
	apigwList, err := biz.ListApigwResources(c, r.committer, req.GatewayName, req.StageName)
	if err != nil {
		utils.BaseErrorJSONResponse(
			c,
			utils.SystemError,
			fmt.Sprintf("apigw list err:%+v", err.Error()),
			http.StatusOK,
		)
		return
	}
	by, err := json.Marshal(apigwList)
	if err != nil {
		utils.BaseErrorJSONResponse(
			c,
			utils.SystemError,
			fmt.Sprintf("apigw list err:%+v", err.Error()),
			http.StatusOK,
		)
		return
	}
	_ = json.Unmarshal(by, &resp)
	utils.SuccessJSONResponse(c, resp)
}

// ApigwStageResourceCount 查询 apigw 当前环境资源数量
func (r *ResourceHandler) ApigwStageResourceCount(c *gin.Context) {
	var req serializer.ApigwListRequest
	if err := c.ShouldBind(&req); err != nil {
		utils.BadRequestErrorJSONResponse(c, utils.ValidationErrorMessage(err))
		return
	}
	count, err := biz.GetApigwResourceCount(c, r.committer, req.GatewayName, req.StageName)
	if err != nil {
		utils.BaseErrorJSONResponse(
			c,
			utils.SystemError,
			fmt.Sprintf("apigw count:%+v", err.Error()),
			http.StatusOK,
		)
		return
	}
	output := serializer.ApigwListResourceCountResponse{Count: count}
	utils.SuccessJSONResponse(c, output)
}

// ApigwStageCurrentVersion 查询 apigw 当前环境发布后的版本
func (r *ResourceHandler) ApigwStageCurrentVersion(c *gin.Context) {
	var req serializer.ApigwListRequest
	if err := c.ShouldBind(&req); err != nil {
		utils.BadRequestErrorJSONResponse(c, utils.ValidationErrorMessage(err))
		return
	}
	versionInfo, err := biz.GetApigwStageCurrentVersionInfo(c, r.committer, req.GatewayName, req.StageName)
	if err != nil {
		utils.BaseErrorJSONResponse(
			c,
			utils.SystemError,
			fmt.Sprintf("apigw version:%+v", err.Error()),
			http.StatusOK,
		)
		return
	}
	output := serializer.ApigwListCurrentVersionInfoResponse(versionInfo)
	utils.SuccessJSONResponse(c, output)
}
