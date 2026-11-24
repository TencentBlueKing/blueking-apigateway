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
import { useChartIntervalOption } from '@/hooks/use-chart-interval-option';

describe('hooks/use-chart-interval-option', () => {
  const { getChartIntervalOption } = useChartIntervalOption();

  it('按数值量级推导 interval 并通过 max 回调向上对齐到下一个刻度', () => {
    const cases: Array<[number, number]> = [
      [8, 1],
      [15, 2],
      [40, 5],
      [80, 10],
      [500, 100],
      [3000, 500],
      [8000, 1000],
      [15000, 2000],
      [30000, 5000],
      [80000, 10000],
      [300000, 20000],
      [800000, 50000],
      [3000000, 500000],
      [8000000, 1000000],
      [20000000, 10000000],
    ];

    for (const [max, expectedInterval] of cases) {
      const option = getChartIntervalOption(max, 'number');
      expect(option.yAxis.interval).toBe(expectedInterval);
    }

    // 自定义 xAxis 且验证 max 对齐函数
    const xOption = getChartIntervalOption(80, 'number', 'xAxis');
    expect(xOption.xAxis.interval).toBe(10);
    expect(xOption.xAxis.max({ max: 83 })).toBe(90);
    expect(xOption.xAxis.max({ max: 80 })).toBe(90);
  });

  it('按时间跨度档位设置 interval 与对应时间轴格式器', () => {
    const sampleTime = '2026-11-24 09:08:07';
    const d = dayjs(sampleTime);

    const withinHour = getChartIntervalOption(3600, 'time', 'xAxis');
    expect(withinHour.xAxis.interval).toBe(5 * 60 * 1000);
    expect(withinHour.xAxis.axisLabel.formatter(sampleTime)).toBe(d.format('HH:mm:ss'));

    const withinDay = getChartIntervalOption(86400, 'time', 'xAxis');
    expect(withinDay.xAxis.interval).toBe(2 * 60 * 60 * 1000);
    expect(withinDay.xAxis.axisLabel.formatter(sampleTime)).toBe(d.format('HH:mm'));

    const withinMonth = getChartIntervalOption(86400 * 10, 'time', 'xAxis');
    expect(withinMonth.xAxis.interval).toBe(86400 * 1000);
    expect(withinMonth.xAxis.axisLabel.formatter(sampleTime)).toBe(d.format('MM-DD HH:mm'));

    const withinYear = getChartIntervalOption(86400 * 60, 'time', 'xAxis');
    expect(withinYear.xAxis.interval).toBe(86400 * 1000 * 31);
    expect(withinYear.xAxis.axisLabel.formatter(sampleTime)).toBe(d.format('MM-DD'));

    const overYear = getChartIntervalOption(86400 * 400, 'time', 'xAxis');
    expect(overYear.xAxis.interval).toBe(86400 * 1000 * 31 * 3);
    expect(overYear.xAxis.axisLabel.formatter(sampleTime)).toBe(d.format('YYYY-MM-DD'));
  });
});
