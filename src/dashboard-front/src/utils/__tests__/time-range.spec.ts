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
import { describe, expect, it } from 'vitest';
import {
  DATETIME_TEXT_FORMAT,
  floorToUtcDay,
  getBucketRange,
  getRecentRange,
  intersectTimeRange,
  toEpochSeconds,
  toTimeRangeQuery,
  toTimeRangeSeconds,
} from '@/utils/time-range';

describe('utils/time-range', () => {
  describe('toEpochSeconds', () => {
    it('支持 Date、Dayjs、毫秒数与固定格式日期字符串并向下取整为秒', () => {
      const date = new Date(1700000000999);
      const day = dayjs(1700000000999);
      const text = day.format(DATETIME_TEXT_FORMAT);

      expect(toEpochSeconds(date)).toBe(1700000000);
      expect(toEpochSeconds(day)).toBe(1700000000);
      expect(toEpochSeconds(1700000000999)).toBe(1700000000);
      expect(toEpochSeconds(text)).toBe(1700000000);
      expect(toEpochSeconds(0)).toBe(0);
    });

    it('遇到空值、负时间戳或非标准文本时返回 null', () => {
      expect(toEpochSeconds(null)).toBeNull();
      expect(toEpochSeconds(undefined)).toBeNull();
      expect(toEpochSeconds('')).toBeNull();
      expect(toEpochSeconds(-1)).toBeNull();
      expect(toEpochSeconds(Number.NaN)).toBeNull();
      expect(toEpochSeconds(Number.POSITIVE_INFINITY)).toBeNull();
      expect(toEpochSeconds('2026/11/24 10:00:00')).toBeNull();
      expect(toEpochSeconds('2026-02-30 10:00:00')).toBeNull();
    });
  });

  describe('toTimeRangeSeconds', () => {
    it('返回合法的秒级区间并允许起止相等', () => {
      expect(toTimeRangeSeconds(1000, 2500)).toEqual([1, 2]);
      expect(toTimeRangeSeconds(2000, 2999)).toEqual([2, 2]);
    });

    it('任一端无效或起点晚于终点时返回 null', () => {
      expect(toTimeRangeSeconds(3000, 2000)).toBeNull();
      expect(toTimeRangeSeconds(null, 2000)).toBeNull();
      expect(toTimeRangeSeconds(1000, '')).toBeNull();
    });
  });

  describe('getRecentRange', () => {
    it('以给定终点向前计算指定时长区间', () => {
      const now = dayjs.unix(1700003600);
      expect(getRecentRange(1, 'hour', now)).toEqual([1700000000, 1700003600]);
    });
  });

  describe('toTimeRangeQuery', () => {
    it('双端均为数字时成对返回查询参数，否则返回空对象', () => {
      expect(toTimeRangeQuery({
        time_start: 100,
        time_end: 200,
      })).toEqual({
        time_start: 100,
        time_end: 200,
      });

      expect(toTimeRangeQuery({
        time_start: 100,
        time_end: '',
      })).toEqual({});

      expect(toTimeRangeQuery({
        time_start: '',
        time_end: '',
      })).toEqual({});
    });
  });

  describe('floorToUtcDay & intersectTimeRange', () => {
    it('正确对齐到 UTC 零点并计算区间交集', () => {
      expect(floorToUtcDay(86400 * 10 + 12345)).toBe(86400 * 10);
      expect(intersectTimeRange([10, 50], [20, 40])).toEqual([20, 40]);
      expect(intersectTimeRange([10, 20], [20, 30])).toEqual([20, 20]);
      expect(intersectTimeRange([10, 19], [20, 30])).toBeNull();
    });
  });

  describe('getBucketRange', () => {
    const timeline = [1000, 1060, 1120, 1180];

    it('按桶宽计算闭区间，支持反向框选与越界裁剪', () => {
      expect(getBucketRange(timeline, 1, 2)).toEqual([1060, 1179]);
      expect(getBucketRange(timeline, 2, 1)).toEqual([1060, 1179]);
      expect(getBucketRange(timeline, -2, 10)).toEqual([1000, 1239]);
    });

    it('提供查询窗口时与窗口取交集，且支持单桶回退到查询窗口终点', () => {
      expect(getBucketRange(timeline, 0, 3, [1015, 1200])).toEqual([1015, 1200]);
      expect(getBucketRange([1000], 0, 0, [1000, 1045])).toEqual([1000, 1045]);
      expect(getBucketRange([1000], 0, 0)).toEqual([1000, 1000]);
    });

    it('空时间轴、非整数下标或与查询窗口无交集时返回 null', () => {
      expect(getBucketRange([], 0, 0)).toBeNull();
      expect(getBucketRange(timeline, 0.5, 1)).toBeNull();
      expect(getBucketRange(timeline, 0, 1, [2000, 2100])).toBeNull();
    });
  });
});
