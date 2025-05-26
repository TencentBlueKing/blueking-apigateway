<template>
  <div class="stage-card-item">
    <div class="card-header">
      <div class="name">{{ stage.name }}</div>
      <div class="status-indicator">
        <Spinner v-if="status === 'doing'" style="color:#3a84f6; font-size: 16px;" />
        <div
          v-else
          v-bk-tooltips="{
            content: getStatusText(status),
            disabled: !getStatusText(status),
          }"
          :class="['dot', status]"
        >
        </div>
      </div>
    </div>
    <div class="card-main">
      <div class="text-info">
        <div class="row url">
          <div class="label">{{ t('访问地址') }}：</div>
          <div v-bk-tooltips="getStageUrl(stage.name)" class="value">{{ getStageUrl(stage.name) }}</div>
        </div>
        <div class="row version">
          <div class="label">{{ t('当前资源版本') }}：</div>
          <div v-if="status === 'unreleased'" class="value">
            <BkTag
              size="small"
              style="font-weight: normal;"
              theme="warning"
            >
              {{ t('未发布') }}
            </BkTag>
          </div>
          <div v-else class="value">
            <BkBadge
              v-if="!common.isProgrammableGateway && stage.new_resource_version"
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
            <span v-if="status === 'failure'" :class="['suffix', status]">（{{
              stage.paasInfo?.latest_deployment?.version || stage.paasInfo?.version || '--'
            }} 版本发布失败，<span><BkButton text theme="primary" @click.stop="handleCheckLog">{{
              t('查看日志')
            }}</BkButton></span>）</span>
            <!-- 发布中 -->
            <span v-else-if="status === 'doing'" class="suffix">（<span
              style="font-weight: bold;"
            >{{
              stage.paasInfo?.latest_deployment?.version || stage.publish_version || '--'
            }}</span> 版本正在发布中，<span><BkButton text theme="primary" @click.stop="handleCheckLog">{{
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
      <div class="main-actions">
        <BkButton
          class="mr8"
          size="small"
          theme="primary"
          v-bk-tooltips="actionTooltipConfig"
          :disabled="isActionDisabled"
          :loading="loading"
          @click.stop="handlePublishClick"
        >
          {{ t('发布资源') }}
        </BkButton>
        <BkButton
          size="small"
          v-bk-tooltips="actionTooltipConfig"
          :disabled="isUnlistDisabled"
          :loading="loading"
          @click.stop="handleDelistClick"
        >
          {{ t('下架') }}
        </BkButton>
      </div>
    </div>
    <div class="divider"></div>
    <div class="card-chart" @click.stop="handleChartClick">
      <div :class="{ 'empty-state': status === 'unreleased' }" class="request-counter">
        <div class="label">{{ t('总请求数') }}</div>
        <div class="value">{{ status === 'unreleased' ? t('尚未发布，无数据') : requestCount }}
        </div>
      </div>
      <div class="item-chart-wrapper">
        <StageCardLineChart v-if="status !== 'unreleased'" :data="data" :mount-id="uniqueId()" />
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import {
  computed,
  onBeforeMount,
  ref,
} from 'vue';
import { useCommon } from '@/store';
import { useGetGlobalProperties } from '@/hooks';
import { Spinner } from 'bkui-vue/lib/icon';
import StageCardLineChart from '@/views/stage/overview/comps/stage-card-line-chart.vue';
import { getStatusText } from '@/common/util';
import {
  getApigwMetrics,
  getApigwMetricsInstant,
} from '@/http';
import dayjs from 'dayjs';
import { uniqueId } from 'lodash';

interface IRelease {
  status: string;
  created_time: null | string;
  created_by: string;
}

interface IResourceVersion {
  version: string;
  id: number;
  schema_version: string;
}

interface IPaasInfo {
  branch: string;
  commit_id: string;
  created_by: string | null;
  created_time: string;
  deploy_id: string;
  latest_deployment: {
    branch: string;
    commit_id: string;
    deploy_id: string;
    history_id: number;
    status: string;
    version: string;
  };
  repo_info: {
    branch_commit_info: {
      [branch: string]: {
        commit_id: string;
        extra: object;
        last_update: string;
        message: string;
        type: string;
      }
    };
    branch_list: string[];
    repo_url: string;
  };
  status: string;
  version: string;
}

interface IStageItem {
  id: number;
  name: string;
  description: string;
  description_en: string;
  status: number;
  created_time: string;
  release: IRelease;
  resource_version: IResourceVersion;
  publish_id: number;
  publish_version: string;
  publish_validate_msg: string;
  new_resource_version: string;
  paasInfo?: IPaasInfo;
}

interface IProps {
  stage: IStageItem,
  loading?: boolean,
}

const props = withDefaults(defineProps<IProps>(), {
  stage: () => ({
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
  }),
  loading: false,
});

const emit = defineEmits<{
  'check-log': [void],
  'publish': [void],
  'delist': [void],
}>();

const { t } = useI18n();
const { GLOBAL_CONFIG } = useGetGlobalProperties();
const router = useRouter();
const common = useCommon();

const data = ref<number[]>([]);

const requestCount = ref(0);

const status = computed(() => {
  if (!props.stage) {
    return '';
  }
  if (common.isProgrammableGateway) {
    if (props.stage.paasInfo?.status) {
      return props.stage.paasInfo?.status;
    }
    // 未发布
    if (props.stage.status === 0 || props.stage.release?.status === 'unreleased') {
      return 'unreleased';
    }
    if (props.stage.paasInfo?.latest_deployment?.status) {
      return props.stage.paasInfo?.latest_deployment?.status;
    }
  }
  // 未发布
  if (props.stage.status === 0 || props.stage.release?.status === 'unreleased') {
    return 'unreleased';
  }
  return props.stage.release?.status;
});

// 发布操作是否禁用
const isActionDisabled = computed(() => {
  return status.value === 'doing' || !!props.stage.publish_validate_msg;
});

// 下架操作是否禁用
const isUnlistDisabled = computed(() => {
  return status.value === 'doing' || status.value === 'unreleased' || !!props.stage.publish_validate_msg;
});

const actionTooltipConfig = computed(() => {
  if (status.value === 'doing') {
    return { content: t('发布中'), disabled: false };
  }
  if (!!props.stage.publish_validate_msg) {
    return { content: props.stage.publish_validate_msg, disabled: false };
  }
  return {
    disabled: true,
  };
});

const getRequestCount = async () => {
  const now = dayjs().unix();
  const sixHoursAgo = now - 6 * 60 * 60;
  const { instant } = await getApigwMetricsInstant(common.apigwId, {
    stage_id: props.stage.id,
    time_start: sixHoursAgo,
    time_end: now,
    metrics: 'requests_total',
  });
  requestCount.value = instant;
};

const getRequestTrend = async () => {
  const now = dayjs().unix();
  const sixHoursAgo = now - 6 * 60 * 60;

  const { series } = await getApigwMetrics(common.apigwId, {
    stage_id: props.stage.id,
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
    api_name: common.apigwName,
    stage_name: name,
    resource_path: '',
  };

  let url = GLOBAL_CONFIG.STAGE_DOMAIN;
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
  router.push({ name: 'apigwDashboard', query: { time_span: 'now-6h', stage_id: props.stage.id } });
};

onBeforeMount(async () => {
  await Promise.all([
    getRequestCount(),
    getRequestTrend(),
  ]);
});

</script>

<style lang="scss" scoped>

.stage-card-item {
  font-size: 12px;
  background: #fff;
  padding: 16px 24px 8px 44px;
  box-shadow: 0 2px 4px 0 #1919290d;;
  border-radius: 2px;

  &:hover {
    box-shadow: 0 2px 4px 0 #0000001a, 0 2px 4px 0 #1919290d;
  }

  .card-header {
    position: relative;
    margin-bottom: 4px;

    .name {
      font-weight: 700;
      font-size: 16px;
      color: #313238;
      letter-spacing: 0;
      line-height: 22px;
    }

    .status-indicator {
      position: absolute;
      top: 2px;
      left: -22px;

      &:has(.dot) {
        left: -15px;
      }

      .dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        cursor: pointer;
        border: 1px solid #3fc06d;
        background: #e5f6ea;

        &.success {
          border: 1px solid #3fc06d;
          background: #e5f6ea;
        }

        &.unreleased {
          border: 1px solid #c4c6cc;
          background: #f0f1f5;
        }

        &.delist {
          border: 1px solid #c4c6cc;
          background: #f0f1f5;
        }

        &.failure {
          border: 1px solid #ea3636;
          background: #ffe6e6;
        }
      }
    }
  }

  .card-main {
    .text-info {
      margin-bottom: 12px;

      .row {
        color: #313238;
        font-size: 12px;
        line-height: 28px;
        display: flex;
        align-items: center;

        .label {
          flex-shrink: 0;
        }

        .value {
          .suffix {
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
            white-space: nowrap;
            text-overflow: ellipsis;
            color: #313238;
          }
        }

        &.version {
          max-width: 430px;
          .value {
            font-weight: 700;
            overflow: hidden;
            white-space: nowrap;
            text-overflow: ellipsis;

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
    height: 60px;
    display: flex;
    justify-content: space-between;
    cursor: pointer;

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
        font-weight: 700;
        font-size: 16px;
        line-height: 18px;
        color: #313238;
      }

      &.empty-state {
        align-items: flex-start;

        .value {
          font-weight: normal;
          font-size: 12px;
          color: #979ba5;
        }
      }
    }
  }
}

</style>
