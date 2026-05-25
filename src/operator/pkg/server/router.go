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

// Package server ...
package server

import (
	"github.com/gin-gonic/gin"

	"operator/pkg/apis/open"
	"operator/pkg/config"
	"operator/pkg/constant"
	"operator/pkg/core/committer"
	"operator/pkg/core/registry"
	"operator/pkg/core/store"
	"operator/pkg/leaderelection"
	"operator/pkg/utils"
)

// NewRouter do the router initialization
func NewRouter(
	leaderElector *leaderelection.EtcdLeaderElector,
	registry *registry.APIGWEtcdRegistry,
	committer *committer.Committer,
	apiSixConfStore *store.ApisixEtcdStore,
	router *gin.Engine,
	conf *config.Config,
) *gin.Engine {
	router.GET("/ping", func(c *gin.Context) {
		utils.SuccessJSONResponse(c, "ok")
	})
	router.GET("/healthz", func(c *gin.Context) {
		utils.SuccessJSONResponse(c, "ok")
	})
	operatorRouter := router.Group("/v1/open")
	operatorRouter.Use(gin.BasicAuth(gin.Accounts{
		constant.ApiAuthAccount: conf.HttpServer.AuthPassword,
	}))
	operatorRouter.Use(gin.Recovery())
	open.Register(operatorRouter, leaderElector, registry, committer, apiSixConfStore)
	return router
}
