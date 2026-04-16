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
import utc from 'dayjs/plugin/utc';
import timezone from 'dayjs/plugin/timezone';
import duration from 'dayjs/plugin/duration';
import _dropWhile from 'lodash-es/dropWhile';

import { toFloatPrecision } from './number';

dayjs.extend(utc);
dayjs.extend(timezone);
dayjs.extend(duration);

const TODAY = 'Today';
const YESTERDAY = 'Yesterday';

export const STANDARD_DATE_FORMAT = 'YYYY-MM-DD';
export const STANDARD_TIME_FORMAT = 'HH:mm';
export const STANDARD_TIME_MS_FORMAT = 'HH:mm:ss.SSS';
export const STANDARD_DATETIME_FORMAT = 'MMMM D YYYY, HH:mm:ss.SSS';
export const ONE_MILLISECOND = 1000;
export const ONE_SECOND = 1000 * ONE_MILLISECOND;
export const ONE_MINUTE = 60 * ONE_SECOND;
export const ONE_HOUR = 60 * ONE_MINUTE;
export const ONE_DAY = 24 * ONE_HOUR;
export const DEFAULT_MS_PRECISION = Math.log10(ONE_MILLISECOND);

const UNIT_STEPS: {
  microseconds: number
  ofPrevious: number
  unit: string
}[] = [
  {
    unit: 'd',
    microseconds: ONE_DAY,
    ofPrevious: 24,
  },
  {
    unit: 'h',
    microseconds: ONE_HOUR,
    ofPrevious: 60,
  },
  {
    unit: 'm',
    microseconds: ONE_MINUTE,
    ofPrevious: 60,
  },
  {
    unit: 's',
    microseconds: ONE_SECOND,
    ofPrevious: 1000,
  },
  {
    unit: 'ms',
    microseconds: ONE_MILLISECOND,
    ofPrevious: 1000,
  },
  {
    unit: 'ms',
    microseconds: 1,
    ofPrevious: 1000,
  },
];

const timeUnitToShortTermMapper = {
  milliseconds: 'ms',
  seconds: 's',
  minutes: 'm',
  hours: 'h',
  days: 'd',
};

/**
 * @param {number} duration
 * @param {number} totalDuration
 * @return {number} 0-100 percentage
 */
export function getPercentageOfDuration(duration: number, totalDuration: number): number {
  return (duration / totalDuration) * 100;
}

const quantizeDuration = (duration: number, floatPrecision: number, conversionFactor: number) =>
  toFloatPrecision(duration / conversionFactor, floatPrecision) * conversionFactor;

export function customFormatTime(duration: number, format = 'HH:mm') {
  return dayjs.tz(duration / ONE_MILLISECOND).format(format);
}

/**
 * @param {number} duration (in microseconds)
 * @return {string} formatted, unit-labelled string with time in milliseconds
 */
export function formatDate(duration: number): string {
  return dayjs.tz(duration / ONE_MILLISECOND).format(STANDARD_DATE_FORMAT);
}

/**
 * @param {number} duration (in microseconds)
 * @return {string} formatted, unit-labelled string with time in milliseconds
 */
export function formatDatetime(duration: number): string {
  return dayjs.tz(duration / ONE_MILLISECOND).format(STANDARD_DATETIME_FORMAT);
}

/**
 * Humanizes the duration for display.
 *
 * Example:
 * 5000ms => 5s
 * 1000μs => 1ms
 * 183840s => 2d 3h
 *
 * @param {number} duration (in microseconds)
 * @param {string} split 分隔符
 * @param {number} precision 精度
 * @return {string} formatted duration
 */
export function formatDuration(duration: number, split: string = '', precision?: number | null): string {
  const decimalLen = (String(duration).split('.')[1] || '').length;
  if (precision && duration > 0) {
    return decimalLen > precision ? `${duration.toFixed(precision)}${split}ms` : `${duration}${split}ms`;
  }

  // 直接以 ms 输出，完全不换算、不四舍五入
  return `${duration}${split}ms`;
}

export function formatDurationWithUnit(duration: number, split = '') {
  const units = _dropWhile(
    UNIT_STEPS,
    ({ microseconds }, index) => index < UNIT_STEPS.length - 1 && microseconds > duration,
  );
  if (duration === 0) return '0ms';
  let remainingMicroseconds = duration;
  const durationUnits = units.reduce<string[]>((pre, cur) => {
    if (remainingMicroseconds >= cur.microseconds) {
      const primaryValue = Math.floor(remainingMicroseconds / cur.microseconds);
      remainingMicroseconds = remainingMicroseconds % cur.microseconds;
      pre.push(`${primaryValue}${cur.unit}`);
    }
    return pre;
  }, []);
  return durationUnits.join(split);
}

/**
 * @param {number} duration (in microseconds)
 * @return {string} formatted, unit-labelled string with time in milliseconds
 */
export function formatMillisecondTime(duration: number): string {
  const targetDuration = quantizeDuration(duration, DEFAULT_MS_PRECISION, ONE_MILLISECOND);
  return `${dayjs.duration(targetDuration / ONE_MILLISECOND).asMilliseconds()}ms`;
}

export function formatRelativeDate(value: any, fullMonthName = false) {
  const m = dayjs.isDayjs(value) ? value : dayjs.tz(value);
  const monthFormat = fullMonthName ? 'MMMM' : 'MMM';
  const dt = new Date();
  if (dt.getFullYear() !== m.year()) {
    return m.format(`${monthFormat} D, YYYY`);
  }
  const mMonth = m.month();
  const mDate = m.date();
  const date = dt.getDate();
  if (mMonth === dt.getMonth() && mDate === date) {
    return TODAY;
  }
  dt.setDate(date - 1);
  if (mMonth === dt.getMonth() && mDate === dt.getDate()) {
    return YESTERDAY;
  }
  return m.format(`${monthFormat} D`);
}

/**
 * @param {number} duration (in microseconds)
 * @return {string} formatted, unit-labelled string with time in seconds
 */
export function formatSecondTime(duration: number): string {
  const targetDuration = quantizeDuration(duration, DEFAULT_MS_PRECISION, ONE_SECOND);
  return `${dayjs.duration(targetDuration / ONE_MILLISECOND).asSeconds()}s`;
}

/**
 * @param {number} duration (in microseconds)
 * @return {string} formatted, unit-labelled string with time in milliseconds
 */
export function formatTime(duration: number, isMs = false): string {
  return dayjs.tz(duration / ONE_MILLISECOND).format(isMs ? STANDARD_TIME_MS_FORMAT : STANDARD_TIME_FORMAT);
}

export function formatTraceTableDate(duration: number | string) {
  return dayjs
    .tz(+duration.toString().slice(0, 13).padEnd(13, '0'))
    .format(duration.toString().length > 13 ? 'YYYY-MM-DD HH:mm:ss.SSS' : 'YYYY-MM-DD HH:mm:ss');
}

export const getSuitableTimeUnit = (microseconds: number): string => {
  if (microseconds < 1000) {
    return 'microseconds';
  }

  const duration = dayjs.duration(microseconds / 1000, 'ms');

  return Object.keys(timeUnitToShortTermMapper)
    .reverse()
    .find((timeUnit) => {
      const durationInTimeUnit = duration.as(timeUnit as any);

      return durationInTimeUnit >= 1;
    })!;
};

export function convertTimeUnitToShortTerm(timeUnit: string) {
  // if (timeUnit === 'microseconds') return 'μs';
  if (timeUnit === 'microseconds') return 'ms';

  const shortTimeUnit = (timeUnitToShortTermMapper as any)[timeUnit];

  if (shortTimeUnit) return shortTimeUnit;

  return '';
}

export function convertToTimeUnit(microseconds: number, targetTimeUnit: string) {
  if (microseconds < 1000) {
    return microseconds;
  }

  return dayjs.duration(microseconds / 1000, 'ms').as(targetTimeUnit as any);
}

export function timeConversion(microseconds: number) {
  if (microseconds < 1000) {
    return `${microseconds}ms`;
  }

  const timeUnit = getSuitableTimeUnit(microseconds);

  return `${dayjs
    .duration(microseconds / 1000, 'ms')
    .as(timeUnit as any)}${convertTimeUnitToShortTerm(timeUnit)}`;
}
