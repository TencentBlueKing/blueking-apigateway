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

package cacheimpls

import (
	"math/rand"
	"time"

	"github.com/TencentBlueKing/gopkg/cache/memory"
	"github.com/TencentBlueKing/gopkg/cache/memory/backend"
)

func newRandomDuration(seconds int) backend.RandomExtraExpirationDurationFunc {
	return func() time.Duration {
		return time.Duration(rand.Intn(seconds*1000)) * time.Millisecond
	}
}

var (

	// gateway_id => gateway
	gatewayIDCache = memory.NewCache(
		"gateway_id",
		tracedFuncWrapper("gateway_id", retrieveGatewayByID),
		12*time.Hour,
		newRandomDuration(30),
	)

	// gateway_name => gateway
	gatewayNameCache = memory.NewCache(
		"gateway_name",
		tracedFuncWrapper("gateway_name", retrieveGatewayByName),
		12*time.Hour,
		newRandomDuration(30),
	)

	stageCache = memory.NewCache(
		"stage",
		tracedFuncWrapper("stage", retrieveStageByID),
		12*time.Hour,
		newRandomDuration(30),
	)

	// mcp server cache
	mcpServerCache = memory.NewCache(
		"mcp_server",
		tracedFuncWrapper("mcp_server", retrieveMCPServerByName),
		12*time.Hour,
		newRandomDuration(30),
	)

	// NOTE: public_info should not be changed, if support changed, we should change the cache here
	jwtInfoCache = memory.NewCache(
		"jwt_info",
		tracedFuncWrapper("jwt_info", retrieveJWTInfo),
		12*time.Hour,
		newRandomDuration(30),
	)

	// app_code + mcp_server_id => permission, may change frequently
	appMCPServerPermission = memory.NewCache(
		"app_mcp_server_permission",
		tracedFuncWrapper("app_mcp_server_permission", retrieveMCPServerPermission),
		1*time.Minute,
		newRandomDuration(10),
	)

	// mcp_server_id => mcp_server_extend (prompts), may change frequently
	mcpServerPromptCache = memory.NewCache(
		"mcp_server_prompt",
		tracedFuncWrapper("mcp_server_prompt", retrieveMCPServerPromptByMcpServerID),
		1*time.Minute,
		newRandomDuration(10),
	)
)
