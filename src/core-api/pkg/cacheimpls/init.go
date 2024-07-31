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

package cacheimpls

import (
	"math/rand"
	"time"

	"github.com/TencentBlueKing/gopkg/cache/memory"
	"github.com/TencentBlueKing/gopkg/cache/memory/backend"
	gocache "github.com/patrickmn/go-cache"
)

func newRandomDuration(seconds int) backend.RandomExtraExpirationDurationFunc {
	return func() time.Duration {
		return time.Duration(rand.Intn(seconds*1000)) * time.Millisecond
	}
}

// NOTE: 如果 retrieve* 失败, 会cache 5s, 避免对 db 的频繁操作(并且有singleflight, 保证只有一个请求会去 db 拉数据)

var (
	// NOTE: 以下几个cache, 业务逻辑侧会保证 id/name -> obj 是确定的不会变的

	// instance_id => micro_gateway, will never change
	// TODO: 需要关注未来 micro_gateway.config中 配置修改的问题
	microGatewayCache = memory.NewCache(
		"micro_gateway",
		tracedFuncWrapper("micro_gateway", retrieveMicroGateway),
		12*time.Hour,
		newRandomDuration(30),
	)

	microGatewayCredentialsCache = memory.NewCache(
		"micro_gateway_credentials",
		tracedFuncWrapper("micro_gateway_credentials", retrieveAndVerifyMicroGatewayCredentials),
		2*time.Hour,
		newRandomDuration(30),
	)

	// gateway_id => gateway or gateway_name => gateway will never change
	gatewayCache = memory.NewCache(
		"gateway",
		tracedFuncWrapper("gateway", retrieveGatewayByName),
		2*time.Hour,
		newRandomDuration(30),
	)

	// NOTE: public_key should not be changed, if support changed, we should change the cache here
	jwtPublicKeyCache = memory.NewCache(
		"jwt_public_key",
		tracedFuncWrapper("jwt_public_key", retrieveJWTPublicKey),
		12*time.Hour,
		newRandomDuration(30),
	)

	// resource_version_id => map[resourceName]resourceID, will never change
	resourceVersionMappingCache = memory.NewCache(
		"resource_version_mapping",
		tracedFuncWrapper("resource_version_mapping", retrieveResourceVersionMapping),
		12*time.Hour,
		newRandomDuration(30),
	)

	// event_cache: gateway_id:stage_id:publish_id:step:status
	publishEventCache = gocache.New(10*time.Minute, 15*time.Minute)

	// NOTE: 权限-缓存的变更来源
	// part1: 权限本身的操作
	// 删除/新增权限, 此时 permission cache中数据不是最新
	// 1. 新增权限 (频率高)
	//    1.1 如果之前没有访问过, 立刻生效
	//    1.2 如果最近 1 分钟 访问过了(提示无权限), 1 分钟后生效
	// 2. 删除权限 (频率低)
	//    2.1 如果最近 1 分钟没有访问过, 立刻生效
	//    2.2 如果最近 1 分钟有访问过(有权限), 1分钟后生效

	// part2: 发布带来 release 的差异(会导致最终取权限的resource_id有差异)
	// 1. 发布新的release到某个stage (频率高)
	//    1.1 release 如果没有资源增删, 不会影响权限
	//    1.2 release 如果删除了资源, 资源不存在直接 404, 不会到权限判断(此时权限缓存可能还在, 1分钟)
	//    1.3 release 如果新增了资源, 原来没有访问过, 立刻生效; 原来访问过会 404, 不会到生成缓存这一步, 没有缓存, 不影响权限判断
	// 2. 更改了stageName (正常只在开发调试阶段存在, 小概率)
	//    2.1 改完, 发布, 权限不会受影响(因为stageName改了, 不会命中cache)
	//    2.2 改完, 发布, 访问, 再改回原来的名字, 再发布(小概率): 因为 5 分钟内老的stageName后的缓存中, 会导致查到release-resource_id可能有差异

	// NOTE: 接口调试页面的权限, 需要立刻生效 => how? (不能等 1 分钟)
	// 0. 每次点击调试, 会先判断是否有权限/权限是否过期, 如果无权限/过期, 会直接授权(TODO: 会改成如果还有 5 分钟就过期马上续期)
	// 1. 首次点击调试, 之前都没访问过, 无缓存, 立即生效 - 有权限
	// 2. 有效期是一天
	// 3. 过了一天, 过期了, 会重新授权, 如果过去 1 分钟没有访问过, 立即生效
	// 4. 如果过期前的 1 分钟点击过在线调试, 过期后, 因为有缓存, 会提示已过期(直到 1 分钟后捞取 db 新的数据) (小概率) => 如果 0处理了, 不会出现
	// 结论: 不处理, 后续通过某些发布订阅解决

	// NOTE: 决策:(需要约定, 并且用户需要感知到生效的延时是多久)
	// 1. 新增/删除权限, 大部分场景立即生效, 最多 1 分钟后生效
	// 2. 更改stageName发布-访问-再改回去-再发布, 最多 5 分钟生效
	// 3. 在线调试, 如果正好在过期前的 1 分钟-过期后 1 分钟, 会提示无权限(如果提前 5 分钟续期, 不会出现)

	// NOTE: 这样, apigateway-core 强依赖db, db 不可用会导致 `流量转发不可用`
	//       如果要变成弱依赖, 那么应该 `同步` 权限数据, 或者缓存时间拉长, 例如 12h, 然后通过发布订阅事件等实时更新缓存
	//       这是下一阶段的目标 => 现阶段先不搞? 还是尽快加入发布订阅?

	// stage_name => stage, may change in some cases
	stageCache = memory.NewCache(
		"stage",
		tracedFuncWrapper("stage", retrieveStageByGatewayIDStageName),
		5*time.Minute,
		newRandomDuration(30),
	)

	// 某个环境发布后, 1 分钟生效?
	// stage_id => release, may change frequently
	releaseCache = memory.NewCache(
		"release",
		tracedFuncWrapper("release", retrieveStageByGatewayIDStageID),
		1*time.Minute,
		newRandomDuration(10),
	)

	releaseHistoryCache = memory.NewCache(
		"release_history",
		tracedFuncWrapper("release_history", retrieveReleaseHistory),
		1*time.Minute,
		newRandomDuration(10),
	)

	// app_code + gateway_id => permission, may change frequently
	appGatewayPermissionCache = memory.NewCache(
		"app_gateway_permission",
		tracedFuncWrapper("app_gateway_permission", retrieveAppGatewayPermission),
		1*time.Minute,
		newRandomDuration(10),
	)
	// app_code + gateway_id + resource_id => permission , may change frequently
	appResourcePermissionCache = memory.NewCache(
		"app_resource_permission",
		tracedFuncWrapper("app_resource_permission", retrieveAppResourcePermission),
		1*time.Minute,
		newRandomDuration(10),
	)
)
