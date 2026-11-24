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

package util

import (
	"context"
	"encoding/json"
	"errors"
	"net"
	"syscall"

	"github.com/go-openapi/runtime"
	"github.com/modelcontextprotocol/go-sdk/jsonrpc"
)

// SafeLogError preserves typed failure categories and numeric protocol status.
// Arbitrary messages, URLs, hosts, paths and response payloads are never copied.
func SafeLogError(err error) string {
	if err == nil {
		return ""
	}
	details := map[string]any{"category": "error_details_hidden"}
	var rpc *jsonrpc.Error
	var api *runtime.APIError
	var syntax *json.SyntaxError
	var mismatch *json.UnmarshalTypeError
	var dns *net.DNSError
	var network net.Error
	switch {
	case errors.Is(err, context.DeadlineExceeded):
		details["category"] = "deadline_exceeded"
	case errors.Is(err, context.Canceled):
		details["category"] = "canceled"
	case errors.As(err, &rpc):
		details["category"] = "jsonrpc_error"
		details["code"] = rpc.Code
	case errors.As(err, &api):
		details["category"] = "upstream_http_error"
		details["status_code"] = api.Code
	case errors.As(err, &syntax):
		details["category"] = "invalid_json"
	case errors.As(err, &mismatch):
		details["category"] = "invalid_parameter_type"
	case errors.Is(err, syscall.ECONNREFUSED):
		details["category"] = "connection_refused"
	case errors.As(err, &network) && network.Timeout():
		details["category"] = "timeout"
	case errors.As(err, &dns):
		details["category"] = "dns_error"
	case errors.As(err, &network):
		details["category"] = "network_error"
	}
	out, encodeErr := json.Marshal(details)
	if encodeErr != nil {
		return HiddenLogBody
	}
	return string(out)
}
