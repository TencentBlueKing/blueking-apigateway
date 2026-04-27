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

// Package server is the server for the whole project
package server

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"mcp_proxy/pkg/config"
	"mcp_proxy/pkg/infra/bkaidevtrace"
	"mcp_proxy/pkg/infra/logging"
	sty "mcp_proxy/pkg/infra/sentry"
)

// Run the server, and can be gracefully shutdown
func Run(cfg *config.Config) {
	router := NewRouter(cfg)

	addr := fmt.Sprintf("%s:%d", cfg.Server.Host, cfg.Server.Port)

	logging.GetLogger().Infof("the server addr: %s", addr)

	srv := &http.Server{
		Addr:    addr,
		Handler: router,
	}

	go func() {
		// service connections
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			logging.GetLogger().Fatalf("listen: %s\n", err)
		}
	}()

	// Wait for interrupt signal to gracefully shutdown the server with
	// a timeout of 5 seconds.
	quit := make(chan os.Signal, 1)
	// kill (no param) default send syscanll.SIGTERM
	// kill -2 is syscall.SIGINT
	// kill -9 is syscall. SIGKILL but can"t be catch, so don't need add it
	// nolint: govet
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit
	logging.GetLogger().Info("Shutdown Server ...")

	// Flush buffered sentry events before exit (defer ensures this runs even on fatal paths)
	defer sty.Flush(2 * time.Second)

	// Shutdown HTTP server with a 5-second timeout
	srvCtx, srvCancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer srvCancel()

	if err := srv.Shutdown(srvCtx); err != nil {
		logging.GetLogger().Errorf("Server Shutdown: %s", err)
	}

	// Shutdown BkAIDev trace provider with its own independent context,
	// so it has a full 3 seconds to flush buffered spans regardless of
	// how long srv.Shutdown took.
	traceCtx, traceCancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer traceCancel()

	if err := bkaidevtrace.Shutdown(traceCtx); err != nil {
		logging.GetLogger().Errorf("BkAIDev trace shutdown error: %s", err)
	}

	logging.GetLogger().Info("Server exiting")
}
