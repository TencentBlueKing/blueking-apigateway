<template>
  <div class="dashboard-wrapper p-20px bg-#f5f7fa">
    <div class="grid grid-cols-4 gap-16px mb-16px">
      <BkCard
        v-for="stats in statsList"
        :key="stats.id"
        class="text-center"
        :title="stats.label"
      >
        <div class="text-28px font-bold py-10px color-#313238">
          {{ stats.value }}
        </div>
        <div class="text-12px color-#979ba5">
          {{ t('较昨日') }}
          <span :class="stats.trend === 'up' ? 'color-#2dcb56' : 'color-#ea3636'">
            {{ stats.percent }}% {{ stats.trend === 'up' ? '↑' : '↓' }}
          </span>
        </div>
      </BkCard>
    </div>

    <div class="grid grid-cols-3 gap-16px">
      <BkCard
        class="col-span-2"
        :title="t('访问趋势')"
      >
        <BkLoading :loading="loading">
          <!-- 图表容器：通过 @/utils/echarts 的 createChart 按需创建，禁止整包引入 echarts -->
          <div
            ref="chartRef"
            class="h-300px w-full"
          />
        </BkLoading>
      </BkCard>

      <BkCard :title="t('最近操作')">
        <BkTimeline :list="timelineList" />
      </BkCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ECharts } from 'echarts/core';
import { createChart } from '@/utils/echarts';

interface IStatsCard {
  id: string
  label: string
  value: string
  percent: string
  trend: 'up' | 'down'
}

interface ITimelineItem {
  tag: string
  content: string
}

const { t } = useI18n();

const chartRef = useTemplateRef<HTMLDivElement>('chartRef');
const loading = shallowRef(false);
// ECharts 实例不可被 Vue Proxy 代理，使用普通变量或 shallowRef + markRaw
let chartInstance: ECharts | null = null;

const statsList = shallowRef<IStatsCard[]>([
  {
    id: 'requests',
    label: t('今日请求量'),
    value: '84,200',
    percent: '5',
    trend: 'up',
  },
  {
    id: 'errors',
    label: t('异常请求数'),
    value: '12',
    percent: '2',
    trend: 'down',
  },
  {
    id: 'latency',
    label: t('平均耗时'),
    value: '24ms',
    percent: '3',
    trend: 'down',
  },
  {
    id: 'availability',
    label: t('可用率'),
    value: '99.98%',
    percent: '0.01',
    trend: 'up',
  },
]);

const timelineList = shallowRef<ITimelineItem[]>([]);

const handleResize = () => {
  chartInstance?.resize();
};

onMounted(() => {
  if (chartRef.value) {
    chartInstance = createChart(chartRef.value);
    chartInstance.setOption({
      xAxis: {
        type: 'category',
        data: [],
      },
      yAxis: {
        type: 'value',
      },
      series: [
        {
          type: 'line',
          data: [],
        },
      ],
    });
  }
  window.addEventListener('resize', handleResize);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize);
  chartInstance?.dispose();
  chartInstance = null;
});
</script>

<style lang="scss" scoped>
.dashboard-wrapper {
  min-height: 100%;
}
</style>
