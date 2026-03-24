/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2026 Tencent. All rights reserved.
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

import _get from 'lodash-es/get';

import defaultConfig, { deprecations } from '../../constants/default-config';
import processDeprecation from './process-deprecation';

// 扩展 window 全局类型
declare global {
  interface Window { getJaegerUiConfig?: () => Record<string, any> | undefined | null }
}

let haveWarnedFactoryFn = false;
let haveWarnedDeprecations = false;

/**
 * 手动实现 memoize-one：仅缓存最后一次调用的结果
 */
function memoizeOne<F extends (...args: any[]) => any>(func: F): F {
  let lastArgs: any[] | null = null;
  let lastResult: any;

  const isShallowEqual = (newArgs: any[], oldArgs: any[]): boolean => {
    if (newArgs.length !== oldArgs.length) {
      return false;
    }
    for (let i = 0; i < newArgs.length; i++) {
      if (newArgs[i] !== oldArgs[i]) {
        return false;
      }
    }
    return true;
  };

  return ((...newArgs: any[]) => {
    if (lastArgs === null || !isShallowEqual(newArgs, lastArgs)) {
      lastResult = func(...newArgs);
      lastArgs = newArgs;
    }
    return lastResult;
  }) as F;
}

// 配置类型（与 defaultConfig 结构保持一致）
type AppConfig = typeof defaultConfig & Record<string, any>;

const getConfig = memoizeOne((): AppConfig => {
  const { getJaegerUiConfig } = window;

  if (typeof getJaegerUiConfig !== 'function') {
    if (!haveWarnedFactoryFn) {
      haveWarnedFactoryFn = true;
    }
    return { ...defaultConfig };
  }

  const embedded = getJaegerUiConfig();
  if (!embedded) {
    return { ...defaultConfig };
  }

  // 处理废弃配置
  if (Array.isArray(deprecations)) {
    deprecations.forEach(dep => processDeprecation(embedded, dep, !haveWarnedDeprecations));
    haveWarnedDeprecations = true;
  }

  const rv = {
    ...defaultConfig,
    ...embedded,
  } as AppConfig;

  // 合并 __mergeFields
  const keys = ((defaultConfig as any).__mergeFields || []) as (keyof AppConfig)[];
  for (let i = 0; i < keys.length; i++) {
    const key = keys[i];
    if (typeof (embedded as any)[key] === 'object' && (embedded as any)[key] !== null) {
      rv[key] = {
        ...(defaultConfig as any)[key],
        ...(embedded as any)[key],
      };
    }
  }

  return rv;
});

export default getConfig;

export function getConfigValue<T = any>(path: string): T {
  return _get(getConfig(), path);
}
