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

// Package logging ...
package logging

import (
	"context"
	"log"
	"sync"

	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"

	"mcp_proxy/pkg/config"
	"mcp_proxy/pkg/constant"
	sty "mcp_proxy/pkg/infra/sentry"
	"mcp_proxy/pkg/infra/trace"
	"mcp_proxy/pkg/util"
)

var loggerInitOnce sync.Once

var (
	// for no-api logger
	defaultLogger *zap.SugaredLogger
	// for no-api logger
	apiLogger *zap.Logger
	// for audit logger
	auditLogger *zap.Logger
	// for database logger
	databaseLogger *zap.Logger
)

// InitLogger ...
func InitLogger(config *config.Config) {
	loggerInitOnce.Do(func() {
		options := make([]zap.Option, 0, 3)
		if sty.Enabled() {
			// init sentryCore
			sentryCore, err := newSentryLogCore(config)
			if err != nil {
				log.Printf("new sentry log core fail: %s\n", err.Error())
			} else {
				options = append(options, zap.WrapCore(func(core zapcore.Core) zapcore.Core {
					return zapcore.NewTee(sentryCore, core)
				}))
			}
		}
		options = append(options, zap.AddCaller())

		defaultLogger = newZapJSONLogger(&config.Logger.Default, options).Sugar()
		apiLogger = newZapJSONLogger(&config.Logger.API, options)
		auditLogger = newZapJSONLogger(&config.Logger.Audit, options)
		databaseLogger = newZapJSONLogger(&config.Logger.Database, options)
	})
}

// GetLogger will return the default logger
func GetLogger() *zap.SugaredLogger {
	return defaultLogger
}

// GetLoggerWithContext ...
func GetLoggerWithContext(ctx context.Context) *zap.SugaredLogger {
	ctxLogger := defaultLogger
	if requestID, ok := ctx.Value(util.RequestIDKey).(string); ok {
		ctxLogger = ctxLogger.With(zap.String("request_id", requestID))
	}
	if xRequestID, ok := ctx.Value(constant.XRequestID).(string); ok && xRequestID != "" {
		ctxLogger = ctxLogger.With(zap.String("x_request_id", xRequestID))
	}
	if username, ok := ctx.Value(constant.BkUsername).(string); ok && username != "" {
		ctxLogger = ctxLogger.With(zap.String("bk_username", username))
	}
	return ctxLogger
}

// GetAPILogger will return the api logger
func GetAPILogger() *zap.Logger {
	return apiLogger
}

// GetDatabaseLogger will return the database logger
func GetDatabaseLogger() *zap.Logger {
	return databaseLogger
}

// GetAuditLoggerWithContext ...
func GetAuditLoggerWithContext(ctx context.Context) *zap.Logger {
	ctxLogger := auditLogger
	if requestID, ok := ctx.Value(util.RequestIDKey).(string); ok {
		ctxLogger = ctxLogger.With(zap.String("request_id", requestID))
	}
	if xRequestID, ok := ctx.Value(constant.XRequestID).(string); ok && xRequestID != "" {
		ctxLogger = ctxLogger.With(zap.String("x_request_id", xRequestID))
	}
	if traceID := trace.GetTraceIDFromContext(ctx); traceID != "" {
		ctxLogger = ctxLogger.With(zap.String("trace_id", traceID))
	}
	if appCode, ok := ctx.Value(constant.BkAppCode).(string); ok {
		ctxLogger = ctxLogger.With(zap.String("bk_app_code", appCode))
	}
	if username, ok := ctx.Value(constant.BkUsername).(string); ok && username != "" {
		ctxLogger = ctxLogger.With(zap.String("bk_username", username))
	}
	if mcpServerID, ok := ctx.Value(constant.MCPServerID).(int); ok {
		ctxLogger = ctxLogger.With(zap.Int("mcp_server_id", mcpServerID))
	}
	if gatewayID, ok := ctx.Value(constant.GatewayID).(int); ok {
		ctxLogger = ctxLogger.With(zap.Int("gateway_id", gatewayID))
	}
	return ctxLogger
}
