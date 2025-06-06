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
)

var loggerInitOnce sync.Once

var (
	// for no-api logger
	defaultLogger *zap.SugaredLogger
	// for no-api logger
	apiLogger *zap.Logger
	// for audit logger
	auditLogger *zap.Logger
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
	})
}

// GetLogger will return the default logger
func GetLogger() *zap.SugaredLogger {
	return defaultLogger
}

// GetLoggerWithContext ...
func GetLoggerWithContext(ctx context.Context) *zap.SugaredLogger {
	ctxLogger := defaultLogger
	if requestID, ok := ctx.Value(constant.RequestID).(string); ok {
		ctxLogger = defaultLogger.With(zap.String("request_id", requestID))
	}
	return ctxLogger
}

// GetAPILogger will return the api logger
func GetAPILogger() *zap.Logger {
	return apiLogger
}

// GetAuditLoggerWithContext ...
func GetAuditLoggerWithContext(ctx context.Context) *zap.Logger {
	ctxLogger := auditLogger
	if requestID, ok := ctx.Value(constant.RequestID).(string); ok {
		ctxLogger = auditLogger.With(zap.String("request_id", requestID))
	}
	if appCode, ok := ctx.Value(constant.BkAppCode).(string); ok {
		ctxLogger = auditLogger.With(zap.String("bk_app_code", appCode))
	}
	if mcpServerID, ok := ctx.Value(constant.MCPServerID).(string); ok {
		ctxLogger = auditLogger.With(zap.String("mcp_server_id", mcpServerID))
	}
	return ctxLogger
}
