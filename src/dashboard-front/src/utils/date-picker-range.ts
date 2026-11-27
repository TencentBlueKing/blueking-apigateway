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
 * @blueking/date-picker 选择值的解析
 *
 * 组件的选择值可能是相对表达式（如 ['now-10m', 'now']、['now/d', 'now']）或绝对毫秒时间戳。
 * 相对表达式必须在每轮查询时按当前时间重新解析，这里复用组件自身的 DateRange，
 * 保证与组件展示的语义一致。
 */

import { DateRange, type DateValue } from '@blueking/date-picker';
import { type TimeRangeSeconds, toTimeRangeSeconds } from '@/utils/time-range';

/**
 * 按当前时间将日期组件的选择值解析为秒级区间
 * @returns 选择值无效时返回 null
 */
export const resolveDatePickerRange = (value: DateValue | undefined | null): TimeRangeSeconds | null => {
  if (!value) {
    return null;
  }

  try {
    const { startDate, endDate } = new DateRange(value);
    return toTimeRangeSeconds(startDate, endDate);
  }
  catch {
    // 无法识别的表达式会在组件内部抛错
    return null;
  }
};
