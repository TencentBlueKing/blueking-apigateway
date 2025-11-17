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

package server

import (
	"context"

	raven "github.com/getsentry/raven-go"
	"github.com/gin-contrib/pprof"
	"github.com/gin-gonic/contrib/sentry"
	"github.com/gin-gonic/gin"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"go.opentelemetry.io/contrib/instrumentation/github.com/gin-gonic/gin/otelgin"

	"mcp_proxy/pkg/config"
	"mcp_proxy/pkg/infra/logging"
	"mcp_proxy/pkg/infra/proxy"
	"mcp_proxy/pkg/mcp"
	"mcp_proxy/pkg/middleware"
	"mcp_proxy/pkg/util"
)

// NewRouter do the router initialization
func NewRouter(cfg *config.Config) *gin.Engine {
	router := gin.Default()

	router.Use(middleware.RequestID())
	// metrics
	router.Use(middleware.Metrics())
	// recovery sentry
	router.Use(sentry.Recovery(raven.DefaultClient, false))

	// basic
	// liveness
	router.GET("/ping", func(c *gin.Context) {
		c.JSON(200, gin.H{
			"message": "pong",
		})
	})

	// healthz
	router.GET("/healthz", func(c *gin.Context) {
		for _, dbConfig := range cfg.DatabaseMap {
			dbConfig := dbConfig
			// reset the options for check
			dbConfig.MaxIdleConns = 1
			dbConfig.MaxOpenConns = 1
			dbConfig.ConnMaxLifetimeSecond = 60
		}

		c.JSON(200, gin.H{
			"status": "ok",
		})
	})

	// pprof with basic auth (仅在启用时注册)
	pprofGroup := router.Group("/debug/pprof")
	pprofGroup.Use(gin.BasicAuth(gin.Accounts{
		cfg.PProf.Username: cfg.PProf.Password,
	}))
	pprof.RouteRegister(pprofGroup, "")
	logging.GetLogger().Infof("pprof enabled with basic auth at /debug/pprof")

	// metrics
	router.GET("/metrics", gin.WrapH(promhttp.Handler()))

	ctx := context.Background()

	// mcp 用户态mcp proxy
	mcpProxy := proxy.NewMCPProxy(cfg.McpServer.MessageUrlFormat)
	mcpSvc, err := mcp.Init(ctx, mcpProxy)
	if err != nil {
		logging.GetLogger().Panic("mcp user proxy init failed: %v", err)
		return nil
	}
	util.GoroutineWithRecovery(ctx, func() {
		mcpSvc.Run(ctx)
	})

	seeRouter := router.Group("/:name")
	seeRouter.Use(middleware.APILogger())
	seeRouter.Use(middleware.BkGatewayJWTAuthMiddleware())
	seeRouter.Use(middleware.MCPServerPermissionMiddleware())
	seeRouter.Use(middleware.MCPServerHeaderMiddleware())
	seeRouter.GET("/sse", mcpProxy.SseHandler())
	seeRouter.POST("/sse/message", mcpProxy.SseMessageHandler())

	// mcp application 应用态mcp proxy
	mcpApplicationProxy := proxy.NewMCPProxy(cfg.McpServer.MessageApplicationUrlFormat)
	mcpApplicationSvc, err := mcp.Init(ctx, mcpApplicationProxy)
	if err != nil {
		logging.GetLogger().Panic("mcp application proxy init failed: %v", err)
		return nil
	}
	util.GoroutineWithRecovery(ctx, func() {
		mcpApplicationSvc.Run(ctx)
	})

	seeAppRouter := router.Group("/:name/application")
	seeAppRouter.Use(middleware.APILogger())
	seeAppRouter.Use(middleware.BkGatewayJWTAuthMiddleware())
	seeAppRouter.Use(middleware.MCPServerPermissionMiddleware())
	seeAppRouter.Use(middleware.MCPServerHeaderMiddleware())
	seeAppRouter.GET("/sse", mcpApplicationProxy.SseHandler())
	seeAppRouter.POST("/sse/message", mcpApplicationProxy.SseMessageHandler())

	// trace
	if cfg.Tracing.GinAPIEnabled() {
		// set gin otel
		router.Use(otelgin.Middleware(cfg.Tracing.ServiceName))
	}

	return router
}
