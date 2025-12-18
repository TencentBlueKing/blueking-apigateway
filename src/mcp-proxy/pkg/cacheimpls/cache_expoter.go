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

import "github.com/TencentBlueKing/gopkg/cache/memory"

// NewRandomDuration is exported for testing
var NewRandomDuration = newRandomDuration

// Getter functions for testing

// GetGatewayIDCache ...
func GetGatewayIDCache() memory.Cache { return gatewayIDCache }

// GetGatewayNameCache ...
func GetGatewayNameCache() memory.Cache { return gatewayNameCache }

// GetStageCache ...
func GetStageCache() memory.Cache { return stageCache }

// GetMCPServerCache ...
func GetMCPServerCache() memory.Cache { return mcpServerCache }

// GetJWTInfoCache ...
func GetJWTInfoCache() memory.Cache { return jwtInfoCache }

// GetAppMCPServerPermission ...
func GetAppMCPServerPermission() memory.Cache { return appMCPServerPermission }

// Setter functions for testing

// SetGatewayIDCache ...
func SetGatewayIDCache(c memory.Cache) { gatewayIDCache = c }

// SetGatewayNameCache ...
func SetGatewayNameCache(c memory.Cache) { gatewayNameCache = c }

// SetStageCache ...
func SetStageCache(c memory.Cache) { stageCache = c }

// SetMCPServerCache ...
func SetMCPServerCache(c memory.Cache) { mcpServerCache = c }

// SetJWTInfoCache ...
func SetJWTInfoCache(c memory.Cache) { jwtInfoCache = c }

// SetAppMCPServerPermission ...
func SetAppMCPServerPermission(c memory.Cache) { appMCPServerPermission = c }

// GetMCPServerPromptCache ...
func GetMCPServerPromptCache() memory.Cache { return mcpServerPromptCache }

// SetMCPServerPromptCache ...
func SetMCPServerPromptCache(c memory.Cache) { mcpServerPromptCache = c }
