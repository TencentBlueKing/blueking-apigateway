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

<template>
  <CardContainer>
    <div class="stage-card-item">
      <div class="card-header">
        <div
          v-if="!loading"
          class="status-indicator"
        >
          <Spinner
            v-if="status === 'doing'"
            style="font-size: 16px;color:#3a84f6;"
          />
          <div
            v-bk-tooltips="{
              content: getStatusText(status),
              disabled: !getStatusText(status),
            }"
            class="dot"
            :class="[status]"
          />
        </div>
        <div class="name">
          {{ stage.name }}
        </div>
      </div>
      <div class="card-main">
        <div class="text-info">
          <div class="row url">
            <div class="label">
              {{ t('访问地址') }}：
            </div>
            <div
              v-bk-tooltips="getStageUrl(stage.name)"
              class="value"
            >
              {{ getStageUrl(stage.name) }}
            </div>
          </div>
          <div class="row version">
            <div class="label">
              {{ t('当前资源版本') }}：
            </div>
            <div
              v-if="status === 'unreleased'"
              class="value"
            >
              <BkTag
                size="small"
                class="font-normal"
                theme="warning"
              >
                {{ t('未发布') }}
              </BkTag>
            </div>
            <div
              v-else
              class="value"
            >
              <BkBadge
                v-if="!gatewayStore.isProgrammableGateway && stage.new_resource_version"
                v-bk-tooltips="{ content: `有新版本 ${stage.new_resource_version || '--'} 可以发布` }"
                :count="999"
                dot
                position="top-right"
                theme="danger"
              >
                <span>{{ stage.resource_version.version || '--' }}</span>
              </BkBadge>
              <span v-else>{{ stage.resource_version.version || '--' }}</span>
              <!-- 发布失败 -->
              <span
                v-if="status === 'failure'"
                class="suffix"
                :class="[status]"
              >（{{
                stage.paasInfo?.latest_deployment?.version || stage.paasInfo?.version || '--'
              }} 版本发布失败，<span><BkButton
                text
                theme="primary"
                @click.stop="handleCheckLog"
              >{{
                t('查看日志')
              }}</BkButton></span>）</span>
              <!-- 发布中 -->
              <span
                v-else-if="status === 'doing'"
                class="suffix"
              >（<span
                class="font-bold"
              >{{
                stage.paasInfo?.latest_deployment?.version || stage.publish_version || '--'
              }}</span> 版本正在发布中，<span><BkButton
                text
                theme="primary"
                @click.stop="handleCheckLog"
              >{{
                t('查看日志')
              }}</BkButton></span>）</span>
              <!-- 发布成功 -->
              <span
                v-else
                v-bk-tooltips="`于 ${stage.release.created_time || '--'} 发布成功`"
                class="suffix"
              >（于 {{
                stage.release.created_time || '--'
              }} 发布成功）</span>
            </div>
          </div>
        </div>
        <div>
          <BkButton
            v-bk-tooltips="actionTooltipConfig"
            class="mr-12px"
            size="small"
            theme="primary"
            :disabled="isActionDisabled"
            :loading="status === 'doing'"
            @click.stop="handlePublishClick"
          >
            {{ t('发布资源') }}
          </BkButton>
          <BkButton
            v-bk-tooltips="actionTooltipConfig"
            size="small"
            :disabled="isUnlistDisabled"
            :loading="status === 'doing'"
            @click.stop="handleDelistClick"
          >
            {{ t('下架') }}
          </BkButton>
        </div>
      </div>
      <template v-if="featureFlagStore.flags.ENABLE_RUN_DATA_METRICS">
        <div class="divider" />
        <div
          class="card-chart"
          @click.stop="handleChartClick"
        >
          <div
            :class="{ 'empty-state': stage.status === 0 }"
            class="request-counter"
          >
            <div class="label">
              {{ t('总请求数') }}
            </div>
            <div class="value">
              {{ stage.status === 0 ? t('尚未发布，无数据') : requestCount }}
            </div>
          </div>
          <div class="item-chart-wrapper">
            <StageCardLineChart
              v-if="stage.status === 1"
              :data="data"
              :mount-id="uniqueId()"
            />
          </div>
        </div>
      </template>
    </div>
  </CardContainer>
</template>

<script lang="ts" setup>
import { Spinner } from 'bkui-lib/icon';
import StageCardLineChart from './StageCardLineChart.vue';
import { getStatusText } from '@/utils';
import { getGatewayMetrics, getGatewayMetricsInstant } from '@/services/source/metrics';
import dayjs from 'dayjs';
import {
  useEnv,
  useFeatureFlag,
  useGateway,
} from '@/stores';
import { uniqueId } from 'lodash-es';
import { useRouteParams } from '@vueuse/router';
import CardContainer from '@/components/card-container/Index.vue';

interface IRelease {
  status: string
  created_time: null | string
  created_by: string
}

interface IResourceVersion {
  version: string
  id: number
  schema_version: string
}

interface IPaasInfo {
  branch: string
  commit_id: string
  created_by: string | null
  created_time: string
  deploy_id: string
  latest_deployment: {
    branch: string
    commit_id: string
    deploy_id: string
    history_id: number
    status: string
    version: string
  }
  repo_info: {
    branch_commit_info: {
      [branch: string]: {
        commit_id: string
        extra: object
        last_update: string
        message: string
        type: string
      }
    }
    branch_list: string[]
    repo_url: string
  }
  status: string
  version: string
}

interface IStageItem {
  id: number
  name: string
  description: string
  description_en: string
  status: number
  created_time: string
  release: IRelease
  resource_version: IResourceVersion
  publish_id: number
  publish_version: string
  publish_validate_msg: string
  new_resource_version: string
  paasInfo?: IPaasInfo
}

interface IProps {
  stage?: IStageItem
  loading?: boolean
}

const {
  stage = {
    id: 0,
    name: '',
    description: '',
    description_en: '',
    status: 1,
    created_time: '',
    release: {
    // status: 'success',
    // status: 'failure',
      status: '',
      created_time: null,
      created_by: '',
    },
    resource_version: {
      version: '',
      id: 0,
      schema_version: '',
    },
    publish_id: 0,
    publish_version: '',
    publish_validate_msg: '',
    new_resource_version: '',
  },
  loading = false,
} = defineProps<IProps>();

const emit = defineEmits<{
  'check-log': [void]
  'publish': [void]
  'delist': [void]
}>();

const { t } = useI18n();
const router = useRouter();
const gatewayStore = useGateway();
const envStore = useEnv();
const featureFlagStore = useFeatureFlag();

const gatewayId = useRouteParams('id', 0, { transform: Number });

const data = ref<number[]>([]);

const requestCount = ref(0);

const status = computed(() => {
  if (!stage) {
    return '';
  }
  if (gatewayStore.isProgrammableGateway) {
    if (stage.paasInfo?.status === 'doing'
      || stage.paasInfo?.status === 'pending'
      || stage.paasInfo?.latest_deployment?.status === 'doing'
      || stage.paasInfo?.latest_deployment?.status === 'pending') {
      return 'doing';
    }
    // 未发布
    if (stage.status === 0 || stage.release?.status === 'unreleased') {
      return 'unreleased';
    }
    return stage.paasInfo?.status
      || stage.paasInfo?.latest_deployment?.status
      || stage.release?.status
      || '';
  }
  // 未发布
  if (stage.status === 0 || stage.release?.status === 'unreleased') {
    return 'unreleased';
  }
  return stage.release?.status;
});

// 发布操作是否禁用
const isActionDisabled = computed(() => {
  return status.value === 'doing' || !!stage.publish_validate_msg;
});

// 下架操作是否禁用
const isUnlistDisabled = computed(() => {
  return status.value === 'doing' || status.value === 'unreleased' || !!stage.publish_validate_msg;
});

const actionTooltipConfig = computed(() => {
  if (status.value === 'doing') {
    return {
      content: t('发布中'),
      disabled: false,
    };
  }
  if (!!stage.publish_validate_msg) {
    return {
      content: stage.publish_validate_msg,
      disabled: false,
    };
  }
  return { disabled: true };
});

const getRequestCount = async () => {
  const now = dayjs().unix();
  const sixHoursAgo = now - 6 * 60 * 60;
  const { instant } = await getGatewayMetricsInstant(gatewayId.value, {
    stage_id: stage.id,
    time_start: sixHoursAgo,
    time_end: now,
    metrics: 'requests_total',
  });
  requestCount.value = instant;
};

const getRequestTrend = async () => {
  if (!featureFlagStore.flags.ENABLE_RUN_DATA_METRICS) {
    return;
  }
  const now = dayjs().unix();
  const sixHoursAgo = now - 6 * 60 * 60;

  const { series } = await getGatewayMetrics(gatewayId.value, {
    stage_id: stage.id,
    time_start: sixHoursAgo,
    time_end: now,
    metrics: 'requests',
  });

  const seriesDatapoints = series?.[0]?.datapoints as [number, number][] || [];
  const results = [] as number[];
  let count = 0;

  seriesDatapoints.forEach((dataPoint, index) => {
    count += (dataPoint[0] || 0);
    if (index % 12 === 11) {
      results.push(count);
      count = 0;
    }
  });

  while (results.length < 6) {
    results.push(0);
  }

  data.value = results;
};

const handleCheckLog = () => {
  emit('check-log');
};

// 访问地址
const getStageUrl = (name: string) => {
  const keys: any = {
    api_name: gatewayStore.currentGateway!.name,
    stage_name: name,
    resource_path: '',
  };

  let url = envStore.env.BK_API_RESOURCE_URL_TMPL;

  for (const name of Object.keys(keys)) {
    const reg = new RegExp(`{${name}}`);
    url = url?.replace(reg, keys[name]);
  }
  return url;
};

const handlePublishClick = () => {
  emit('publish');
};

const handleDelistClick = () => {
  emit('delist');
};

const handleChartClick = () => {
  router.push({
    name: 'apigwDashboard',
    query: {
      time_span: 'now-6h',
      stage_id: stage.id,
    },
  });
};

onBeforeMount(async () => {
  if (stage.status === 1) {
    await Promise.all([
      getRequestCount(),
      getRequestTrend(),
    ]);
  }
});

</script>

<style lang="scss" scoped>

.stage-card-item {
  padding: 16px 24px 8px 44px;
  font-size: 12px;

  .card-header {
    position: relative;
    margin-bottom: 4px;

    .name {
      font-size: 16px;
      font-weight: 700;
      line-height: 22px;
      letter-spacing: 0;
      color: #313238;
    }

    .status-indicator {
      position: absolute;
      top: 9px;
      left: -22px;

      &:has(.dot) {
        left: -15px;
      }

      .dot {
        width: 8px;
        height: 8px;
        cursor: pointer;
        background: #e5f6ea;
        border: 1px solid #3fc06d;
        border-radius: 50%;

        &.success {
          background: #e5f6ea;
          border: 1px solid #3fc06d;
        }

        &.unreleased {
          background: #f0f1f5;
          border: 1px solid #c4c6cc;
        }

        &.delist {
          background: #f0f1f5;
          border: 1px solid #c4c6cc;
        }

        &.failure {
          background: #ffe6e6;
          border: 1px solid #ea3636;
        }
      }
    }
  }

  .card-main {

    .text-info {
      margin-bottom: 12px;

      .row {
        display: flex;
        font-size: 12px;
        line-height: 28px;
        color: #313238;
        align-items: center;

        .label {
          flex-shrink: 0;
        }

        .value {

          .suffix {
            margin-left: 4px;
            color: #979ba5;

            &.failure {
              color: #ea3636;
            }
          }
        }

        &.url {
          max-width: 430px;

          .value {
            overflow: hidden;
            color: #313238;
            text-overflow: ellipsis;
            white-space: nowrap;
          }
        }

        &.version {
          max-width: 430px;

          .value {
            overflow: hidden;
            font-weight: 700;
            text-overflow: ellipsis;
            white-space: nowrap;

            :deep(.bk-badge-main .bk-badge.pinned.top-right) {
              top: 10px;
              right: -6px;
            }

            .suffix {
              font-weight: normal;
            }
          }
        }
      }
    }
  }

  .divider {
    height: 1px;
    margin-block: 16px;
    background-color: #eaebf0;
  }

  .card-chart {
    display: flex;
    height: 60px;
    cursor: pointer;
    justify-content: space-between;

    .request-counter {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 16px;

      .label {
        line-height: 16px;
        color: #63656e;
      }

      .value {
        font-size: 16px;
        font-weight: 700;
        line-height: 18px;
        color: #313238;
      }

      &.empty-state {
        align-items: flex-start;

        .value {
          font-size: 12px;
          font-weight: normal;
          color: #979ba5;
        }
      }
    }
  }
}

</style>
