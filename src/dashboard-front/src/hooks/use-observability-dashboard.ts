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

import { useGateway } from '@/stores';
import {
  type IChartDataLoading,
  type IChartDataType,
  type IObservabilitySearchParams,
  type IStatisticsType,
  fetchMetricsQueryInstant,
  fetchMetricsQueryRange,
} from '@/services/source/observability';
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
type IntervalValue = `${number}${IntervalUnit}` | 'off';

// 时间转换工具函数
const getDefaultTimeRange = (): [number, number] => {
  const end = new Date();
  const start = new Date(end.getTime() - 24 * 60 * 60 * 1000);
  return [Math.floor(start.getTime() / 1000), Math.floor(end.getTime() / 1000)];
};

// 解析刷新间隔工具函数
const parseIntervalValue = (value: IntervalValue): number => {
  if (value === 'off') return 0;

  const unit = value.slice(-1) as IntervalUnit;
  const num = Number(value.slice(0, -1));

  const unitMap: Record<IntervalUnit, number> = {
    s: 1000,
    m: 60 * 1000,
    h: 60 * 60 * 1000,
    d: 24 * 60 * 60 * 1000,
  };

  return num * unitMap[unit];
};

// 加载状态 - 初始化为所有指标的false
const chartLoading = ref<IChartDataLoading>(
  Object.fromEntries([...METRICS_LIST, ...STATISTICS_TYPES].map(key => [key, false])),
);
// 时序图数据
const chartData = ref<IChartDataType>({});
// 统计瞬时数据
const statistics = ref<IStatisticsType>({});
// 自动刷新间隔
const interval = ref<IntervalValue>('off');
// 下拉框展开状态
const isOpenStep = ref(false);
const isOpenInterval = ref(false);

// 默认时间范围
const defaultTime = computed(() => getDefaultTimeRange());

// 查询条件参数（优化初始值类型）
const searchParams = ref<IObservabilitySearchParams>({
  time_start: defaultTime.value[0],
  time_end: defaultTime.value[1],
  step: 'auto',
  app_code: '',
  metrics: '',
  mcp_server_name: '',
});

/**
 * 可观测监控 Hook
 */
export function useObservabilityDashboard() {
  const gatewayStore = useGateway();

  // 获取最新网关
  const gatewayId = computed(() => gatewayStore?.apigwId);

  // 定时器ID
  let timeId: ReturnType<typeof setTimeout> | null = null;

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
        fetchMetricsQueryRange,
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
        fetchMetricsQueryInstant,
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
   * 初始化数据（自动刷新时触发 loading）
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
   * 设置自动刷新定时器
   */
  const setAutoRefreshInterval = (value: IntervalValue) => {
    if (timeId) {
      clearInterval(timeId);
      timeId = null;
    }

    if (value === 'off') return;

    const intervalTime = parseIntervalValue(value);
    if (intervalTime <= 0) return;

    timeId = setInterval(() => {
      fetchInitData();
    }, intervalTime);
  };

  /**
   * 处理刷新间隔变更
   */
  const handleRefreshTimeChange = (value: IntervalValue) => {
    isOpenInterval.value = false;
    interval.value = value;
    setAutoRefreshInterval(value);
  };

  /**
   * 处理时间粒度变更
   */
  const handleStepChange = (value: string) => {
    isOpenStep.value = false;
    searchParams.value.step = value;
  };

  const handleResetTime = () => {
    handleCleanup();
    handleRefreshTimeChange('off');
    handleStepChange('auto');
  };

  // 清理定时器
  const handleCleanup = () => {
    if (timeId) {
      clearInterval(timeId);
      timeId = null;
    }
  };

  onUnmounted(() => {
    interval.value = 'off';
    searchParams.value = {
      time_start: defaultTime.value[0],
      time_end: defaultTime.value[1],
      step: 'auto',
      app_code: '',
      metrics: '',
      mcp_server_name: '',
    };
    handleCleanup();
  });

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
    fetchPageMetricsData,
    fetchInstantMetricsData,
    fetchSingleMetricsData,
    fetchInitData,
  };
}
