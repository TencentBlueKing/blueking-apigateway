<template>
  <top />
  <div class="statistics">
    <div class="requests line-container">
      <div class="total-requests">
        <div class="title">
          {{ t('总请求数') }}
        </div>
        <div class="number">
          63409
        </div>
      </div>
      <div class="success-requests">
        <line-chart
          :title="t('总请求数趋势')"
          :chart-data="chartData['requests']"
          instance-id="requests" />
      </div>
      <div class="error-requests">
        <line-chart
          :title="t('非 200 请求数趋势')"
          :chart-data="chartData['non_200_status']"
          instance-id="non_200_status" />
      </div>
    </div>

    <div class="secondary-panel line-container">
      <div class="secondary-lf">
        <line-chart
          :title="t('top10 app_code 请求数趋势')"
          :chart-data="chartData['app_requests']"
          instance-id="app_requests" />
      </div>
      <div class="secondary-rg">
        <line-chart
          :title="t('top10 资源请求数趋势')"
          :chart-data="chartData['resource_requests']"
          instance-id="resource_requests" />
      </div>
    </div>

    <div class="secondary-panel line-container">
      <div class="secondary-lf">
        <line-chart
          :title="t('top10 资源 ingress 带宽占用')"
          :chart-data="chartData['ingress']"
          instance-id="ingress" />
      </div>
      <div class="secondary-rg">
        <line-chart
          :title="t('top10 资源 egress 带宽占用')"
          :chart-data="chartData['egress']"
          instance-id="egress" />
      </div>
    </div>

    <div class="full-line">
      <line-chart
        :title="t('资源响应耗时分布')"
        :chart-data="chartData['response_time']"
        instance-id="response_time" />
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onBeforeUnmount } from 'vue';
import { useCommon } from '@/store';
import { getApigwMetrics } from '@/http';
import { useI18n } from 'vue-i18n';
import { SearchParamsType } from './type';
import mitt from '@/common/event-bus';
import Top from './components/top.vue';
import LineChart from './components/line-chart.vue';

const common = useCommon();
const { apigwId } = common;

const { t } = useI18n();

const metricsList = ref<string[]>([
  'requests_total', // 请求总数
  'requests', // 总请求数趋势
  'non_200_status', // 非 200 请求数趋势
  'app_requests', // app_code 维度请求数趋势
  'resource_requests', // 每个资源请求数趋势
  'ingress', // 每个资源的 ingress  带宽占用
  'egress', // 每个资源的 egress 带宽占用
  'failed_500_requests', // 一段时间内 500 状态码请求数量（用于计算健康率）
  'response_time', // 每个资源的响应耗时分布 50th 80th 90th 取 top10 资源 (response_time_50th response_time_80th response_time_90th)
]);
const chartData = ref<any>({
  response_time: {},
});

// 请求数据
const getData = async (searchParams: SearchParamsType, type: string) => {
  searchParams.metrics = type;
  const data = await getApigwMetrics(apigwId, searchParams);

  if (type === 'response_time_50th' || type === 'response_time_80th' || type === 'response_time_90th') {
    chartData.value.response_time[type] = data;
  } else {
    chartData.value[type] = data;
  }
};

mitt.on('search-change', (searchParams: SearchParamsType) => {
  metricsList.value.forEach((type: string) => {
    if (type !== 'response_time') {
      getData(searchParams, type);
    } else {
      getData(searchParams, 'response_time_50th');
      getData(searchParams, 'response_time_80th');
      getData(searchParams, 'response_time_90th');
    };
  });
});

onBeforeUnmount(() => {
  mitt.off('search-change');
});

</script>

<style lang="scss" scoped>
.statistics {
  padding: 20px 24px 32px;
  .line-container {
    display: flex;
    align-items: center;
    margin-bottom: 16px;
  }
  .requests {
    .total-requests {
      width: 254px;
      height: 320px;
      background: #FFFFFF;
      box-shadow: 0 1px 2px 0 #0000001a;
      border-radius: 2px;
      margin-right: 16px;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      .title {
        font-size: 14px;
        color: #63656E;
        line-height: 18px;
        margin-bottom: 24px;
      }
      .number {
        font-weight: Bold;
        font-size: 32px;
        color: #313238;
        line-height: 32px;
      }
    }
    .success-requests {
      width: 673px;
      height: 320px;
      background: #FFFFFF;
      box-shadow: 0 2px 4px 0 #1919290d;
      border-radius: 2px;
      margin-right: 16px;
    }
    .error-requests {
      width: 673px;
      height: 320px;
      background: #FFFFFF;
      box-shadow: 0 2px 4px 0 #1919290d;
      border-radius: 2px;
    }
  }
  .secondary-panel {
    .secondary-lf {
      width: 808px;
      height: 360px;
      background: #FFFFFF;
      box-shadow: 0 2px 4px 0 #1919290d;
      border-radius: 2px;
      margin-right: 16px;
    }
    .secondary-rg {
      width: 808px;
      height: 360px;
      background: #FFFFFF;
      box-shadow: 0 2px 4px 0 #1919290d;
      border-radius: 2px;
    }
  }
  .full-line {
    height: 360px;
    background: #FFFFFF;
    box-shadow: 0 2px 4px 0 #1919290d;
    border-radius: 2px;
  }
}
</style>
