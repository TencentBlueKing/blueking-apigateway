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

import dayjs from 'dayjs';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { getUtcTimeAgo, setupDayjsLocale } from '@/utils/dayUtc';
import { getDuplicateKeys } from '@/utils/duplicateKeys';
import { filterSimpleEmpty } from '@/utils/filterEmptyValues';
import { getLoginURL } from '@/utils/getLoginURL';
import { getSearchSelectorParams } from '@/utils/getSearchSelectorParams';
import { isAfter24h } from '@/utils/isAfter24h';
import { sortByKey } from '@/utils/sortByKey';
import { timeFormatter } from '@/utils/timeFormatter';
import { buildURLParams, parseURL } from '@/utils/url';

describe('utils/common-helpers', () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  describe('filterSimpleEmpty', () => {
    it('过滤 null、undefined、NaN、空串、空数组与空对象，保留 0、false 和非空值', () => {
      expect(filterSimpleEmpty({
        a: null,
        b: undefined,
        c: Number.NaN,
        d: '',
        e: [],
        f: {},
        g: 0,
        h: false,
        i: 'ok',
        j: [1],
        k: { nested: true },
      })).toEqual({
        g: 0,
        h: false,
        i: 'ok',
        j: [1],
        k: { nested: true },
      });
    });
  });

  describe('getDuplicateKeys', () => {
    it('找出数组中指定字段的重复值，忽略空值和非对象元素', () => {
      const rows = [
        { name: 'alpha' },
        { name: '' },
        { name: null },
        { name: undefined },
        null,
        'invalid',
        { name: 'beta' },
        { name: 'alpha' },
        { name: 'alpha' },
        { name: '' },
        { name: 'beta' },
      ];
      expect(getDuplicateKeys(rows, 'name')).toEqual(['alpha', 'beta']);
      expect(getDuplicateKeys([], 'name')).toEqual([]);
      expect(getDuplicateKeys([{ name: 'only' }], 'name')).toEqual([]);
      expect(getDuplicateKeys(rows, '')).toEqual([]);
    });
  });

  describe('sortByKey', () => {
    it('按指定字符串键忽略大小写升序排序并保留同键项', () => {
      const items = [
        { name: 'Charlie' },
        { name: 'alpha' },
        { name: 'Beta' },
        { name: 'Alpha' },
      ];
      expect(sortByKey(items, 'name')).toEqual([
        { name: 'alpha' },
        { name: 'Alpha' },
        { name: 'Beta' },
        { name: 'Charlie' },
      ]);
    });
  });

  describe('getSearchSelectorParams', () => {
    it('将搜索框选择项聚合为逗号分隔参数对象并去除首尾空格', () => {
      const params = getSearchSelectorParams<{
        status: string
        keyword: string
      }>([
        {
          id: 'status',
          name: '状态',
          values: [
            {
              id: ' active ',
              name: '启用',
            },
            {
              id: 'inactive',
              name: '停用',
            },
          ],
        },
        {
          id: 'keyword',
          name: '关键词',
          values: [{
            id: ' demo ',
            name: 'demo',
          }],
        },
      ]);

      expect(params).toEqual({
        status: 'active,inactive',
        keyword: 'demo',
      });
    });
  });

  describe('parseURL & buildURLParams & getLoginURL', () => {
    it('正确解析 URL 各组成部分并规范尾部斜杠', () => {
      const parsed = parseURL('https://apigw.example.com:8443/api/v1?foo=1&bar=2#section');
      expect(parsed).toEqual({
        source: 'https://apigw.example.com:8443/api/v1?foo=1&bar=2#section',
        protocol: 'https',
        host: 'apigw.example.com',
        pathname: '/api/v1/',
        port: '8443',
        search: 'foo=1&bar=2',
        hash: 'section',
        origin: 'https://apigw.example.com:8443',
      });
    });

    it('正确序列化普通键值、数组、Date、嵌套对象并跳过空值', () => {
      const date = new Date('2026-11-24T00:00:00.000Z');
      expect(buildURLParams(null)).toBe('');
      expect(buildURLParams({
        name: 'hello world',
        tags: ['a', 'b'],
        at: date,
        meta: { x: 1 },
        skipNull: null,
        skipUndef: undefined,
      })).toBe(
        'name=hello+world&tags[]=a&tags[]=b&at=2026-11-24T00:00:00.000Z&meta=%7B%22x%22:1%7D',
      );
    });

    it('getLoginURL 正确追加 size、is_from_logout 和 c_url 参数', () => {
      const result = getLoginURL('https://login.example.com/plain/', 'https://apigw.example.com/home', 'small');
      const url = new URL(result);
      expect(url.searchParams.get('size')).toBe('small');
      expect(url.searchParams.get('is_from_logout')).toBe('1');
      expect(url.searchParams.get('c_url')).toBe('https://apigw.example.com/home');
    });
  });

  describe('isAfter24h & timeFormatter & dayUtc', () => {
    it('isAfter24h 准确判断距离当前时间是否满 24 小时', () => {
      vi.useFakeTimers();
      vi.setSystemTime(new Date('2026-11-24T12:00:00.000Z'));

      expect(isAfter24h('2026-11-23T12:00:00.000Z')).toBe(true);
      expect(isAfter24h('2026-11-23T12:00:01.000Z')).toBe(false);
    });

    it('timeFormatter 对空值返回 -- 并支持自定义格式', () => {
      expect(timeFormatter('')).toBe('--');
      expect(timeFormatter('2026-11-24 10:20:30', 'YYYY/MM/DD')).toBe('2026/11/24');
    });

    it('setupDayjsLocale 覆盖相对时间的同时保留月份与星期配置，且 getUtcTimeAgo 安全处理无效输入', () => {
      vi.useFakeTimers();
      vi.setSystemTime(new Date('2026-11-24T12:00:00.000Z'));

      setupDayjsLocale('en');
      expect(dayjs('2026-11-24').format('MMMM')).toBe('November');

      setupDayjsLocale('unsupported-lang');
      expect(dayjs.locale()).toBe('zh-cn');
      expect(dayjs('2026-11-24').format('MMMM')).toBe('十一月');

      expect(getUtcTimeAgo('')).toBe('');
      expect(getUtcTimeAgo('not-a-date')).toBe('');
      expect(getUtcTimeAgo('2026-11-24T11:55:00.000Z')).toContain('5');
    });
  });
});
