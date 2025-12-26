/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
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
import localeData from 'dayjs/plugin/localeData';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/zh-cn';
import 'dayjs/locale/en';
import { t } from '@/locales';

dayjs.extend(utc);
dayjs.extend(localeData);
dayjs.extend(relativeTime);

const SUPPORTED_LANGS = ['zh-cn', 'en'] as const;

type ValidLang = (typeof SUPPORTED_LANGS)[number];

interface RelativeTimeConfig {
  s?: string | undefined
  ss?: string | ((num: number) => string)
  m?: string | undefined
  mm?: string | ((num: number) => string)
  h?: string | undefined
  hh?: string | ((num: number) => string)
  d?: string | undefined
  dd?: string | ((num: number) => string)
  M?: string | undefined
  MM?: string | ((num: number) => string)
  y?: string | undefined
  yy?: string | ((num: number) => string)
  future?: string | undefined
  past?: string | undefined
}

// 默认相对时间配置
const defaultRelativeTime = {
  s: '刚刚',
  ss: '%d 秒前',
  m: t('1分钟前'),
  mm: '%d 分钟前',
  h: t('1小时前'),
  hh: '%d 小时前',
  d: t('1天前'),
  dd: '%d 天前',
  M: t('1个月前'),
  MM: '%d 个月前',
  y: t('1年前'),
  yy: '%d 年',
  future: '在 %s',
  past: '%s',
};

/**
 * @desc 设置国际化时间
 * @param { String } lang
 * @returns { String }
 */
export function setupDayjsLocale(lang: string): void {
  const validLang = SUPPORTED_LANGS.includes(lang as ValidLang)
    ? (lang as ValidLang)
    : 'zh-cn';
  dayjs.locale(validLang);

  const localeDataObj = dayjs.localeData();

  const relativeTimeConfig = (localeDataObj as { relativeTime?: typeof defaultRelativeTime }).relativeTime || {};

  const customRelativeTime: Partial<RelativeTimeConfig> = {
    ...relativeTimeConfig,
    ...defaultRelativeTime,
    s: t('刚刚') || defaultRelativeTime.s,
    ss: (num: number) => (t('几秒前', { n: num }) || defaultRelativeTime.ss).replace(/\{n\}|\%d/g, num.toString()),
    mm: (num: number) => (t('{n}分钟前', { n: num }) || defaultRelativeTime.mm).replace(/\{n\}|\%d/g, num.toString()),
    hh: (num: number) => (t('{n}小时前', { n: num }) || defaultRelativeTime.hh).replace(/\{n\}|\%d/g, num.toString()),
    dd: (num: number) => (t('{n}天前', { n: num }) || defaultRelativeTime.dd).replace(/\{n\}|\%d/g, num.toString()),
    MM: (num: number) => (t('{n}个月前', { n: num }) || defaultRelativeTime.MM).replace(/\{n\}|\%d/g, num.toString()),
    yy: (num: number) => (t('{n}年前', { n: num }) || defaultRelativeTime.yy).replace(/\{n\}|\%d/g, num.toString()),
  };

  dayjs.locale(validLang, {
    relativeTime: customRelativeTime as Partial<{
      future: string
      past: string
      s: string
      m: string
      mm: string
      h: string
      hh: string
      d: string
      dd: string
      M: string
      MM: string
      y: string
      yy: string
    }>,
  });
};

/**
 * @desc 获取Utc时间
 * @param { String } updatedTimeStr
 * @returns { String }
 */
export function getUtcTimeAgo(updatedTimeStr: string): string {
  if (!updatedTimeStr) return '';

  const targetUtc = dayjs(updatedTimeStr).utc();
  const nowUtc = dayjs().utc();

  if (!targetUtc.isValid() || !nowUtc.isValid()) {
    return '';
  }

  try {
    return targetUtc.from(nowUtc);
  }
  catch (error) {
    console.error('Failed to format relative time:', error);
    return '';
  }
}
