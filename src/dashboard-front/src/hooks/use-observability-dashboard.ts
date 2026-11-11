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

import type { InjectionKey } from 'vue';
import { useGateway } from '@/stores';
import { queryMcpMetricsInstant, queryMcpMetricsRange } from '@/services/source/gateway/mcp-server/metrics';
import type { IChartDataLoading, IChartDataType, IStatisticsType } from '@/types/observability';
import type { IObservabilitySearchParams } from '@/services/source/gateway/mcp-server/log';
import { filterSimpleEmpty } from '@/utils/filterEmptyValues';

/** 时序图指标常量 */
export const METRICS_LIST = Object.freeze([
  'requests',
  'requests_2xx',
  'non_2xx_status',
  'app_requests',
  'tool_requests',
  'method_requests',
  'request_body_size',
  'response_body_size',
  'response_time_50th',
  'response_time_95th',
  'response_time_99th',
] as const);

/** 瞬时值指标常量 */
export const STATISTICS_TYPES = Object.freeze([
  'requests_total',
  'health_rate',
] as const);

type MetricsType = (typeof METRICS_LIST)[number];
type StatisticsType = (typeof STATISTICS_TYPES)[number];
type IntervalUnit = 's' | 'm' | 'h' | 'd';
export type IntervalValue = `${number}${IntervalUnit}` | 'off';

// 默认时间范围：最近 24 小时。每次调用都按当前时间计算
const getDefaultTimeRange = (): [number, number] => {
  const end = new Date();
  const start = new Date(end.getTime() - 24 * 60 * 60 * 1000);
  return [Math.floor(start.getTime() / 1000), Math.floor(end.getTime() / 1000)];
};

const createDefaultSearchParams = (): IObservabilitySearchParams => {
  const [timeStart, timeEnd] = getDefaultTimeRange();
  return {
    time_start: timeStart,
    time_end: timeEnd,
    step: 'auto',
    app_code: '',
    metrics: '',
    mcp_server_name: '',
  };
};

// 加载状态 - 初始化为所有指标的 false
const createDefaultLoading = (): IChartDataLoading =>
  Object.fromEntries([...METRICS_LIST, ...STATISTICS_TYPES].map(key => [key, false]));

/**
 * 解析刷新间隔
 * @returns 毫秒；'off' 或无效值返回 0
 */
export const parseIntervalValue = (value: IntervalValue): number => {
  if (value === 'off') return 0;

  const unit = value.slice(-1) as IntervalUnit;
  const num = Number(value.slice(0, -1));

  const unitMap: Record<IntervalUnit, number> = {
    s: 1000,
    m: 60 * 1000,
    h: 60 * 60 * 1000,
    d: 24 * 60 * 60 * 1000,
  };

  const milliseconds = num * unitMap[unit];
  return Number.isFinite(milliseconds) ? milliseconds : 0;
};

/**
 * 创建可观测仪表盘的状态与请求方法
 * 状态归属于可观测页面的一个实例，随页面卸载释放
 */
const createObservabilityDashboard = () => {
  const gatewayStore = useGateway();

  // 获取最新网关
  const gatewayId = computed(() => gatewayStore?.apigwId);

  // 加载状态
  const chartLoading = ref<IChartDataLoading>(createDefaultLoading());
  // 时序图数据
  const chartData = ref<IChartDataType>({});
  // 统计瞬时数据
  const statistics = ref<IStatisticsType>({});
  // 自动刷新间隔；定时器由仪表盘组件根据该值统一调度
  const interval = ref<IntervalValue>('off');
  // 下拉框展开状态
  const isOpenStep = ref(false);
  const isOpenInterval = ref(false);
  // 查询条件参数
  const searchParams = ref<IObservabilitySearchParams>(createDefaultSearchParams());

  /**
   * 统一设置所有指标的加载状态
   */
  const setAllLoading = (value: boolean) => {
    const allKeys = [...METRICS_LIST, ...STATISTICS_TYPES] as Array<keyof IChartDataLoading>;
    allKeys.forEach((key) => {
      chartLoading.value[key] = value;
    });
  };

  /**
   * 通用请求处理函数
   */
  const requestHandler = async <T>(
    fetchFn: (apigwId: number, params: IObservabilitySearchParams) => Promise<T>,
    params: Partial<IObservabilitySearchParams>,
    errorMsg: string,
  ): Promise<T | null> => {
    try {
      const result = await fetchFn(gatewayId.value, filterSimpleEmpty(params));
      return result;
    }
    catch (error) {
      console.error(errorMsg, error);
      return null;
    }
  };

  /**
   * 获取单指标时序图数据
   */
  const fetchSingleMetricsData = async ({ metrics }: { metrics: MetricsType }) => {
    const hasValidParams = gatewayId.value && searchParams.value.time_start;
    if (!hasValidParams) return;

    chartLoading.value[metrics] = true;

    try {
      const params = {
        ...searchParams.value,
        metrics,
      };
      const res = await requestHandler(
        queryMcpMetricsRange,
        params,
        `时序图指标${metrics}请求失败:`,
      );
      chartData.value[metrics] = res ?? {};
    }
    finally {
      chartLoading.value[metrics] = false;
    }
  };

  /**
   * 获取单指标瞬时统计数据
   */
  const fetchSingleInstantData = async ({ metrics }: { metrics: StatisticsType }) => {
    const hasValidParams = gatewayId.value && searchParams.value.time_start;
    if (!hasValidParams) return;

    chartLoading.value[metrics] = true;

    try {
      const params = {
        ...searchParams.value,
        metrics,
      };
      const res = await requestHandler(
        queryMcpMetricsInstant,
        params,
        `[瞬时统计] ${metrics} 请求失败：`,
      );
      statistics.value[metrics] = res ?? {};
    }
    finally {
      chartLoading.value[metrics as keyof IChartDataLoading] = false;
    }
  };

  /**
   * 批量获取页面所有时序图数据
   */
  const fetchPageMetricsData = () => {
    const requests = METRICS_LIST.map(metrics =>
      fetchSingleMetricsData({ metrics }),
    );
    return Promise.all(requests);
  };

  /**
   * 批量获取瞬时统计数据
   */
  const fetchInstantMetricsData = () => {
    const requests = STATISTICS_TYPES.map(metrics =>
      fetchSingleInstantData({ metrics }),
    );
    return Promise.all(requests);
  };

  /**
   * 按当前查询参数请求全部数据（自动刷新时触发 loading）
   */
  const fetchInitData = async () => {
    // 自动刷新/初始化时，统一开启所有 loading
    setAllLoading(true);

    try {
      await Promise.all([fetchPageMetricsData(), fetchInstantMetricsData()]);
    }
    finally {
      // 所有请求完成后，统一关闭 loading
      setAllLoading(false);
    }
  };

  /**
   * 处理刷新间隔变更
   */
  const handleRefreshTimeChange = (value: IntervalValue) => {
    isOpenInterval.value = false;
    interval.value = value;
  };

  /**
   * 处理时间粒度变更
   */
  const handleStepChange = (value: string) => {
    isOpenStep.value = false;
    searchParams.value.step = value;
  };

  /**
   * 重置刷新间隔与时间粒度
   */
  const handleResetTime = () => {
    handleRefreshTimeChange('off');
    handleStepChange('auto');
  };

  /**
   * 恢复初始状态：停止自动刷新、清空图表数据，查询参数回到默认的最近 24 小时
   */
  const resetDashboard = () => {
    interval.value = 'off';
    searchParams.value = createDefaultSearchParams();
    chartData.value = {};
    statistics.value = {};
    chartLoading.value = createDefaultLoading();
  };

  return {
    interval,
    isOpenStep,
    isOpenInterval,
    searchParams,
    chartLoading,
    chartData,
    statistics,
    handleStepChange,
    handleRefreshTimeChange,
    handleResetTime,
    resetDashboard,
    fetchPageMetricsData,
    fetchInstantMetricsData,
    fetchSingleMetricsData,
    fetchInitData,
  };
};

export type IObservabilityDashboard = ReturnType<typeof createObservabilityDashboard>;

const OBSERVABILITY_DASHBOARD_KEY: InjectionKey<IObservabilityDashboard> = Symbol('observability-dashboard');

/**
 * 可观测页面在 setup 中调用一次：创建仪表盘状态，并提供给仪表盘、工具栏、图表等子组件共享
 */
export function provideObservabilityDashboard() {
  const dashboard = createObservabilityDashboard();
  provide(OBSERVABILITY_DASHBOARD_KEY, dashboard);
  return dashboard;
}

/**
 * 获取可观测页面提供的仪表盘状态
 */
export function useObservabilityDashboard() {
  const dashboard = inject(OBSERVABILITY_DASHBOARD_KEY);
  if (!dashboard) {
    throw new Error('useObservabilityDashboard() must be called inside a descendant of provideObservabilityDashboard()');
  }
  return dashboard;
}
