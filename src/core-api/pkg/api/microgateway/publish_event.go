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
	"github.com/gin-gonic/gin"
	"github.com/spf13/cast"

	"core/pkg/service"
	"core/pkg/util"
)

type reportPublishEventSerializer struct {
	GatewayName string                 `json:"gateway_name" binding:"required" example:"benchmark"`
	StageName   string                 `json:"stage_name"  binding:"required" example:"dev"`
	Name        string                 `json:"name"  binding:"required" example:"generate_release_task"`
	Status      string                 `json:"status" binding:"required" example:"success" `
	Detail      map[string]interface{} `json:"detail"`
}

// ReportPublishEvent report publish event
func ReportPublishEvent(c *gin.Context) {
	var query reportPublishEventSerializer
	if err := c.ShouldBindJSON(&query); err != nil {
		util.BadRequestErrorJSONResponse(c, util.ValidationErrorMessage(err))
		return
	}
	svc := service.NewPublishEventService()
	publishID := cast.ToInt64(c.Param("publish_id"))
	event := service.Event{
		Gateway:   query.GatewayName,
		Stage:     query.StageName,
		Name:      query.Name,
		Status:    query.Status,
		PublishID: publishID,
		DetailMap: query.Detail,
	}
	err := svc.Report(c.Request.Context(), event)
	if err != nil {
		util.SystemErrorJSONResponse(c, err)
		return
	}
	util.SuccessJSONResponse(c, gin.H{
		"result": "report success",
	})
}
