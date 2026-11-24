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

package mcp_test

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"

	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"

	sdkmcp "github.com/modelcontextprotocol/go-sdk/mcp"
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"

	"mcp_proxy/pkg/infra/logging"
	mcppkg "mcp_proxy/pkg/mcp"
)

var _ = Describe("Credential masking protocol middleware", func() {
	DescribeTable("protects emitted method logs and preserves results", func(method string, failure bool) {
		var out bytes.Buffer
		logger := zap.New(
			zapcore.NewCore(
				zapcore.NewJSONEncoder(zap.NewProductionEncoderConfig()),
				zapcore.AddSync(&out),
				zap.InfoLevel,
			),
			logging.WithDesensitize(nil),
		)
		args := json.RawMessage(`{"token":"credential-params","data":[{"api_key":"credential-nested"}]}`)
		req := &sdkmcp.CallToolRequest{Params: &sdkmcp.CallToolParamsRaw{Name: "example", Arguments: args}}
		response := &sdkmcp.CallToolResult{
			Content: []sdkmcp.Content{&sdkmcp.TextContent{Text: `{"token":"credential-result"}`}},
		}
		var handlerErr error
		if failure {
			handlerErr = errors.New("credential-error")
		}
		handler := mcppkg.LoggingMiddlewareWithLogger(
			"test-server", logger,
		)(
			func(_ context.Context, _ string, got sdkmcp.Request) (sdkmcp.Result, error) {
				Expect(got).To(BeIdenticalTo(req))
				return response, handlerErr
			},
		)
		result, callErr := handler(context.Background(), method, req)
		Expect(result).To(BeIdenticalTo(response))
		if failure {
			Expect(callErr).To(BeIdenticalTo(handlerErr))
		} else {
			Expect(callErr).NotTo(HaveOccurred())
		}
		Expect(string(req.Params.Arguments)).To(Equal(string(args)))
		Expect(response.Content[0].(*sdkmcp.TextContent).Text).To(Equal(`{"token":"credential-result"}`))
		Expect(logger.Sync()).To(Succeed())
		logs := out.String()
		Expect(logs).NotTo(BeEmpty())
		Expect(logs).NotTo(ContainSubstring("credential-"))
		Expect(logs).To(ContainSubstring("***"))
	}, Entry("other method", "tools/list", false), Entry("other method failure", "prompts/get", true), Entry("pre-handler tools/call failure", "tools/call", true))
})
