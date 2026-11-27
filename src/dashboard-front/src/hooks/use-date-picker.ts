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

/**
 * datepicker 时间选择器 hooks 适用于列表筛选（bkui DatePicker datetimerange）
 */

import dayjs from 'dayjs';
import type { Ref } from 'vue';
import { Message } from 'bkui-vue';
import type { DatePickerValueType } from 'bkui-vue/lib/date-picker/interface';
import { t as translate } from '@/locales';
import type { ITimeRangeFilter } from '@/types/common';
import {
  DATETIME_TEXT_FORMAT,
  type TimeInstant,
  toTimeRangeSeconds,
} from '@/utils/time-range';

/** 快捷项的稳定标识；页面按 ID 声明可选项与默认项，不依赖数组下标 */
export type DatePresetId
  = | 'today'
    | 'last-5m'
    | 'last-1h'
    | 'last-6h'
    | 'last-12h'
    | 'last-1d'
    | 'last-7d'
    | 'last-15d'
    | 'last-30d';

/** 快捷项配置：ID，或 ID 加页面自定义的文案 */
export type DatePresetOption = DatePresetId | {
  id: DatePresetId
  text: string
};

interface IUseDatePickerOptions {
  /** 可选的快捷项，按显示顺序 */
  presets: readonly DatePresetOption[]
  /** 默认选中的快捷项；不设置表示默认不限时间 */
  defaultPreset?: DatePresetId
}

interface IDatePreset {
  text: () => string
  // 每次调用都按当前时间计算
  getRange: () => [Date, Date]
}

const MINUTE = 60 * 1000;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;

const getRecentDates = (duration: number): [Date, Date] => {
  const end = new Date();
  return [new Date(end.getTime() - duration), end];
};

const DATE_PRESETS: Record<DatePresetId, IDatePreset> = {
  'today': {
    text: () => translate('今天'),
    getRange: () => {
      const end = new Date();
      return [new Date(end.getFullYear(), end.getMonth(), end.getDate()), end];
    },
  },
  'last-5m': {
    text: () => translate('最近 5 分钟'),
    getRange: () => getRecentDates(5 * MINUTE),
  },
  'last-1h': {
    text: () => translate('最近 1 小时'),
    getRange: () => getRecentDates(HOUR),
  },
  'last-6h': {
    text: () => translate('最近 6 小时'),
    getRange: () => getRecentDates(6 * HOUR),
  },
  'last-12h': {
    text: () => translate('最近 12 小时'),
    getRange: () => getRecentDates(12 * HOUR),
  },
  'last-1d': {
    text: () => translate('最近 1 天'),
    getRange: () => getRecentDates(DAY),
  },
  'last-7d': {
    text: () => translate('最近 7 天'),
    getRange: () => getRecentDates(7 * DAY),
  },
  'last-15d': {
    text: () => translate('近15天'),
    getRange: () => getRecentDates(15 * DAY),
  },
  'last-30d': {
    text: () => translate('近30天'),
    getRange: () => getRecentDates(30 * DAY),
  },
};

// bkui 以空数组表示未选择，但其类型声明只包含二元组，这里集中处理类型差异
const createEmptyDateValue = () => [] as unknown as DatePickerValueType;

const toDateValue = (dates: readonly (Date | number | string)[]): DatePickerValueType =>
  (dates.length >= 2 ? [dates[0], dates[1]] : createEmptyDateValue());

/** 流水日志、操作记录等列表通用的“最近 N”快捷项 */
export const RECENT_DATE_PRESETS: readonly DatePresetId[] = Object.freeze([
  'last-5m',
  'last-1h',
  'last-6h',
  'last-12h',
  'last-1d',
  'last-7d',
]);

/**
 * useDatePicker - 时间选择器的自定义钩子函数
 * @param filterData - 筛选条件，确认选择后写入 time_start/time_end
 * @param options - 页面可用的快捷项及默认项
 * @returns 快捷项、选择值及选择、确认、清空、重置等方法
 */
export const useDatePicker = (
  filterData: Ref<ITimeRangeFilter>,
  { presets, defaultPreset }: IUseDatePickerOptions,
) => {
  const { t } = useI18n(); // 获取国际化函数

  // bkui 按引用匹配当前快捷项，列表在 Hook 生命周期内保持不变
  const shortcutsRange = presets.map((option) => {
    const id = typeof option === 'string' ? option : option.id;
    const preset = DATE_PRESETS[id];
    return {
      id,
      text: typeof option === 'string' ? preset.text() : option.text,
      value: preset.getRange,
    };
  });

  const defaultShortcutIndex = defaultPreset
    ? shortcutsRange.findIndex(item => item.id === defaultPreset)
    : -1;

  const shortcutSelectedIndex = shallowRef(defaultShortcutIndex);
  // 面板选值（组件 v-model）：Date 或 'YYYY-MM-DD HH:mm:ss' 文本
  const dateValue = ref<DatePickerValueType>(createEmptyDateValue());
  // 面板默认切换值
  const selectionMode = ref('date');

  /**
   * handleChange - 处理日期变化
   * @param date - 组件 change 事件给出的日期文本
   * @param type - 触发方式，'date' 表示在日期面板中点选
   */
  const handleChange = (date: string[], type: string) => {
    const dates = date ?? [];
    // 直接在输入框中修改时间时，组件只触发 change、不触发 shortcut-change，需要在这里退出快捷项；
    // 点选快捷项时 type 为 'shortcut'，清空时没有选值，这两种情况保持原有的快捷项下标
    if (type !== 'shortcut' && dates[0]) {
      shortcutSelectedIndex.value = -1;
    }
    // 在日期面板中直接点选日期时按整天处理：开始时间归零（结束时间已由组件设为 23:59:59）。
    // 在时间面板中调整或选择快捷项时保留所选时刻
    const isWholeDayPick = Boolean(dates[0])
      && ['date'].includes(type)
      && ['date', 'datetimerange'].includes(selectionMode.value)
      && shortcutSelectedIndex.value === -1;

    if (!isWholeDayPick) {
      dateValue.value = toDateValue(dates);
      return;
    }

    const dayStart = dayjs(dates[0]).startOf('day')
      .format(DATETIME_TEXT_FORMAT);
    dateValue.value = toDateValue([dayStart, dates[1]]);
  };

  /**
   * 当前选择对应的时刻：快捷项按当前时间重新计算，否则使用面板选值
   */
  const getSelectedDates = (): TimeInstant[] => {
    const shortcut = shortcutsRange[shortcutSelectedIndex.value];
    if (shortcut) {
      return shortcut.value();
    }
    return Array.isArray(dateValue.value) ? dateValue.value : [];
  };

  /**
   * applySelectedRange - 按当前时间解析选择并写入筛选条件
   * - 未选择：清空时间条件
   * - 无法得到有效区间（解析失败、只有一端、起点晚于终点）：提示错误，保留原有时间条件
   * @returns 时间条件是否有效；无效时调用方不应发起查询
   */
  const applySelectedRange = () => {
    const [start, end] = getSelectedDates();
    if (!start && !end) {
      filterData.value.time_start = '';
      filterData.value.time_end = '';
      return true;
    }

    const range = toTimeRangeSeconds(start, end);
    if (!range) {
      Message({
        theme: 'error',
        message: t('时间范围无效，请重新选择'),
      });
      return false;
    }

    [filterData.value.time_start, filterData.value.time_end] = range;
    return true;
  };

  /**
   * resetSelection - 恢复默认选择，不修改筛选条件
   * 页面通常随后重建日期组件，并重新查询
   */
  const resetSelection = () => {
    dateValue.value = createEmptyDateValue();
    shortcutSelectedIndex.value = defaultShortcutIndex;
    selectionMode.value = 'date';
  };

  /**
   * handleClear - 清除日期
   */
  const handleClear = () => {
    resetSelection();
    applySelectedRange();
  };

  /**
   * handleConfirm - 确认日期
   * @returns 时间条件是否有效；无效时调用方不应发起查询
   */
  const handleConfirm = () => {
    selectionMode.value = 'date';
    return applySelectedRange();
  };

  // 切换面板事件
  const handleSelectionModeChange = (value: string) => {
    selectionMode.value = value;
  };

  // 快捷项改变事件
  const handleShortcutChange = (
    _value: {
      text: string
      value: () => void
    },
    index: number,
  ) => {
    shortcutSelectedIndex.value = index;
  };

  return {
    dateValue,
    shortcutsRange,
    shortcutSelectedIndex,
    handleChange,
    handleClear,
    handleConfirm,
    handleSelectionModeChange,
    handleShortcutChange,
    applySelectedRange,
    resetSelection,
  };
};
