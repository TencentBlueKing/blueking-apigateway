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

package logging_test

import (
	"bytes"
	"encoding/json"
	"io/ioutil"
	"os"
	"testing"
	"time"

	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"

	"mcp_proxy/pkg/infra/logging"
)

func BenchmarkLoggingWithoutDesensitize(b *testing.B) {
	file, err := ioutil.TempFile(".", "logging_test_*.log")
	if err != nil {
		b.Fatalf("Failed to create log file: %v", err)
	}
	defer os.Remove(file.Name())

	encoder := zapcore.NewJSONEncoder(zap.NewProductionEncoderConfig())

	w := &zapcore.BufferedWriteSyncer{
		WS:            zapcore.AddSync(file),
		Size:          256 * 1024, // 256 kB
		FlushInterval: 30 * time.Second,
	}
	core := zapcore.NewCore(encoder, w, zapcore.InfoLevel)

	logger := zap.New(core)
	defer logger.Sync()

	body := map[string]interface{}{
		"username":           "user1",
		"password":           "password1",
		"credit_card_number": "1234-5678-9012-3456",
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		logger.Info("Sensitive data", zap.Any("body", body))
	}
}

func BenchmarkLoggingWithDesensitize(b *testing.B) {
	file, err := ioutil.TempFile(".", "logging_test_*.log")
	if err != nil {
		b.Fatalf("Failed to create log file: %v", err)
	}
	defer os.Remove(file.Name())

	encoder := zapcore.NewJSONEncoder(zap.NewProductionEncoderConfig())

	w := &zapcore.BufferedWriteSyncer{
		WS:            zapcore.AddSync(file),
		Size:          256 * 1024, // 256 kB
		FlushInterval: 30 * time.Second,
	}

	core := zapcore.NewCore(encoder, w, zapcore.InfoLevel)

	logger := zap.New(core, logging.WithDesensitize(map[string][]string{
		"body": {"password", "credit_card_number"},
	}))
	defer logger.Sync()

	body := map[string]interface{}{
		"username":           "user1",
		"password":           "passwor",
		"credit_card_number": "1234-5678-9012-3456",
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		logger.Info("Sensitive data", zap.Any("body", body))
	}
}

func BenchmarkLoggingJSONWithoutDesensitize(b *testing.B) {
	file, err := ioutil.TempFile(".", "logging_test_*.log")
	if err != nil {
		b.Fatalf("Failed to create log file: %v", err)
	}
	defer os.Remove(file.Name())

	encoder := zapcore.NewJSONEncoder(zap.NewProductionEncoderConfig())
	w := &zapcore.BufferedWriteSyncer{
		WS:            zapcore.AddSync(file),
		Size:          256 * 1024, // 256 kB
		FlushInterval: 30 * time.Second,
	}
	core := zapcore.NewCore(encoder, w, zapcore.InfoLevel)

	logger := zap.New(core)
	defer logger.Sync()

	body := map[string]interface{}{
		"username":           "user1",
		"password":           "password1",
		"credit_card_number": "1234-5678-9012-3456",
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		buf := new(bytes.Buffer)
		if err := json.NewEncoder(buf).Encode(body); err != nil {
			b.Fatalf("Failed to encode JSON: %v", err)
		}
		logger.Info("Sensitive data", zap.String("body", buf.String()))
	}
}

func BenchmarkLoggingJSONWithDesensitize(b *testing.B) {
	file, err := ioutil.TempFile(".", "logging_test_*.log")
	if err != nil {
		b.Fatalf("Failed to create log file: %v", err)
	}
	defer os.Remove(file.Name())

	encoder := zapcore.NewJSONEncoder(zap.NewProductionEncoderConfig())
	w := &zapcore.BufferedWriteSyncer{
		WS:            zapcore.AddSync(file),
		Size:          256 * 1024, // 256 kB
		FlushInterval: 30 * time.Second,
	}
	core := zapcore.NewCore(encoder, w, zapcore.InfoLevel)

	logger := zap.New(core, logging.WithDesensitize(map[string][]string{
		"body": {"password", "credit_card_number"},
	}))
	defer logger.Sync()

	body := map[string]interface{}{
		"username":           "user1",
		"password":           "password1",
		"credit_card_number": "1234-5678-9012-3456",
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		buf := new(bytes.Buffer)
		if err := json.NewEncoder(buf).Encode(body); err != nil {
			b.Fatalf("Failed to encode JSON: %v", err)
		}
		logger.Info("Sensitive data", zap.String("body", buf.String()))
	}
}

func TestDesensitize_JsonArray(t *testing.T) {
	file, err := ioutil.TempFile(".", "logging_test_*.log")
	if err != nil {
		t.Fatalf("Failed to create log file: %v", err)
	}
	defer os.Remove(file.Name())

	encoder := zapcore.NewJSONEncoder(zap.NewProductionEncoderConfig())
	w := &zapcore.BufferedWriteSyncer{
		WS:            zapcore.AddSync(file),
		Size:          256 * 1024, // 256 kB
		FlushInterval: 30 * time.Second,
	}
	core := zapcore.NewCore(encoder, w, zapcore.InfoLevel)

	logger := zap.New(core, logging.WithDesensitize(map[string][]string{
		"body": {"data.#.bk_app_secret"},
	}))
	defer logger.Sync()

	body := map[string]interface{}{
		"data": []struct {
			BkAppSecret string `json:"bk_app_secret"`
			BkAppCode   string `json:"bk_app_code"`
		}{
			{BkAppSecret: "1111-5678-9012-1111", BkAppCode: "test1"},
			{BkAppSecret: "2222-5678-9012-2222", BkAppCode: "test2"},
			{BkAppSecret: "3333-5678-9012-3333", BkAppCode: "test3"},
		},
	}

	buf := new(bytes.Buffer)
	if err := json.NewEncoder(buf).Encode(body); err != nil {
		t.Fatalf("Failed to encode JSON: %v", err)
	}
	logger.Info("Sensitive data", zap.String("body", buf.String()))
	//{"level":"info","ts":1699933892.8620539,"msg":"Sensitive data",
	//"body":"{\"date\":[
	//{\"bk_app_secret\":\"111***************111\",\"bk_app_code\":\"test1\"},
	//{\"bk_app_secret\":\"222***************222\",\"bk_app_code\":\"test2\"},
	//{\"bk_app_secret\":\"333***************333\",\"bk_app_code\":\"test3\"}]}\n"}
}
