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
	"strings"
	"sync"
	"time"

	"go.uber.org/zap"

	"core/pkg/config"
	"go.uber.org/zap/zapcore"
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
func InitLogger(logger *config.Logger) {
	loggerInitOnce.Do(func() {
		defaultLogger = newZapJSONLogger(&logger.Default).Sugar()

		// json logger
		apiLogger = newZapJSONLogger(&logger.API)
	})
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

func newZapJSONLogger(cfg *config.LogConfig) *zap.Logger {
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

	// 设置日志级别
	l, err := parseZapLogLevel(cfg.Level)
	if err != nil {
		fmt.Println("api logger settings level invalid, will use level: info")
		l = zap.InfoLevel
	}

	core := zapcore.NewCore(
		zapcore.NewJSONEncoder(zap.NewProductionEncoderConfig()),
		w,
		l,
	)
	return zap.New(core)
}

// GetLogger will return the default logger
func GetLogger() *zap.SugaredLogger {
	return defaultLogger
}

// GetAPILogger will return the api logger
func GetAPILogger() *zap.Logger {
	return apiLogger
}
