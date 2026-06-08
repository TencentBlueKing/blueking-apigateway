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

// Package server provides the server for the BlueKing API Gateway Operator.
package server

import (
	"context"
	"strconv"

	"github.com/gin-contrib/pprof"
	"github.com/gin-gonic/gin"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"go.uber.org/zap"

	"operator/pkg/config"
	"operator/pkg/constant"
	"operator/pkg/core/committer"
	"operator/pkg/core/registry"
	"operator/pkg/core/store"
	"operator/pkg/leaderelection"
	"operator/pkg/logging"
)

// Server ...
type Server struct {
	LeaderElector     *leaderelection.EtcdLeaderElector
	apigwEtcdRegistry *registry.APIGWEtcdRegistry
	committer         *committer.Committer
	apisixEtcdStore   *store.ApisixEtcdStore

	mux *gin.Engine

	logger *zap.SugaredLogger
}

// NewServer ...
func NewServer(
	leaderElector *leaderelection.EtcdLeaderElector,
	apigwEtcdRegistry *registry.APIGWEtcdRegistry,
	apisixEtcdStore *store.ApisixEtcdStore,
	committer *committer.Committer,
) *Server {
	return &Server{
		LeaderElector:     leaderElector,
		apigwEtcdRegistry: apigwEtcdRegistry,
		apisixEtcdStore:   apisixEtcdStore,
		committer:         committer,
		logger:            logging.GetLogger().Named("server"),
		mux:               gin.Default(),
	}
}

// RegisterMetric ...
func (s *Server) RegisterMetric(gatherer prometheus.Gatherer) {
	handler := promhttp.HandlerFor(gatherer, promhttp.HandlerOpts{
		ErrorHandling: promhttp.HTTPErrorOnError,
	})

	s.mux.GET("/metrics", gin.WrapH(handler))
}

// Run ...
func (s *Server) Run(ctx context.Context, config *config.Config) error {
	router := NewRouter(s.LeaderElector, s.apigwEtcdRegistry, s.committer, s.apisixEtcdStore, s.mux, config)
	// run http server
	var addr, addrv6 string
	if config.HttpServer.BindAddressV6 != "" {
		addrv6 = config.HttpServer.BindAddressV6 + ":" + strconv.Itoa(
			config.HttpServer.BindPort,
		)
		go MustServeHTTP(ctx, addrv6, "tcp6", router)
	}

	// register pprof router, not only for debug mode
	{
		pprofRouter := router.Group("/debug/pprof")
		pprofRouter.Use(gin.BasicAuth(gin.Accounts{
			constant.ApiAuthAccount: config.HttpServer.AuthPassword,
		}))
		pprof.Register(pprofRouter, "")
	}

	if config.HttpServer.BindAddress != "" {
		addr = config.HttpServer.BindAddress + ":" + strconv.Itoa(
			config.HttpServer.BindPort,
		)
		go MustServeHTTP(ctx, addr, "tcp4", router)
	}
	return nil
}
