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
	"fmt"
	"log"
	"strings"
	"sync"
	"time"

	"github.com/getsentry/sentry-go"
	"go.uber.org/zap"

	"github.com/tchap/zapext/v2/zapsentry"
	"go.uber.org/zap/zapcore"

	"core/pkg/config"
)

var loggerInitOnce sync.Once

// for no-api logger
var defaultLogger = newZapSugarLogger()

// for api
var apiLogger *zap.Logger

func newZapSugarLogger() *zap.SugaredLogger {
	logger, _ := zap.NewProduction()
	// nolint: errcheck
	defer logger.Sync() // flushes buffer, if any
	sugar := logger.Sugar()

	return sugar
}

// InitLogger ...
func InitLogger(config *config.Config) {
	loggerInitOnce.Do(func() {
		options := make([]zap.Option, 0, 3)
		if len(config.Sentry.DSN) != 0 {
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

		// json logger
		apiLogger = newZapJSONLogger(&config.Logger.API, options)
	})
}

// newSentryLogCore
func newSentryLogCore(cfg *config.Config) (zapcore.Core, error) {
	rawCore := zapsentry.NewCore(zapcore.Level(cfg.Sentry.ReportLogLevel), sentry.CurrentHub().Client())
	sentryCore := zapcore.RegisterHooks(rawCore, func(entry zapcore.Entry) error {
		if entry.Level == zapcore.FatalLevel {
			sentry.CurrentHub().Client().Flush(2 * time.Second)
		}
		return nil
	})
	return sentryCore, nil
}

// parseZapLogLevel takes a string level and returns the zap log level constant.
func parseZapLogLevel(lvl string) (zapcore.Level, error) {
	switch strings.ToLower(lvl) {
	case "panic":
		return zap.PanicLevel, nil
	case "fatal":
		return zap.FatalLevel, nil
	case "error":
		return zap.ErrorLevel, nil
	case "warn", "warning":
		return zap.WarnLevel, nil
	case "info":
		return zap.InfoLevel, nil
	case "debug":
		return zap.DebugLevel, nil
	}

	var l zapcore.Level
	return l, fmt.Errorf("not a valid logrus Level: %q", lvl)
}

func newZapJSONLogger(cfg *config.LogConfig, options []zap.Option) *zap.Logger {
	writer, err := getWriter(cfg.Writer, cfg.Settings)
	if err != nil {
		panic(err)
	}

	ws := zapcore.AddSync(writer)

	w := ws
	if cfg.Buffered {
		w = &zapcore.BufferedWriteSyncer{
			WS:            ws,
			Size:          256 * 1024, // 256 kB
			FlushInterval: 30 * time.Second,
		}
	}

	encoderConfig := zap.NewProductionEncoderConfig()
	// 设置时间格式
	encoderConfig.EncodeTime = zapcore.RFC3339NanoTimeEncoder

	// 设置日志级别
	l, err := parseZapLogLevel(cfg.Level)
	if err != nil {
		fmt.Println("api logger settings level invalid, will use level: info")
		l = zap.InfoLevel
	}

	core := zapcore.NewCore(
		zapcore.NewJSONEncoder(encoderConfig),
		w,
		l,
	)
	return zap.New(core, options...)
}

// GetLogger will return the default logger
func GetLogger() *zap.SugaredLogger {
	return defaultLogger
}

// GetAPILogger will return the api logger
func GetAPILogger() *zap.Logger {
	return apiLogger
}
