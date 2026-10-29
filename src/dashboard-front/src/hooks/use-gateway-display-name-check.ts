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

import {
  checkDisplayNameAvailable,
  checkDisplayNameAvailableForUpdate,
} from '@/services/source/gateway';

interface IDisplayNameCheckOptions {
  // 编辑场景传入网关 ID，用于排除自身
  gatewayId?: () => number | undefined
  // 表单中的网关 ID，展示名为空时用于兜底查重
  gatewayName: () => string | undefined
  // 表单中的展示名
  displayName: () => string | undefined
}

// 同一目标（网关 + 名称）的查重结果短暂复用，避免输入框失焦与提交校验重复请求
const CHECK_CACHE_TTL = 3_000;

interface IPendingCheck {
  key: string
  promise: Promise<boolean>
}

interface ICachedCheck {
  key: string
  isAvailable: boolean
  expiresAt: number
}

export function useGatewayDisplayNameCheck({
  gatewayId,
  gatewayName,
  displayName,
}: IDisplayNameCheckOptions) {
  // 只采用最后一次发起的查重结果，忽略输入变化前发出的旧请求
  let requestSeq = 0;
  // 在途请求：目标相同时复用同一个 Promise
  let pendingCheck: IPendingCheck | null = null;
  // 最近一次结果：失焦校验与提交校验几乎同时触发，直接复用结果
  let cachedCheck: ICachedCheck | null = null;
  // 最新一次查重（含在途）：过期请求需要等它的结论，避免写回相反的判定
  let latestCheck: Promise<boolean> | null = null;

  const requestDisplayNameCheck = async (id: number | undefined, target: string, key: string) => {
    const seq = ++requestSeq;
    let isAvailable = true;
    let isFailed = false;
    try {
      const result = id
        ? await checkDisplayNameAvailableForUpdate(id, target)
        : await checkDisplayNameAvailable(target);
      isAvailable = Boolean(result?.is_available);
    }
    catch {
      // 查重未完成不能当作名称可用，但不阻塞提交，最终由保存接口兜底
      isFailed = true;
    }

    // 期间又发起了新的查重：本次结果（无论成功或失败）已过期。
    // 必须返回最新一次的结论，不能直接返回“可用”，否则会覆盖更新的“已被使用”判定
    if (seq !== requestSeq) {
      return latestCheck ? await latestCheck : true;
    }

    // 仅缓存成功查询的结果，失败不缓存，避免短时间内把异常结论当作可用
    if (!isFailed) {
      cachedCheck = {
        key,
        isAvailable,
        expiresAt: Date.now() + CHECK_CACHE_TTL,
      };
    }

    return isAvailable;
  };

  const checkDisplayName = (): Promise<boolean> => {
    // 展示名为空时用网关 ID 兜底查重：其他网关可能已将该值作为展示名
    const target = (displayName() ?? '').trim() || (gatewayName() ?? '').trim();
    if (!target) return Promise.resolve(true);

    const id = gatewayId?.();
    const key = `${id ?? 'create'}::${target}`;

    if (cachedCheck?.key === key && Date.now() < cachedCheck.expiresAt) {
      return Promise.resolve(cachedCheck.isAvailable);
    }

    if (pendingCheck?.key === key) {
      return pendingCheck.promise;
    }

    let promise: Promise<boolean> = Promise.resolve(true);

    promise = requestDisplayNameCheck(id, target, key).finally(() => {
      if (pendingCheck?.promise === promise) {
        pendingCheck = null;
      }
    });

    pendingCheck = {
      key,
      promise,
    };

    latestCheck = promise;

    return promise;
  };

  return { checkDisplayName };
}
