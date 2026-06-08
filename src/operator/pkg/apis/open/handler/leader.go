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
	"net/http"

	"github.com/gin-gonic/gin"

	"operator/pkg/utils"
)

// GetLeader get leader pod host
func (r *ResourceHandler) GetLeader(c *gin.Context) {
	if r.LeaderElector == nil {
		utils.BaseErrorJSONResponse(c, utils.NotFoundError, "LeaderElector not found", http.StatusOK)
		return
	}
	utils.SuccessJSONResponse(c, r.LeaderElector.Leader())
}
