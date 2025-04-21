<template>
  <BkSideslider v-model:isShow="isShow" :width="1100" quick-close>
    <template #header>
      <div class="log-details-title">
        <div class="log-details-name">【{{ currentStage?.name || historyStage?.name }}】{{ t('发布日志详情') }}</div>
      </div>
    </template>
    <template #default>
      <div class="deploy-status-alert-wrapper">
        <div v-if="!isPaasDeployFinished || !isGatewayPublishFinished" class="deploying-alert">
          <div class="loading-icon">
            <Spinner />
          </div>
          <div class="main-text">{{ t('正在发布中，请稍等...') }}</div>
          <div class="mr50">{{ t('已耗时') }}: <span>{{ totalDuration }}s</span></div>
          <div>{{ t('操作人') }}: <span>{{ deployedBy }}</span></div>
        </div>
        <BkAlert
          v-else-if="
            isPaasDeployFailed
              || deployStatus === 'failure'
              || deployStatus === 'failed'
              || deployStatus === 'fail'
          "
          theme="error"
        >
          <div class="alert-content">
            <div class="mr80"><span class="pr4">{{ t('版本') }}</span><span
              class="pr4"
            >{{ version || historyVersion || '--' }}</span><span
              style="color: #ea3636;"
            >{{ t('发布失败') }}</span></div>
            <div class="mr50">{{ t('已耗时') }}: <span>{{ totalDuration }}s</span></div>
            <div>{{ t('操作人') }}: <span>{{ deployedBy }}</span></div>
            <div class="action">
              <div class="divider"></div>
              <BkButton style="height: 26px;font-size: 12px;" @click="handleRetry">{{ t('失败重试') }}</BkButton>
            </div>
          </div>
        </BkAlert>
        <BkAlert v-else theme="success">
          <div class="alert-content">
            <div class="mr80"><span class="pr4">{{ t('版本') }}</span><span
              class="pr4"
            >{{ version || historyVersion || '--' }}</span><span
              style="color: #2dcb56;"
            >{{ t('发布成功') }}</span></div>
            <div class="mr50">{{ t('已耗时') }}: <span>{{ totalDuration }}s</span></div>
            <div>{{ t('操作人') }}: <span>{{ deployedBy }}</span></div>
            <div class="action">
              <div class="divider"></div>
              <BkButton style="height: 26px;font-size: 12px;" @click="handleGoDebug">{{ t('去调试') }}</BkButton>
            </div>
          </div>
        </BkAlert>
      </div>
      <div class="log-details-main">
        <div class="main-process">
          <div v-for="(list, index) in paasTimelineLists" :key="index" class="paas-deploy-timeline-wrapper">
            <BkTimeline :list="list" class="mb20" />
          </div>
          <div class="gateway-publish-timeline-wrapper">
            <BkTimeline :list="gatewayPublishTimeline" class="mb20" />
          </div>
        </div>
        <div class="main-encoding">
          <MonacoEditor v-model="eventOutputLines" read-only />
        </div>
      </div>
    </template>
  </BkSideslider>
</template>

<script lang="ts" setup>
import {
  computed,
  h,
  ref,
  watch,
} from 'vue';
import {
  useRoute,
  useRouter,
} from 'vue-router';
import {
  getDeployEvents,
  getFinishedDeployEvents,
  IGatewayEvent,
  IGatewayEventTemplate,
  IPaasEventInstance,
} from '@/http/programmable';
import { useI18n } from 'vue-i18n';
import MonacoEditor from '@/components/ag-editor.vue';
import { useTimeoutPoll } from '@vueuse/core';
import { Spinner } from 'bkui-vue/lib/icon';
import dayjs from 'dayjs';
import { sumBy } from 'lodash';

interface ITimelineItem {
  description?: string;
  step?: number;
  size?: string;
  color?: string;
  filled?: boolean;
  tag?: any;
  content?: string;
  icon?: typeof Spinner;
  status?: 'doing' | 'success' | 'failure';
  duration?: number;
  isParent?: boolean;
  rawType?: string;
  nodeType?: string;
}

interface IProps {
  deployId?: number,
  historyId?: number,
  currentStage?: any,
  version?: string,
}

const props = withDefaults(defineProps<IProps>(), {
  deployId: 0,
  historyId: 0,
  currentStage: () => ({}),
  version: '',
});

const emit = defineEmits([
  'release-success',
  'release-doing',
]);

const { t } = useI18n();
const route = useRoute();
const router = useRouter();

const isShow = ref(false);
const paasEventTextLines = ref('');
const gatewayEventTextLines = ref('');

const paasEventInstances = ref<IPaasEventInstance[]>([]);
const gatewayEventTemplates = ref<IGatewayEventTemplate[]>([]);
const gatewayEvents = ref<IGatewayEvent[]>([]);

const isPaasDeployFinished = ref(false);
const isPaasDeployFailed = ref(false);
const deployedBy = ref('');
const deployStatus = ref('');

const historyStage = ref<{ id: number, name: string } | null>();
const historyVersion = ref('');

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
          style: { color: 'black', fontWeight: '700' },
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
        instanceDuration += stepDuration;
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

const gatewayPublishTimeline = computed(() => {
  let list: ITimelineItem[] = [];// 整理步骤

  // 生成步骤节点
  list = gatewayEventTemplates.value.map((eventTemplate) => {
    const step: any = {
      // size: 'large',
      tag: eventTemplate.description,
    };
    const currentEvents = gatewayEvents.value.filter(event => event.step === eventTemplate.step);

    // 根据步骤状态赋予不同的图标样式
    if (currentEvents.some(event => event.status === 'failure')) {
      step.color = 'red';
      step.status = 'failure';
    } else if (currentEvents.some(event => event.status === 'success')) {
      step.color = 'green';
      step.filled = true;
      step.status = 'success';
    } else {
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
    } else {
      // 如果当前步骤已结束，则用下一个步骤的开始时间计算时间差
      if (nextEvents.length) {
        const endTime = dayjs(nextEvents.find(event => event.status === 'doing')?.created_time);
        duration = endTime.diff(startTime, 's', true) || 0;
      } else {
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

  return list;
});

const gatewayPublishTotalDuration = computed(() => {
  return sumBy(gatewayPublishTimeline.value, step => step.duration || 0);
});

const paasDeployTotalDuration = computed(() => {
  return paasTimelineLists.value.reduce((duration, timelineList) => {
    timelineList.forEach((node) => {
      if (node.isParent) {
        duration += node.duration;
      }
    });
    return duration;
  }, 0);
});

const totalDuration = computed(() => {
  return gatewayPublishTotalDuration.value + paasDeployTotalDuration.value;
});

const isGatewayPublishFinished = computed(() => {
  return deployStatus.value === 'success' || deployStatus.value === 'failure';
});

const eventOutputLines = computed(() => {
  // 当 PAAS 部署完成后
  if (isPaasDeployFinished.value) {
    return paasEventTextLines.value.concat(gatewayEventTextLines.value);
  }
  return paasEventTextLines.value;
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
  () => isShow.value,
  () => {
    if (!isShow.value) {
      if (isGatewayPublishFinished.value) {
        emit('release-success');
      } else {
        emit('release-doing');
      }
      pausePoll();
      resetStates();
    }
  },
);

watch(
  () => props.deployId,
  () => {
    if (props.deployId && isShow.value) {
      startPoll();
    }
  },
);

watch(
  () => props.historyId,
  async () => {
    // 查询静态的发布记录，调用一次接口即可，不要轮询
    if (props.historyId && isShow.value) {
      await getEvents();
    }
  },
);

watch(isGatewayPublishFinished, () => {
  if (isPaasDeployFinished.value && isGatewayPublishFinished) {
    pausePoll();
  }
});

// 获取日志列表
const getEvents = async () => {
  const requestFunc = props.deployId ? getDeployEvents : getFinishedDeployEvents;

  const {
    stage: stageResponse,
    resource_version_display,
    created_by,
    events_template,
    events: gatewayEventsResponse,
    paas_deploy_info: paasResponse,
    status,
  } = await requestFunc(apigwId.value, props.deployId || props.historyId);

  historyStage.value = stageResponse || null;
  historyVersion.value = resource_version_display || '';
  deployedBy.value = created_by || '';
  deployStatus.value = status || '';

  paasEventInstances.value = paasResponse.events_instance || [];
  gatewayEventTemplates.value = events_template || [];
  gatewayEvents.value = gatewayEventsResponse || [];

  const paasEvents = paasResponse.events || [];
  const paasOutputLines: string[] = [];
  const gatewayOutputLines: string[] = [];

  paasEvents.forEach((event) => {
    let line = '';
    try {
      const data = JSON.parse(event.data);
      if (data.line) {
        line = data.line;
      }
    } catch {
      line = event.data;
    } finally {
      if (line && !line.endsWith('\n')) {
        line += '\n';
      }
      paasOutputLines.push(line);
    }
  });

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

  // 有错误事件时
  if (paasEventInstances.value.some(instance => instance.status === 'failed')) {
    paasEventInstances.value = [];
    isPaasDeployFinished.value = true;
    isPaasDeployFailed.value = true;
    pausePoll();
    return;
  }

  const lastInstance = paasEventInstances.value[paasEventInstances.value.length - 1];

  if (lastInstance?.status === 'successful') {
    isPaasDeployFinished.value = true;
    isPaasDeployFailed.value = false;
    // pausePoll();
  }
};

const { pause: pausePoll, resume: startPoll } = useTimeoutPoll(getEvents, 2000, {
  immediate: false,
});

const showSideslider = () => {
  isShow.value = true;
};

const handleRetry = () => {
  resetStates();
  startPoll();
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
  isPaasDeployFinished.value = false;
  isPaasDeployFailed.value = false;
};

const handleGoDebug = () => {
  router.replace({ name: 'apigwOnlineTest' });
};

defineExpose({
  showSideslider,
});
</script>

<style lang="scss" scoped>
.log-details-title {
  display: flex;
  align-items: center;

  .log-details-name {
    font-size: 14px;
    color: #2c2e35;
    margin-right: 8px;
    font-weight: 700;
  }

  .title-publish-info {
    font-size: 12px;
    color: #63656e;
    margin-left: 32px;

    span {
      color: #2c2e35;
    }
  }
}

.deploy-status-alert-wrapper {
  margin-bottom: 16px;
  padding: 16px 16px 0;

  :deep(.bk-alert-wraper) {
    align-items: center;
  }

  .alert-content {
    display: flex;
    align-items: center;
  }

  .deploying-alert {
    display: flex;
    align-items: center;
    height: 42px;
    background: #eaebf0;
    border-radius: 2px;
    color: #63656e;
    padding: 8px 10px;
    font-size: 12px;

    .loading-icon {
      margin-right: 9px;
      //color: blue;
      color: #3a84ff;
      font-size: 20px;
    }

    .main-text {
      margin-right: 86px;
    }
  }

  .action {
    margin-left: 21px;
    display: flex;
    align-items: center;

    .divider {
      width: 1px;
      height: 14px;
      background-color: #c4c6cc;
      margin-right: 21px;
    }
  }
}

.log-details-main {
  display: flex;
  align-items: center;
  padding: 0 16px;
  height: calc(100vh - 128px);
  box-sizing: border-box;

  .main-process {
    width: 270px;
    height: 100%;
    background-color: #f5f7fa;
    overflow-y: auto;
    padding: 16px;
    box-sizing: border-box;
    margin-right: 16px;

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
        border-left-style: dashed;
        padding-bottom: 0;

        &:before {
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
          margin-top: 0;
          font-size: 12px;
          color: black;
          font-weight: 700;
        }
      }

      :deep(.bk-timeline .bk-timeline-dot) {
        border-left-style: dashed;
        padding-bottom: 0;

        &:before {
          top: -9px;
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
