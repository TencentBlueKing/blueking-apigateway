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

import { describe, expect, it } from 'vitest';
import { inferJsonSchema } from '@/utils/inferJsonSchema';

describe('utils/inferJsonSchema', () => {
  it('推断基础原始类型并对无法识别的值抛出异常', () => {
    expect(inferJsonSchema(42)).toEqual({ type: 'integer' });
    expect(inferJsonSchema(3.14)).toEqual({ type: 'number' });
    expect(inferJsonSchema('hello')).toEqual({ type: 'string' });
    expect(inferJsonSchema(true)).toEqual({ type: 'boolean' });
    expect(inferJsonSchema(null)).toEqual({ type: 'null' });

    expect(() => inferJsonSchema(undefined)).toThrow('Type of value couldn\'t be determined');
    expect(() => inferJsonSchema(Number.NaN)).toThrow();
    expect(() => inferJsonSchema(Number.POSITIVE_INFINITY)).toThrow();
    expect(() => inferJsonSchema(new Date())).toThrow();
  });

  it('识别常用字符串 format，并支持通过 detectFormat: false 关闭', () => {
    expect(inferJsonSchema('2026-11-24T10:30:00Z')).toEqual({
      type: 'string',
      format: 'date-time',
    });
    expect(inferJsonSchema('2026-11-24')).toEqual({
      type: 'string',
      format: 'date',
    });
    expect(inferJsonSchema('10:30:00')).toEqual({
      type: 'string',
      format: 'time',
    });
    expect(inferJsonSchema('dev.user+tag@example.com')).toEqual({
      type: 'string',
      format: 'email',
    });
    expect(inferJsonSchema('192.168.1.1')).toEqual({
      type: 'string',
      format: 'ipv4',
    });
    expect(inferJsonSchema('2001:db8::1')).toEqual({
      type: 'string',
      format: 'ipv6',
    });
    expect(inferJsonSchema('https://example.com/api/v1?a=1')).toEqual({
      type: 'string',
      format: 'uri',
    });

    expect(inferJsonSchema('dev@example.com', { detectFormat: false })).toEqual({ type: 'string' });
  });

  it('在长点号分隔字符串上不会触发邮箱正则灾难性回溯', () => {
    const start = performance.now();
    const result = inferJsonSchema(`${'a.'.repeat(35)}!`);
    expect(result).toEqual({ type: 'string' });
    expect(performance.now() - start).toBeLessThan(200);
  });

  it('推断空对象与嵌套对象结构', () => {
    expect(inferJsonSchema({})).toEqual({ type: 'object' });
    expect(inferJsonSchema({
      id: 1,
      score: 99.5,
      meta: { active: true },
    })).toEqual({
      type: 'object',
      properties: {
        id: { type: 'integer' },
        score: { type: 'number' },
        meta: {
          type: 'object',
          properties: {
            active: { type: 'boolean' },
          },
        },
      },
    });
  });

  it('合并同构数组元素，并将 integer 与 number 混合提升为 number', () => {
    expect(inferJsonSchema([])).toEqual({ type: 'array' });
    expect(inferJsonSchema([1, 2, 3])).toEqual({
      type: 'array',
      items: { type: 'integer' },
    });
    expect(inferJsonSchema([1, 2.5, 3])).toEqual({
      type: 'array',
      items: { type: 'number' },
    });
    // 键集合一致但顺序不同的对象仍能合并出完整 properties
    expect(inferJsonSchema([
      {
        a: 1,
        b: 'x',
      },
      {
        b: 'y',
        a: 2.5,
      },
    ])).toEqual({
      type: 'array',
      items: {
        type: 'object',
        properties: {
          a: { type: 'number' },
          b: { type: 'string' },
        },
      },
    });
  });

  it('处理异构数组、对象键不一致及空/非空嵌套数组的退化规则', () => {
    // 混合完全不同的基础类型时不生成 items
    expect(inferJsonSchema([1, 'two'])).toEqual({ type: 'array' });

    // 对象属性键集合不一致时退化为 { type: 'object' }
    expect(inferJsonSchema([{ a: 1 }, { b: 2 }])).toEqual({
      type: 'array',
      items: { type: 'object' },
    });

    // 字符串数组包含不同 format 时退化为 { type: 'string' }
    expect(inferJsonSchema(['192.168.0.1', 'plain-text'])).toEqual({
      type: 'array',
      items: { type: 'string' },
    });

    // 嵌套数组中一个为空数组、一个带元素时，合并省略内层 items
    expect(inferJsonSchema([[], [1, 2]])).toEqual({
      type: 'array',
      items: { type: 'array' },
    });

    // 嵌套数组元素类型互斥时，同样退化为只声明内层为 array
    expect(inferJsonSchema([[1], ['a']])).toEqual({
      type: 'array',
      items: { type: 'array' },
    });
  });
});
