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
 * 查询用时间范围的转换与校验
 *
 * 后端时间参数统一为 Unix 整数秒：非负整数，起止成对，且起点不晚于终点。
 */

import dayjs, { type Dayjs, type ManipulateType } from 'dayjs';
import customParseFormat from 'dayjs/plugin/customParseFormat';
import type { ITimeRangeFilter } from '@/types/common';

dayjs.extend(customParseFormat);

/** Unix 整数秒 */
export type EpochSeconds = number;

/** 起止均有效、起点不晚于终点的秒级区间 */
export type TimeRangeSeconds = readonly [EpochSeconds, EpochSeconds];

/**
 * 绝对时刻
 * - number：毫秒时间戳
 * - string：仅接受 DATETIME_TEXT_FORMAT 格式（bkui DatePicker change 事件的输出）
 */
export type TimeInstant = Dayjs | Date | number | string;

/** bkui DatePicker 与列表页日期 Hook 使用的日期时间文本格式 */
export const DATETIME_TEXT_FORMAT = 'YYYY-MM-DD HH:mm:ss';

const toMilliseconds = (value: TimeInstant) => {
  if (typeof value === 'string') {
    // 按固定格式严格解析，不依赖浏览器对非 ISO 文本的 Date 解析
    return dayjs(value, DATETIME_TEXT_FORMAT, true).valueOf();
  }
  if (dayjs.isDayjs(value)) {
    return value.valueOf();
  }
  if (value instanceof Date) {
    return value.getTime();
  }
  return value;
};

/**
 * 将绝对时刻转换为 Unix 整数秒
 * @returns 无效时返回 null
 */
export const toEpochSeconds = (value: TimeInstant | null | undefined): EpochSeconds | null => {
  if (value === null || value === undefined || value === '') {
    return null;
  }

  const milliseconds = toMilliseconds(value);
  if (!Number.isFinite(milliseconds) || milliseconds < 0) {
    return null;
  }

  return Math.floor(milliseconds / 1000);
};

/**
 * 将起止时刻转换为后端可接受的秒级区间
 * @returns 任一端无效或起点晚于终点时返回 null
 */
export const toTimeRangeSeconds = (
  start: TimeInstant | null | undefined,
  end: TimeInstant | null | undefined,
): TimeRangeSeconds | null => {
  const startSeconds = toEpochSeconds(start);
  const endSeconds = toEpochSeconds(end);

  if (startSeconds === null || endSeconds === null || startSeconds > endSeconds) {
    return null;
  }

  return [startSeconds, endSeconds];
};

/**
 * 以当前时刻为终点的最近一段时间
 * @param amount 时长
 * @param unit 时长单位
 * @param now 终点时刻，默认当前时间
 */
export const getRecentRange = (
  amount: number,
  unit: ManipulateType,
  now: Dayjs = dayjs(),
): TimeRangeSeconds => [now.subtract(amount, unit).unix(), now.unix()];

/**
 * 由筛选状态生成接口的时间参数
 * 两端都是有效秒数时成对返回；否则都不传，避免把空字符串或单端时间发给后端
 */
export const toTimeRangeQuery = ({ time_start, time_end }: ITimeRangeFilter): {
  time_start?: EpochSeconds
  time_end?: EpochSeconds
} => (typeof time_start === 'number' && typeof time_end === 'number'
  ? {
    time_start,
    time_end,
  }
  : {});

const SECONDS_PER_DAY = 24 * 60 * 60;

/**
 * 向下取整到 UTC 0 点
 * Unix 时间不计闰秒，UTC 日界线恰为 86400 秒的整数倍
 */
export const floorToUtcDay = (seconds: EpochSeconds): EpochSeconds =>
  Math.floor(seconds / SECONDS_PER_DAY) * SECONDS_PER_DAY;

/**
 * 两个秒级区间的交集
 * @returns 无交集时返回 null
 */
export const intersectTimeRange = (
  range: TimeRangeSeconds,
  bounds: TimeRangeSeconds,
): TimeRangeSeconds | null => {
  const start = Math.max(range[0], bounds[0]);
  const end = Math.min(range[1], bounds[1]);
  return start <= end ? [start, end] : null;
};

/**
 * 由柱状图框选的桶下标计算查询区间
 *
 * timeline 为后端返回的各桶起点（秒，升序、等间隔）。
 * 结果为闭区间 [首桶起点, 末桶起点 + 桶宽 - 1]，与日志接口 gte/lte 的闭区间一致；
 * 给出 queryRange 时再与当前查询窗口取交集（首末桶按固定间隔对齐，可能超出窗口），
 * 使框选后的日志数与所选柱子的计数一致。
 * @returns 下标无效或选择为空时返回 null
 */
export const getBucketRange = (
  timeline: readonly number[],
  startIndex: number,
  endIndex: number,
  queryRange?: TimeRangeSeconds | null,
): TimeRangeSeconds | null => {
  const lastIndex = timeline.length - 1;
  if (lastIndex < 0 || !Number.isInteger(startIndex) || !Number.isInteger(endIndex)) {
    return null;
  }

  const first = Math.max(0, Math.min(startIndex, endIndex));
  const last = Math.min(lastIndex, Math.max(startIndex, endIndex));
  if (first > last) {
    return null;
  }

  const bucketWidth = lastIndex > 0 ? timeline[1] - timeline[0] : 0;
  const start = timeline[first];
  // 只有一个桶时无法得出桶宽，以当前查询窗口的终点作为结束
  const end = bucketWidth > 0
    ? timeline[last] + bucketWidth - 1
    : (queryRange?.[1] ?? timeline[last]);

  const range = toTimeRangeSeconds(start * 1000, end * 1000);
  if (!range || !queryRange) {
    return range;
  }

  return intersectTimeRange(range, queryRange);
};
