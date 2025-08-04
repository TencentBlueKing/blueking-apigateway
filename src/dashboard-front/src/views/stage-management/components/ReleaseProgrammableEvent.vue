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
  <BkSideslider
    v-model:is-show="isShow"
    :width="1100"
    quick-close
  >
    <template #header>
      <div class="log-details-title">
        <div class="log-details-name">
          【{{ stage?.name || historyStage?.name }}】{{ t('发布日志详情') }}
        </div>
      </div>
    </template>
    <template #default>
      <div class="deploy-status-alert-wrapper">
        <!-- 环境下线操作，展示下线状态 -->
        <div
          v-if="source === 'stage_disable'"
          class="deploying-alert"
        >
          <div class="main-text">
            {{ t('已下线') }}
          </div>
        </div>
        <div
          v-else-if="status === 'pending' || status === 'doing'"
          class="deploying-alert"
        >
          <div class="loading-icon">
            <Spinner />
          </div>
          <div class="main-text">
            {{ t('正在发布中，请稍等...') }}
          </div>
          <div class="mr-50px">
            {{ t('已耗时') }}: <span>{{ totalDuration }}s</span>
          </div>
        </div>
        <BkAlert
          v-else-if="status === 'fail' || status === 'failed' || status === 'failure'"
          theme="error"
        >
          <div class="alert-content">
            <div class="mr-80px">
              <span class="pr-4px">{{ t('版本') }}</span><span
                class="pr-4px"
              >{{ historyVersion || stage?.paasInfo?.latest_deployment?.version || version || '--' }}</span><span
                class="color-#ea3636"
              >{{ t('发布失败') }}</span>
            </div>
            <div class="mr-50px">
              {{ t('已耗时') }}: <span>{{ totalDuration }}s</span>
            </div>
            <div class="action">
              <div class="divider" />
              <BkButton
                class="h-26px text-12px"
                @click="handleRetry"
              >
                {{ t('失败重试') }}
              </BkButton>
            </div>
          </div>
        </BkAlert>
        <BkAlert
          v-else
          theme="success"
        >
          <div class="alert-content">
            <div class="mr-80px">
              <span class="pr-4px">{{ t('版本') }}</span><span
                class="pr-4px"
              >{{ historyVersion || stage?.paasInfo?.latest_deployment?.version || version || '--' }}</span><span
                class="color-#2dcb56"
              >{{ t('发布成功') }}</span>
            </div>
            <div class="mr-50px">
              {{ t('已耗时') }}: <span>{{ totalDuration }}s</span>
            </div>
            <div class="action">
              <div class="divider" />
              <BkButton
                class="h-26px text-12px"
                @click="handleGoDebug"
              >
                {{ t('去调试') }}
              </BkButton>
            </div>
          </div>
        </BkAlert>
      </div>
      <div class="log-details-main">
        <div class="main-process">
          <div
            v-for="(list, index) in paasTimelineLists"
            :key="index"
            class="paas-deploy-timeline-wrapper"
          >
            <BkTimeline
              :list="list"
              class="mb-20px"
            />
          </div>
          <div class="gateway-publish-timeline-wrapper">
            <BkTimeline
              :list="gatewayPublishTimeline"
              class="mb-20px"
            />
          </div>
        </div>
        <div class="main-encoding">
          <AgEditor
            ref="editorRef"
            v-model="eventOutputLines"
            read-only
          />
        </div>
      </div>
    </template>
  </BkSideslider>
</template>

<script lang="ts" setup>
import {
  type IEventResponse,
  type IGatewayEvent,
  type IGatewayEventTemplate,
  type IPaasEventInstance,
  getDeployEvents,
  getFinishedDeployEvents,
} from '@/services/source/programmable.ts';
import AgEditor from '@/components/ag-editor/Index.vue';
import { useTimeoutPoll } from '@vueuse/core';
import { Spinner } from 'bkui-lib/icon';
import dayjs from 'dayjs';
import { sumBy } from 'lodash-es';

interface ITimelineItem {
  description?: string
  step?: number
  size?: string
  color?: string
  filled?: boolean
  tag?: any
  content?: string
  icon?: typeof Spinner
  status?: 'doing' | 'success' | 'failure'
  duration?: number
  isParent?: boolean
  rawType?: string
  nodeType?: string
}

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
  deployId?: string
  historyId?: number
  stage?: IStageItem | null
  version?: string
  history?: IEventResponse | null
}

const {
  deployId = '',
  historyId = 0,
  stage = {
    id: 0,
    name: '',
    description: '',
    description_en: '',
    status: 1,
    created_time: '',
    release: {
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
    paasInfo: {
      branch: '',
      commit_id: '',
      created_by: '',
      created_time: '',
      deploy_id: '',
      latest_deployment: {
        branch: '',
        commit_id: '',
        deploy_id: '',
        history_id: 0,
        status: '',
        version: '',
      },
      repo_info: {
        branch_commit_info: {},
        branch_list: [],
        repo_url: '',
      },
      status: '',
      version: '',
    },
  },
  version = '',
  history = null,
} = defineProps<IProps>();

const emit = defineEmits<{
  'release-success': [void]
  'hide-when-pending': [void]
  'retry': [void]
}>();

const { t } = useI18n();
const route = useRoute();
const router = useRouter();

const isShow = ref(false);
const paasEventTextLines = ref('');
const gatewayEventTextLines = ref('');

const paasEventInstances = ref<IPaasEventInstance[]>([]);
const gatewayEventTemplates = ref<IGatewayEventTemplate[]>([]);
const gatewayEvents = ref<IGatewayEvent[]>([]);

const deployedBy = ref('');
const deployStatus = ref('');

const historyStage = ref<{
  id: number
  name: string
} | null>();
const historyVersion = ref('');

// 操作类型
const source = ref('');

const editorRef = ref();

const apigwId = computed(() => +route.params?.id);

const paasTimelineLists = computed(() => {
  const list: ITimelineItem[][] = [];
  paasEventInstances.value.forEach((instance) => {
    const subList: ITimelineItem[] = [];
    let instanceDuration = 0;
    subList.push({
      tag: h(
        'div',
        {
          style: {
            color: 'black',
            fontWeight: '700',
          },
        },
        instance.display_name,
      ),
      content: '',
      rawType: instance.type,
      isParent: true,
      nodeType: 'vnode',
      ...getDotStyles(instance.status),
    });

    if (instance.steps?.length) {
      instance.steps.forEach((step) => {
        const stepDuration = getDotDuration(step.start_time, step.complete_time);
        instanceDuration += stepDuration || 0;
        subList.push({
          tag: step.display_name,
          content: getDotDurationText(stepDuration),
          rawType: step.name,
          isParent: false,
          ...getDotStyles(step.status),
        });
      });
    }

    subList[0].content = `${instanceDuration}s`;
    subList[0].duration = instanceDuration;
    list.push(subList);
  });
  return list;
});

// 网关发布的时间线数据
const gatewayPublishTimeline = computed(() => {
  let list: ITimelineItem[] = [];// 整理步骤

  // 生成步骤节点
  list = gatewayEventTemplates.value.map((eventTemplate) => {
    const step: any = {
      // size: 'large',
      tag: eventTemplate.description,
      isParent: false,
    };
    const currentEvents = gatewayEvents.value.filter(event => event.step === eventTemplate.step);

    // 根据步骤状态赋予不同的图标样式
    if (currentEvents.some(event => event.status === 'failure')) {
      step.color = 'red';
      step.status = 'failure';
    }
    else if (currentEvents.some(event => event.status === 'success')) {
      step.color = 'green';
      step.filled = true;
      step.status = 'success';
    }
    else {
      step.status = 'doing';
      // 整个发布任务在进行中时才处理图标样式
      if (deployStatus.value === 'pending' || deployStatus.value === 'doing') {
        // 给已结束步骤的下一个在 doing 状态的步骤显示加载图标
        const prevEvents = gatewayEvents.value.filter(event => event.step === eventTemplate.step - 1);
        if (prevEvents.find(event => event.status === 'success' || event.status === 'failure')) {
          step.color = 'blue';
          step.icon = Spinner;
        }
      }
    }

    // 计算每个步骤使用的时间
    const startTime = dayjs(currentEvents.find(event => event.status === 'doing')?.created_time);
    let duration = 0;
    const nextEvents = gatewayEvents.value.filter(event => event.step === eventTemplate.step + 1);

    // 当前步骤未完成，则计算当前步骤已使用的时间
    if (step.status === 'doing') {
      duration = dayjs().diff(startTime, 's', true) || 0;
    }
    else {
      // 如果当前步骤已结束，则用下一个步骤的开始时间计算时间差
      if (nextEvents.length) {
        const endTime = dayjs(nextEvents.find(event => event.status === 'doing')?.created_time);
        duration = endTime.diff(startTime, 's', true) || 0;
      }
      else {
        // 没有下一个步骤就用当前步骤自己的 created_time 计算时间差
        const endTime = dayjs(currentEvents.find(event => event.status === 'success' || event.status === 'failure')?.created_time);
        duration = endTime.diff(startTime, 's', true) || 0;
      }
    }

    // 步骤展示文本
    const fixedDuration = +duration.toFixed(2);
    step.content = `<span style="font-size: 12px;">${fixedDuration}s</span>`;
    step.duration = fixedDuration;

    return step;
  });

  const allStepDuration = sumBy(list, step => step.duration || 0);

  const parentNode: ITimelineItem = {
    color: 'green',
    content: `${allStepDuration}s`,
    duration: allStepDuration,
    filled: true,
    status: 'success',
    isParent: true,
    tag: h(
      'div',
      {
        style: {
          color: 'black',
          fontWeight: '700',
        },
      },
      t('网关发布'),
    ),
    nodeType: 'vnode',
  };

  if (deployStatus.value === 'failed') {
    delete parentNode.icon;
    delete parentNode.color;
    parentNode.filled = false;
  }
  else if (list.some(step => step.status === 'doing')) {
    parentNode.status = 'doing';
    parentNode.color = 'blue';
    parentNode.icon = Spinner;
    parentNode.filled = false;
  }
  else if (list.some(step => step.status === 'failure')) {
    parentNode.color = 'red';
    parentNode.status = 'failure';
    parentNode.filled = false;
  }

  return [
    parentNode,
    ...list,
  ];
});

const gatewayPublishTotalDuration = computed(() => {
  return gatewayPublishTimeline.value?.[0].duration || 0;
});

const paasDeployTotalDuration = computed(() => {
  return paasTimelineLists.value.reduce((duration, timelineList) => {
    timelineList.forEach((node) => {
      if (node.isParent) {
        duration += node.duration || 0;
      }
    });
    return duration;
  }, 0);
});

const totalDuration = computed(() => {
  return paasDeployTotalDuration.value + gatewayPublishTotalDuration.value;
});

const eventOutputLines = computed(() => {
  // 当 PAAS 部署完成后
  if (isFinished.value) {
    return paasEventTextLines.value.concat(gatewayEventTextLines.value);
  }
  return paasEventTextLines.value;
});

// 发布记录给的 status
const eventRecordStatus = computed(() => history?.status || '');

const status = computed(() => {
  if (eventRecordStatus.value === 'failure') {
    return 'failure';
  }
  if (deployStatus.value) {
    return deployStatus.value;
  }
  if (stage?.paasInfo?.status) {
    return stage.paasInfo.status;
  }
  return '';
});

const isFinished = computed(() => {
  return status.value !== 'pending' && status.value !== 'doing';
});

const statusStyleMap: Record<string, any> = {
  successful: {
    color: 'green',
    filled: true,
    icon: undefined,
  },
  failed: {
    color: 'red',
    icon: undefined,
  },
  pending: {
    color: 'blue',
    icon: Spinner,
    // size: 'large',
  },
  success: {
    color: 'green',
    filled: true,
    icon: undefined,
  },
  failure: {
    color: 'red',
    icon: undefined,
  },
  doing: {
    color: 'blue',
    icon: Spinner,
    // size: 'large',
  },
};

watch(
  isShow,
  () => {
    if (!isShow.value) {
      if (isFinished.value) {
        emit('release-success');
      }
      else {
        emit('hide-when-pending');
      }
      pausePoll();
      resetStates();
    }
    else {
      getEvents();
      startPoll();
    }
  },
);

// 获取日志列表
const getEvents = async () => {
  const requestFunc = deployId ? getDeployEvents : getFinishedDeployEvents;

  const {
    stage: stageResponse,
    resource_version_display,
    created_by,
    events_template,
    events: gatewayEventsResponse,
    paas_deploy_info: paasResponse,
    source: sourceResponse,
    status,
  } = await requestFunc(apigwId.value, deployId || historyId);

  historyStage.value = stageResponse || null;
  historyVersion.value = resource_version_display || '';
  deployedBy.value = created_by || '';
  // 记录 paas 部署状态，断路检查是否失败
  deployStatus.value = paasResponse.deploy_result?.status === 'failed' ? 'failed' : (status || '');
  source.value = sourceResponse || '';

  paasEventInstances.value = (paasResponse.events_instance && Array.isArray(paasResponse.events_instance))
    ? paasResponse.events_instance
    : [];
  gatewayEventTemplates.value = events_template || [];
  gatewayEvents.value = gatewayEventsResponse || [];

  const paasEvents = (paasResponse.events && Array.isArray(paasResponse.events)) ? paasResponse.events : [];
  let paasOutputLines: string[] = [];
  const gatewayOutputLines: string[] = [];

  const paasLogs = paasResponse?.deploy_result?.logs
    || paasResponse?.deploy_result?.log
    || paasResponse?.deploy_result?.err_detail;

  // events 为空，且 deploy_result 里有返回信息，实则paas部署出问题了，展示 logs
  if (!paasEvents.length && paasLogs) {
    paasOutputLines = [
      paasLogs || 'Error',
      '\n\n',
    ];
    if (!paasEventInstances.value.length) {
      paasEventInstances.value = [
        {
          display_name: t('PaaS 部署'),
          type: '',
          steps: [],
          display_blocks: null,
          uuid: '',
          status: 'failed',
          start_time: '',
          complete_time: '',
        },
      ];
    }
  }
  else {
    paasEvents.forEach((event) => {
      let line = '';
      try {
        const data = JSON.parse(event.data);
        if (data.line) {
          line = data.line;
        }
      }
      catch {
        line = event.data;
      }
      finally {
        if (line && !line.endsWith('\n')) {
          line += '\n';
        }
        paasOutputLines.push(line);
      }
    });
  }

  gatewayEvents.value.forEach((event) => {
    let line = event.status === 'failure'
      ? `  Err_msg: ${event.detail?.err_msg ?? 'Unknown error'}`
      : `${event.created_time}  ${event.name}  ${event.status}`;

    if (!line.endsWith('\n')) {
      line += '\n';
    }

    gatewayOutputLines.push(line);
  });

  paasEventTextLines.value = paasOutputLines.join('');
  gatewayEventTextLines.value = gatewayOutputLines.join('');

  editorRef.value?.setCursorPos({ toBottom: true });
  if (isFinished.value) {
    pausePoll();
  }
};

const { pause: pausePoll, resume: startPoll } = useTimeoutPoll(getEvents, 2000, { immediate: false });

const showSideslider = () => {
  isShow.value = true;
};

const getDotStyles = (status?: string | null) => {
  if (!status) {
    return {};
  }
  return statusStyleMap[status] || {};
};

const getDotDuration = (start: string | null, end: string | null) => {
  if (!start || !end) {
    return null;
  }
  return dayjs(end).diff(start, 's', true) || 0;
};

const getDotDurationText = (duration: number | null) => {
  return duration === null ? '--' : `${duration}s`;
};

const resetStates = () => {
  paasEventTextLines.value = '';
  gatewayEventTextLines.value = '';
  paasEventInstances.value = [];
  gatewayEventTemplates.value = [];
  gatewayEvents.value = [];
  deployedBy.value = '';
  deployStatus.value = '';
  historyStage.value = null;
  historyVersion.value = '';
  source.value = '';
};

const handleGoDebug = () => {
  router.replace({
    name: 'OnlineDebugging',
    query: { stage_id: stage!.id || historyStage.value!.id },
  });
};

const handleRetry = () => {
  emit('retry');
  resetStates();
  isShow.value = false;
  // startPoll();
};

defineExpose({ showSideslider });
</script>

<style lang="scss" scoped>
.log-details-title {
  display: flex;
  align-items: center;

  .log-details-name {
    margin-right: 8px;
    font-size: 14px;
    font-weight: 700;
    color: #2c2e35;
  }

  .title-publish-info {
    margin-left: 32px;
    font-size: 12px;
    color: #63656e;

    span {
      color: #2c2e35;
    }
  }
}

.deploy-status-alert-wrapper {
  padding: 16px 16px 0;
  margin-bottom: 16px;

  :deep(.bk-alert-wraper) {
    align-items: center;
  }

  .alert-content {
    display: flex;
    align-items: center;
  }

  .deploying-alert {
    display: flex;
    height: 42px;
    padding: 8px 10px;
    font-size: 12px;
    color: #63656e;
    background: #eaebf0;
    border-radius: 2px;
    align-items: center;

    .loading-icon {
      margin-right: 9px;
      font-size: 20px;

      // color: blue;
      color: #3a84ff;
    }

    .main-text {
      margin-right: 86px;
    }
  }

  .action {
    display: flex;
    margin-left: 21px;
    align-items: center;

    .divider {
      width: 1px;
      height: 14px;
      margin-right: 21px;
      background-color: #c4c6cc;
    }
  }
}

.log-details-main {
  display: flex;
  height: calc(100vh - 128px);
  padding: 0 16px;
  box-sizing: border-box;
  align-items: center;

  .main-process {
    width: 270px;
    height: 100%;
    padding: 16px;
    margin-right: 16px;
    overflow-y: auto;
    background-color: #f5f7fa;
    box-sizing: border-box;

    .paas-deploy-timeline-wrapper {

      :deep(.bk-timeline .bk-timeline-dot .bk-timeline-section) {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: 10px;

        .bk-timeline-title {
          padding-bottom: 0;
          font-size: 12px;
        }

        .bk-timeline-content {
          font-size: 12px;
        }
      }

      :deep(.bk-timeline .bk-timeline-dot) {
        padding-bottom: 0;
        border-left-style: dashed;

        &::before {
          top: -11px;
        }

        // Spinner 图标

        svg {
          width: 18px !important;
          height: 18px !important;
        }
      }
    }

    .gateway-publish-timeline-wrapper {

      :deep(.bk-timeline .bk-timeline-dot .bk-timeline-section) {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: 10px;

        .bk-timeline-title {
          padding-bottom: 0;
          font-size: 12px;
        }

        .bk-timeline-content {
          font-size: 12px;
        }
      }

      :deep(.bk-timeline .bk-timeline-dot) {
        padding-bottom: 0;
        border-left-style: dashed;

        &::before {
          top: -11px;
        }

        // Spinner 图标

        svg {
          width: 18px !important;
          height: 18px !important;
        }
      }
    }
  }

  .main-encoding {
    flex: 1;
    height: 100%;
  }
}

:deep(.codemirror .monaco-editor) {
  top: 0;
}
</style>
