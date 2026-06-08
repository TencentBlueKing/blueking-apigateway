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

// Package logging ...
package logging

import (
	"fmt"
	"time"

	sentry "github.com/getsentry/sentry-go"
	"github.com/go-logr/zapr"
	"github.com/tchap/zapext/v2/zapsentry"
	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
	ctrl "sigs.k8s.io/controller-runtime"
	ctrlZap "sigs.k8s.io/controller-runtime/pkg/log/zap"

	"operator/pkg/config"
)

var defaultLogger *zap.Logger

// Init ...
func Init(cfg *config.Config) {
	// init sentry
	var (
		sentryCore zapcore.Core
		err        error
	)
	if len(cfg.Sentry.Dsn) != 0 {
		sentryCore, err = newSentryLogCore(cfg)
		if err != nil {
			fmt.Printf("new sentry log core fail: %s\n", err.Error())
		}
	}

	options := make([]zap.Option, 0, 3)
	if sentryCore != nil {
		options = append(options, zap.WrapCore(func(core zapcore.Core) zapcore.Core {
			return zapcore.NewTee(sentryCore, core)
		}))
	}
	options = append(options, zap.AddCaller())

	// init zap
	initControllerLogger(&cfg.Logger.Controller, options)

	initSystemLogger(&cfg.Logger.Default, options)
}

func initControllerLogger(cfg *config.LogConfig, options []zap.Option) {
	writer, err := getWriter(cfg.Writer, cfg.Settings)
	if err != nil {
		panic(err)
	}

	zapOpts := ctrlZap.Options{
		EncoderConfigOptions: []ctrlZap.EncoderConfigOption{func(ec *zapcore.EncoderConfig) {
			ec.EncodeTime = zapcore.RFC3339NanoTimeEncoder
		}},
		Level:      newZapLevel(cfg.Level),
		DestWriter: writer,
	}

	ctrl.SetLogger(ctrlZap.New(ctrlZap.UseFlagOptions(&zapOpts), ctrlZap.RawZapOpts(options...)))
}

func initSystemLogger(cfg *config.LogConfig, options []zap.Option) {
	writer, err := getWriter(cfg.Writer, cfg.Settings)
	if err != nil {
		panic(err)
	}
	w := zapcore.AddSync(writer)
	encoderConfig := zap.NewProductionEncoderConfig()
	encoderConfig.EncodeTime = timeEncoder
	// 设置日志级别
	l := newZapLevel(cfg.Level)
	core := zapcore.NewCore(
		zapcore.NewJSONEncoder(encoderConfig),
		w,
		l,
	)

	defaultLogger = zap.New(core, options...)
}

func newZapLevel(levelStr string) zap.AtomicLevel {
	level := zap.NewAtomicLevelAt(zapcore.InfoLevel)
	switch levelStr {
	case "debug":
		level = zap.NewAtomicLevelAt(zapcore.DebugLevel)
	case "info":
		level = zap.NewAtomicLevelAt(zapcore.InfoLevel)
	case "warn":
		level = zap.NewAtomicLevelAt(zapcore.WarnLevel)
	case "error":
		level = zap.NewAtomicLevelAt(zapcore.ErrorLevel)
	case "fatal":
		level = zap.NewAtomicLevelAt(zapcore.FatalLevel)
	case "panic":
		level = zap.NewAtomicLevelAt(zapcore.PanicLevel)
	}
	return level
}

func newSentryLogCore(cfg *config.Config) (zapcore.Core, error) {
	rawCore := zapsentry.NewCore(zapcore.Level(cfg.Sentry.ReportLevel), sentry.CurrentHub().Client())
	sentryCore := zapcore.RegisterHooks(rawCore, func(entry zapcore.Entry) error {
		if entry.Level == zapcore.FatalLevel {
			sentry.CurrentHub().Client().Flush(2 * time.Second)
		}
		return nil
	})
	return sentryCore, nil
}

// GetControllerLogger ...
func GetControllerLogger() *zap.Logger {
	return ctrl.Log.WithName("controller").GetSink().(zapr.Underlier).GetUnderlying() //nolint:forcetypeassert
}

// GetLogger ...
func GetLogger() *zap.SugaredLogger {
	if defaultLogger == nil {
		logger, _ := zap.NewProduction()
		defer func() { _ = logger.Sync() }()
		return logger.Sugar()
	}
	return defaultLogger.Sugar()
}

func timeEncoder(t time.Time, enc zapcore.PrimitiveArrayEncoder) {
	enc.AppendString(t.Format("2006-01-02 15:04:05"))
}
