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
 * ECharts 按需引入，图表统一通过 createChart 创建实例。
 * - 只注册了项目用到的图表和组件，使用新的图表类型（如饼图）或组件时需在下方 use() 中注册，
 *   否则对应部分不会渲染，开发环境控制台会提示未注册
 * - 不要从 utils/index.ts 导出，避免 ECharts 进入首屏 chunk
 */
import { BarChart, LineChart } from 'echarts/charts';
import {
  DataZoomComponent,
  GridComponent,
  LegendComponent,
  MarkAreaComponent,
  MarkPointComponent,
  TitleComponent,
  ToolboxComponent,
  TooltipComponent,
} from 'echarts/components';
import {
  type ECharts,
  type EChartsInitOpts,
  init,
  use,
} from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
// ECharts 6 调整了默认配色、图例位置等，注册 v5 主题保持升级前的样式
import 'echarts/theme/v5';

export type { ECharts } from 'echarts/core';

use([
  LineChart,
  BarChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  DataZoomComponent,
  MarkPointComponent,
  MarkAreaComponent,
  ToolboxComponent,
  TitleComponent,
  CanvasRenderer,
]);

export const createChart = (dom?: HTMLElement | null, opts?: EChartsInitOpts): ECharts => init(dom, 'v5', opts);
