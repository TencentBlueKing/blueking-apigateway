<template>
  <bk-sideslider v-model:isShow="isShow" :width="960" quick-close>
    <template #header>
      <div class="log-details-title">
        <div class="log-details-name">【{{ currentStage?.name }}】{{ t('发布日志详情') }}</div>
      </div>
    </template>
    <template #default>
      <div class="deploy-status-alert-wrapper">
        <div v-if="!isDeployFinished" class="deploying-alert">
          <div class="loading-icon">
            <Spinner />
          </div>
          <div class="main-text">{{ t('正在发布中，请稍等...') }}</div>
          <div class="mr50">{{ t('已耗时') }}: <span>{{ totalDuration }}s</span></div>
          <div>{{ t('操作人') }}: <span>{{ deployedBy }}</span></div>
        </div>
        <BkAlert v-else-if="isDeployFailed" theme="error">
          <div class="alert-content">
            <div class="mr80"><span class="pr4">{{ t('版本') }}</span><span class="pr4">1.0.2</span><span
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
            <div class="mr80"><span class="pr4">{{ t('版本') }}</span><span class="pr4">1.0.2</span><span
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
          <div v-for="(list, index) in timelineLists" :key="index">
            <bk-timeline
              :list="list"
              class="mb20"
            />
          </div>
        </div>
        <div class="main-encoding">
          <editor-monaco v-model="eventTextLines" :read-only="true" />
        </div>
      </div>
    </template>
  </bk-sideslider>
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
  getProgrammableDeployEvents,
  IEventsInstance,
} from '@/http/programmable';
import { useI18n } from 'vue-i18n';
import editorMonaco from '@/components/ag-editor.vue';
import { useTimeoutPoll } from '@vueuse/core';
import { Spinner } from 'bkui-vue/lib/icon';
import dayjs from 'dayjs';

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
  isParent: boolean;
  rawType?: string;
  nodeType?: string;
}

const props = defineProps({
  deployId: {
    type: Number,
  },
  currentStage: {
    type: Object,
    default: () => ({}),
  },
});

const emit = defineEmits([
  'release-success',
  'release-doing',
]);

const { t } = useI18n();

const route = useRoute();
const router = useRouter();

const isShow = ref(false);
const logDetails = ref<any>();
const eventTextLines = ref('');

const instances = ref<IEventsInstance[]>([]);

const isDeployFinished = ref(false);
const isDeployFailed = ref(false);
const deployedBy = ref('');

const apigwId = computed(() => +route.params?.id);

const timelineLists = computed(() => {
  const list: ITimelineItem[][] = [];
  instances.value.forEach((instance) => {
    const subList: ITimelineItem[] = [];
    let instanceDuration = 0;
    subList.push({
      // tag: instance.display_name,
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

const totalDuration = computed(() => {
  return timelineLists.value.reduce((duration, timelineList) => {
    timelineList.forEach((node) => {
      if (node.isParent) {
        duration += node.duration;
      }
    });
    return duration;
  }, 0);
});

const statusStyleMap: Record<string, any> = {
  successful: {
    color: 'green',
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
};

const getDotStyles = (status: string | null) => {
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

watch(
  () => isShow.value,
  (v) => {
    if (!v && logDetails.value?.status === 'successful') {
      emit('release-success');
    }
    if (!v && logDetails.value?.status !== 'successful') {
      emit('release-doing');
    }
    if (!v) {
      pausePoll();
    }
  },
);

watch(
  () => props.deployId,
  (id) => {
    if (id && isShow.value) {
      startPoll();
    }
  },
);

// 获取日志列表
const getEvents = async () => {
  const { paas_deploy_info: response } = await getProgrammableDeployEvents(apigwId.value, props.deployId);
  instances.value = response.events_instance || [];
  const events = response.events || [];
  const lines: string[] = [];

  events.forEach((event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.line) {
        lines.push(data.line);
      }
    } catch {
      lines.push(event.data);
    }
  });

  eventTextLines.value = lines.join('\n');

  if (instances.value.some(instance => instance.status === 'failed')) {
    instances.value = [];
    isDeployFinished.value = true;
    isDeployFailed.value = true;
    pausePoll();
    return;
  }
  const lastInstance = instances.value[instances.value.length - 1];
  if (lastInstance?.status === 'successful') {
    isDeployFinished.value = true;
    isDeployFailed.value = false;
    pausePoll();
  }
};

const { pause: pausePoll, resume: startPoll } = useTimeoutPoll(getEvents, 2000, {
  immediate: false,
});

const showSideslider = () => {
  isShow.value = true;
};

const handleRetry = () => {
  eventTextLines.value = '';
  isDeployFinished.value = false;
  isDeployFailed.value = false;
  startPoll();
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

    //:deep(.bk-timeline .bk-timeline-dot .bk-timeline-icon .bk-timeline-icon-inner>:first-child) {
    //  font-size: 20px !important;
    //}
    //
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
      //border-color: #d8d8d8;
      &:before {
        top: -10px;
      }

      //&.bk-timeline-large {
      //  margin-top: 11px;
      //
      //  &:before {
      //    top: -10px;
      //    left: -5px;
      //    width: 9px;
      //    height: 9px;
      //  }
      //}
      //
      //.bk-timeline-icon {
      //  top: -12px;
      //  left: -6px;
      //  width: 9px;
      //  height: 9px;
      //}
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
