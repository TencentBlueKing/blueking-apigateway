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
	"time"

	sentry "github.com/getsentry/sentry-go"
	"github.com/tchap/zapext/v2/zapsentry"
	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"

	"mcp_proxy/pkg/config"
)

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
	// 日志脱敏
	if cfg.Desensitization.Enabled {
		fieldMap := make(map[string][]string)
		for _, filed := range cfg.Desensitization.Fields {
			fieldMap[filed.Key] = filed.JsonPath
		}
		options = append(options, WithDesensitize(fieldMap))
	}

	return zap.New(core, options...)
}
