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

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { resolveDatePickerRange } from '@/utils/date-picker-range';

describe('utils/date-picker-range', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-11-24T08:00:00.000Z'));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('按当前时钟动态解析相对表达式区间', () => {
    const nowSec = Math.floor(Date.now() / 1000);
    expect(resolveDatePickerRange(['now-10m', 'now'])).toEqual([nowSec - 600, nowSec]);

    // 时钟前进后再次调用应返回新的相对区间
    vi.advanceTimersByTime(120_000);
    expect(resolveDatePickerRange(['now-10m', 'now'])).toEqual([nowSec - 480, nowSec + 120]);
  });

  it('支持解析绝对时间戳与日期文本区间', () => {
    const start = Date.parse('2026-11-24T06:00:00.000Z');
    const end = Date.parse('2026-11-24T07:00:00.000Z');
    expect(resolveDatePickerRange([start, end])).toEqual([start / 1000, end / 1000]);
  });

  it('空值或无法识别的表达式安全返回 null', () => {
    expect(resolveDatePickerRange(null)).toBeNull();
    expect(resolveDatePickerRange(undefined)).toBeNull();
    expect(resolveDatePickerRange(['invalid-expr', 'now'])).toBeNull();
  });
});
