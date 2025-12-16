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

package logging_test

import (
	"bytes"
	"encoding/json"
	"os"
	"time"

	. "github.com/onsi/ginkgo/v2"
	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"

	"mcp_proxy/pkg/infra/logging"
)

var _ = Describe("Desensitize", func() {
	Describe("JsonArray", func() {
		It("should desensitize array fields", func() {
			file, err := os.CreateTemp(".", "logging_test_*.log")
			if err != nil {
				Fail("Failed to create log file")
			}
			defer os.Remove(file.Name())

			encoder := zapcore.NewJSONEncoder(zap.NewProductionEncoderConfig())
			w := &zapcore.BufferedWriteSyncer{
				WS:            zapcore.AddSync(file),
				Size:          256 * 1024,
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
			err = json.NewEncoder(buf).Encode(body)
			if err != nil {
				Fail("Failed to encode JSON")
			}
			logger.Info("Sensitive data", zap.String("body", buf.String()))
		})
	})
})
