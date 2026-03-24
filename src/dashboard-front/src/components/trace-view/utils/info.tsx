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

import { isArray, isNull, isObjectLike, isString, isUndefined, mergeWith } from 'lodash-es';

import type { ITraceTree } from '@/components/trace-view/typings/trace';

// 定义明确的函数类型，替代不安全的 Function
type AnyFunction = (...args: any[]) => any;

export const typeTools = {
  isArray,
  isObject: isObjectLike, // 等价纯对象判断
  isNumber: (val: unknown): val is number => typeof val === 'number' && !isNaN(val),
  isString,
  isFunction: (val: unknown): val is AnyFunction => typeof val === 'function',
  isBoolean: (val: unknown): val is boolean => typeof val === 'boolean',
  isNull: (val: unknown): val is null => isNull(val),
  isUndefined: (val: unknown): val is undefined => isUndefined(val),
  isNotNull: function <T>(val: T): val is NonNullable<T> {
    return !isNull(val) && !isUndefined(val);
  },
};

/**
 * @desc 插入跨应用 span 合并 trace_tree
 * @param { ITraceTree } originTree
 * @param { ITraceTree } newTree
 * @returns { ITraceTree }
 */
export const mergeTraceTree = <T extends ITraceTree>(originTree: T, newTree: Partial<T>): T => {
  return mergeWith({}, originTree, newTree, (originVal, newVal) => {
    if (isArray(originVal)) {
      return [...originVal, ...(isArray(newVal) ? newVal : [])];
    }
    // 对象 → 继续深度合并
    if (isObjectLike(originVal)) {
      return undefined;
    }
    // 字符串/基础类型 → 保留原始值
    return originVal;
  });
};
