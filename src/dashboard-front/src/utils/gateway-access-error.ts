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

import type { RouteLocationRaw, Router } from 'vue-router';

interface IGatewayRequestError {
  code?: string | number
  error?: { code?: string | number }
  response?: {
    status?: number
    data?: { error?: { code?: string | number } }
  }
}

export function getGatewayErrorRoute(error: unknown, gatewayId: number, retryPath: string): RouteLocationRaw {
  // 统一 HTTP 层通常抛出响应 body，也兼容保留 response 的 RequestError。
  // 不根据 message 文案推断权限；网络、5xx、协议异常等未知失败都提供重试。
  const failure = error as IGatewayRequestError | null;
  const code = failure?.error?.code ?? failure?.response?.data?.error?.code ?? failure?.code;
  const denied = [403, 404].includes(failure?.response?.status ?? Number(code))
    || code === 'NO_PERMISSION' || code === 'NOT_FOUND';
  return {
    name: denied ? 'GatewayNotFound' : 'GatewayLoadError',
    params: { id: gatewayId },
    ...(denied ? {} : { query: { retry: retryPath } }),
    replace: true,
  };
}

export function getGatewayRetryRoute(router: Router, gatewayId: number, retry: unknown): RouteLocationRaw {
  // query 可被手工修改，只允许重试当前网关的业务路由，不能跳去外部地址或递归进入错误页。
  if (typeof retry === 'string' && retry.startsWith('/') && !retry.startsWith('//')) {
    const target = router.resolve(retry);
    if (Number(target.params.id) === gatewayId
      && target.matched.some(record => record.name === 'Resources')
      && !target.meta.skipRoleCheck && target.name !== undefined) {
      return target.fullPath;
    }
  }
  return {
    name: 'BasicInfo',
    params: { id: gatewayId },
  };
}
