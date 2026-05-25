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

// Package open provides the API routes for the BlueKing API Gateway Operator.
package open

import (
	"github.com/gin-gonic/gin"

	"operator/pkg/apis/open/handler"
	"operator/pkg/core/committer"
	"operator/pkg/core/registry"
	"operator/pkg/core/store"
	"operator/pkg/leaderelection"
)

// Register registers the API routes
func Register(
	r *gin.RouterGroup,
	leaderElector *leaderelection.EtcdLeaderElector,
	registry *registry.APIGWEtcdRegistry,
	committer *committer.Committer,
	apisixConfStore *store.ApisixEtcdStore,
) {
	// register resource api
	resourceApi := handler.NewResourceApi(leaderElector, registry, committer, apisixConfStore)
	r.GET("/leader/", resourceApi.GetLeader)
	r.POST("/apigw/resources/", resourceApi.ApigwList)
	r.POST("/apigw/resources/count/", resourceApi.ApigwStageResourceCount)
	r.POST("/apigw/resources/current-version/", resourceApi.ApigwStageCurrentVersion)

	r.POST("/apisix/resources/", resourceApi.ApisixList)
	r.POST("/apisix/resources/count/", resourceApi.ApisixStageResourceCount)
	r.POST("/apisix/resources/current-version/", resourceApi.ApisixStageCurrentVersion)
}
