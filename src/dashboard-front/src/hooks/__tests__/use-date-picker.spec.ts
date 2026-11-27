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

import { ref } from 'vue';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { ITimeRangeFilter } from '@/types/common';

const { bkMessageMock } = vi.hoisted(() => ({ bkMessageMock: vi.fn() }));

vi.mock('bkui-vue', () => ({ Message: bkMessageMock }));
vi.mock('vue-i18n', () => ({ useI18n: () => ({ t: (key: string) => key }) }));
vi.mock('@/locales', () => ({ t: (key: string) => key }));

import { RECENT_DATE_PRESETS, useDatePicker } from '@/hooks/use-date-picker';

describe('hooks/use-date-picker', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-11-24T10:00:00.000Z'));
    bkMessageMock.mockReset();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('按预设 ID 与自定义文案构建快捷项，并在每次 applySelectedRange 时按当前时间重算', () => {
    const filter = ref<ITimeRangeFilter>({
      time_start: '',
      time_end: '',
    });

    const picker = useDatePicker(filter, {
      presets: [
        ...RECENT_DATE_PRESETS,
        {
          id: 'today',
          text: '自定义今天',
        },
      ],
      defaultPreset: 'last-1h',
    });

    expect(picker.shortcutsRange).toHaveLength(7);
    expect(picker.shortcutsRange[6].text).toBe('自定义今天');
    expect(picker.shortcutSelectedIndex.value).toBe(1);

    const nowSec = Math.floor(Date.now() / 1000);
    expect(picker.applySelectedRange()).toBe(true);
    expect(filter.value).toEqual({
      time_start: nowSec - 3600,
      time_end: nowSec,
    });

    // 推进 5 分钟后再次应用，相对时间区间同步推进
    vi.advanceTimersByTime(5 * 60 * 1000);
    expect(picker.applySelectedRange()).toBe(true);
    expect(filter.value).toEqual({
      time_start: nowSec - 3600 + 300,
      time_end: nowSec + 300,
    });
  });

  it('日期面板点选日期时起点归零且退出快捷项，时间面板调整则保留原时刻', () => {
    const filter = ref<ITimeRangeFilter>({
      time_start: '',
      time_end: '',
    });
    const picker = useDatePicker(filter, {
      presets: ['last-5m', 'last-1h'],
      defaultPreset: 'last-5m',
    });

    // 在日期面板直接选择日期，应退出快捷项并将开始时间归零到 00:00:00
    picker.handleChange(['2026-11-20 14:30:00', '2026-11-24 23:59:59'], 'date');
    expect(picker.shortcutSelectedIndex.value).toBe(-1);
    expect(picker.dateValue.value).toEqual(['2026-11-20 00:00:00', '2026-11-24 23:59:59']);

    // 切换到时间面板后修改时刻，保留具体时分秒
    picker.handleSelectionModeChange('time');
    picker.handleChange(['2026-11-20 09:15:30', '2026-11-24 18:45:00'], 'date');
    expect(picker.dateValue.value).toEqual(['2026-11-20 09:15:30', '2026-11-24 18:45:00']);

    expect(picker.handleConfirm()).toBe(true);
    expect(typeof filter.value.time_start).toBe('number');
    expect(typeof filter.value.time_end).toBe('number');
    expect(Number(filter.value.time_end) > Number(filter.value.time_start)).toBe(true);
  });

  it('选择快捷项保持下标；非法区间提示错误、返回 false 且不破坏原筛选值', () => {
    const filter = ref<ITimeRangeFilter>({
      time_start: 1000,
      time_end: 2000,
    });
    const picker = useDatePicker(filter, { presets: ['last-5m', 'last-1h'] });

    picker.handleShortcutChange({
      text: '最近 1 小时',
      value: () => undefined,
    }, 1);
    picker.handleChange(['2026-11-24 09:00:00', '2026-11-24 10:00:00'], 'shortcut');
    expect(picker.shortcutSelectedIndex.value).toBe(1);

    // 手动输入倒置区间（起点晚于终点）
    picker.handleChange(['2026-11-25 10:00:00', '2026-11-24 10:00:00'], 'input');
    expect(picker.shortcutSelectedIndex.value).toBe(-1);
    expect(picker.applySelectedRange()).toBe(false);
    expect(bkMessageMock).toHaveBeenCalledWith({
      theme: 'error',
      message: '时间范围无效，请重新选择',
    });
    // 保留原有有效筛选条件
    expect(filter.value).toEqual({
      time_start: 1000,
      time_end: 2000,
    });
  });

  it('resetSelection 仅还原选择状态，handleClear 同时清空或回填默认筛选条件', () => {
    const filter = ref<ITimeRangeFilter>({
      time_start: 1000,
      time_end: 2000,
    });
    const picker = useDatePicker(filter, { presets: ['last-5m'] });

    picker.handleChange(['2026-11-20 00:00:00', '2026-11-24 23:59:59'], 'date');
    picker.resetSelection();
    expect(picker.dateValue.value).toEqual([]);
    // resetSelection 不直接改写 filterData
    expect(filter.value).toEqual({
      time_start: 1000,
      time_end: 2000,
    });

    picker.handleClear();
    expect(filter.value).toEqual({
      time_start: '',
      time_end: '',
    });
  });
});
