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

// Package constant ...
package constant

// BkGatewayJWTHeaderKey ...
const (
	BkGatewayJWTHeaderKey = "X-Bkapi-Jwt"
	BkGatewayRequestIDKey = "X-Bkapi-Request-ID"
	OfficialGatewayName   = "bk-apigateway"
	// RequestIDHeaderKey is a key to set the request id in header
	RequestIDHeaderKey = "X-Request-Id"

	BkApiAuthorizationHeaderKey = "X-Bkapi-Authorization"

	// BkApiTimeoutHeaderKey is a key to set the timeout in header
	BkApiTimeoutHeaderKey = "X-Bkapi-Timeout"

	// BkApiAllowedHeadersKey is a key to set the allowed headers in header
	BkApiAllowedHeadersKey = "X-Bkapi-Allowed-Headers"

	// BkApiMCPServerIDKey is a key to set the mcp server id in header
	BkApiMCPServerIDKey = "X-Bkapi-Mcp-Server-Id"
	// BkApiMCPServerNameKey is a key to set the mcp server name in header
	BkApiMCPServerNameKey = "X-Bkapi-Mcp-Server-Name"
)

// CtxKey ...
type CtxKey string

// BkAppCode ...
const (
	BkAppCode           CtxKey = "bk_app_code"
	BkUsername          CtxKey = "bk_username"
	BkGatewayInnerJWT   CtxKey = "bk_api_inner_jwt"
	MCPServerID         CtxKey = "mcp_server_id"
	MCPServerName       CtxKey = "mcp_server_name"
	GatewayID           CtxKey = "gateway_id"
	BkApiTimeout        CtxKey = "bk_api_timeout"
	BkApiAllowedHeaders CtxKey = "bk_api_allowed_headers"
)

// BkVirtualAppCodeFormat ...
const BkVirtualAppCodeFormat = "v_mcp_%d_%s" // 格式 v_mcp_%d_%s 【mcp 代表虚拟app_code 的类型】

type ProtocolType string

const (
	ProtocolTypeSSE            ProtocolType = "sse"
	ProtocolTypeStreamableHTTP ProtocolType = "streamable_http"
)
