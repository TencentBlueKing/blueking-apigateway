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
	"time"

	"github.com/gin-contrib/pprof"
	"github.com/gin-gonic/gin"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"go.opentelemetry.io/contrib/instrumentation/github.com/gin-gonic/gin/otelgin"

	"mcp_proxy/pkg/config"
	"mcp_proxy/pkg/infra/logging"
	"mcp_proxy/pkg/infra/proxy"
	sty "mcp_proxy/pkg/infra/sentry"
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
	router.Use(sty.Recovery())
	// trace - otelgin middleware must be placed before route groups to cover all routes
	if cfg.Tracing.GinAPIEnabled() {
		router.Use(otelgin.Middleware(cfg.Tracing.ServiceName))
	}

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

	// pprof with basic auth (仅在配置了用户名密码时启用)
	if cfg.PProf.Username != "" && cfg.PProf.Password != "" {
		pprofGroup := router.Group("/debug/pprof")
		pprofGroup.Use(gin.BasicAuth(gin.Accounts{
			cfg.PProf.Username: cfg.PProf.Password,
		}))
		pprof.RouteRegister(pprofGroup, "")
		logging.GetLogger().Infof("pprof enabled with basic auth at /debug/pprof")
	} else {
		logging.GetLogger().Warnf("pprof disabled: PPROF_USERNAME and PPROF_PASSWORD environment variables not set")
	}

	// metrics
	router.GET("/metrics", gin.WrapH(promhttp.Handler()))

	ctx := context.Background()

	// mcp proxy: 用户态和应用态共享同一个 MCPProxy 实例
	// 两者加载相同的 MCP Server 数据，仅路由前缀不同
	mcpInitStart := time.Now()
	proxy.InitSharedTransport(cfg.McpServer.Transport)
	mcpProxy := proxy.NewMCPProxy()
	mcpSvc, err := mcp.Init(ctx, mcpProxy)
	if err != nil {
		logging.GetLogger().Panicf("mcp proxy init failed: %v", err)
		return nil
	}
	util.GoroutineWithRecovery(ctx, func() {
		mcpSvc.Run(ctx)
	})
	logging.GetLogger().Infof("mcp proxy init complete, duration=%s", time.Since(mcpInitStart))

	// 用户态路由
	seeRouter := router.Group("/:name")
	seeRouter.Use(middleware.APILogger())
	seeRouter.Use(middleware.BkGatewayJWTAuthMiddleware())
	seeRouter.Use(middleware.MCPServerPermissionMiddleware())
	seeRouter.Use(middleware.MCPServerHeaderMiddleware())
	// SSE 协议路由 - 官方 SDK 的 SSEHandler 同时处理 GET 和 POST 请求
	seeRouter.GET("/sse", mcpProxy.SseHandler())
	seeRouter.POST("/sse", mcpProxy.SseHandler())
	// Streamable HTTP 协议路由
	seeRouter.GET("/mcp", mcpProxy.StreamableHTTPHandler())
	seeRouter.POST("/mcp", mcpProxy.StreamableHTTPHandler())

	// 应用态路由（共享 MCPProxy 实例）
	seeAppRouter := router.Group("/:name/application")
	seeAppRouter.Use(middleware.APILogger())
	seeAppRouter.Use(middleware.BkGatewayJWTAuthMiddleware())
	seeAppRouter.Use(middleware.MCPServerPermissionMiddleware())
	seeAppRouter.Use(middleware.MCPServerHeaderMiddleware())
	// SSE 协议路由 - 官方 SDK 的 SSEHandler 同时处理 GET 和 POST 请求
	seeAppRouter.GET("/sse", mcpProxy.SseHandler())
	seeAppRouter.POST("/sse", mcpProxy.SseHandler())
	// Streamable HTTP 协议路由
	seeAppRouter.GET("/mcp", mcpProxy.StreamableHTTPHandler())
	seeAppRouter.POST("/mcp", mcpProxy.StreamableHTTPHandler())

	return router
}
