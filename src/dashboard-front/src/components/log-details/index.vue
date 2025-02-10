<template>
  <bk-sideslider v-model:isShow="isShow" :width="960" quick-close>
    <template #header>
      <div class="log-details-title">
        <div class="log-details-name">【{{ logDetails?.stage?.name }}】{{ t('发布日志详情') }}</div>
        <bk-tag theme="success" v-if="logDetails?.status === 'success'">
          {{ t('发布成功') }}
        </bk-tag>
        <bk-tag theme="info" v-else-if="logDetails?.status === 'doing'">
          {{ t('进行中') }}
        </bk-tag>
        <bk-tag theme="danger" v-else-if="logDetails?.status === 'failure'">
          {{ t('发布失败') }}
        </bk-tag>
        <div class="title-publish-info">{{ t('发布版本') }}: <span>{{ logDetails?.resource_version_display }}</span></div>
        <div class="title-publish-info">
          {{ t('耗时') }}:
          <span>
            {{ state.totalDuration.toFixed(2) }} s
          </span>
        </div>
      </div>
    </template>
    <template #default>
      <div class="log-details-main">
        <div class="main-process">
          <div>
            <bk-timeline
              class="mb20"
              :list="state.objectSteps"
            />
          </div>
        </div>
        <div class="main-encoding">
          <editor-monaco v-model="logBody" :read-only="true" ref="logCodeViewer" />
        </div>
      </div>
    </template>
  </bk-sideslider>
</template>

<script lang="ts" setup>
import { ref, reactive, watch, computed } from 'vue';
import { useRoute } from 'vue-router';
import dayjs from 'dayjs';
import { getLogs } from '@/http';
import { useI18n } from 'vue-i18n';
import editorMonaco from '@/components/ag-editor.vue';
import { Spinner } from 'bkui-vue/lib/icon';

const props = defineProps({
  historyId: {
    type: Number,
  },
});

const { t } = useI18n();

const route = useRoute();
const apigwId = computed(() => +route.params?.id);

const isShow = ref(false);
const logCodeViewer: any = ref<InstanceType<typeof editorMonaco>>();

const logDetails = ref<any>();
const state = reactive({
  objectSteps: [] as IStep[],
  totalDuration: 0,
});
const logBody = ref('');

let timeId: any = null;

// 改变当前选中值
// const handleTimelineChange = (data: any) => {
//   const { tag } = data;
//   let detail = '';
//   for (let i = 0; i < state.objectSteps?.length; i++) {
//     const item = state.objectSteps[i];
//     if (item?.tag === tag) {
//       detail = item?.detail;
//       break;
//     }
//   }
//   logBody.value = detail || '';
// };

interface IStep {
  name?: string;
  description?: string;
  step?: number;
  size?: string;
  color?: string;
  filled?: boolean;
  tag?: string;
  content?: string;
  icon?: typeof Spinner;
  status?: 'doing' | 'success' | 'failure';
  duration?: number;
}

// 获取日志列表
const getLogsList = async () => {
  try {
    const response = await getLogs(apigwId.value, props.historyId);
    if (response.status !== 'doing') {
      clearInterval(timeId);
    }
    logDetails.value = response;

    // 整理步骤
    state.objectSteps = [];
    state.totalDuration = 0;
    logBody.value = '';

    const events = response.events || [];
    const eventTemplates = response.events_template || [];

    // 生成步骤节点
    state.objectSteps = eventTemplates.map((eventTemplate) => {
      const step: IStep = {
        size: 'large',
        tag: eventTemplate.description,
      };
      const currentEvents = events.filter(event => event.step === eventTemplate.step);

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
        if (logDetails.value?.status === 'doing') {
          // 给已结束步骤的下一个在 doing 状态的步骤显示加载图标
          const prevEvents = events.filter(event => event.step === eventTemplate.step - 1);
          if (prevEvents.find(event => event.status === 'success' || event.status === 'failure')) {
            step.color = 'blue';
            step.icon = Spinner;
          }
        }
      }

      // 计算每个步骤使用的时间
      const startTime = dayjs(currentEvents.find(event => event.status === 'doing')?.created_time);
      let duration = 0;
      const nextEvents = events.filter(event => event.step === eventTemplate.step + 1);

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
      step.content = `<span style="font-size: 12px;">${fixedDuration} s</span>`;
      step.duration = fixedDuration;
      // 计算总耗时
      state.totalDuration += fixedDuration;

      // 步骤日志
      const stepLogs = currentEvents.map(event => (event.status === 'failure'
        ? `  err_msg: ${event.detail?.err_msg ?? 'unknown error'}`
        : `${event.created_time}  ${event.name}  ${event.status}`));

      logBody.value += `${stepLogs.join('\n')}\n\n`;
      return step;
    });
  } catch (e) {
    clearInterval(timeId);
  }
};

const showSideslider = () => {
  isShow.value = true;
};

const emit = defineEmits(['release-success', 'release-doing']);

watch(
  () => isShow.value,
  (v) => {
    if (!v && logDetails.value?.status === 'success') {
      emit('release-success');
    }
    if (!v && logDetails.value?.status !== 'success') {
      emit('release-doing');
    }
    if (!v) {
      clearInterval(timeId);
    }
  },
);

watch(
  () => props.historyId,
  (id) => {
    if (id && isShow.value) {
      getLogsList();
      timeId = setInterval(() => {
        getLogsList();
      }, 1000 * 2);
    }
  },
);

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
    color: #63656E;
    margin-left: 32px;
    span {
      color: #2c2e35;
    }
  }
}

.log-details-main {
  display: flex;
  align-items: center;
  padding: 16px 16px 0px;
  height: calc(100vh - 52px);
  box-sizing: border-box;
  .main-process {
    width: 270px;
    height: 100%;
    background-color: #f5f7fa;
    overflow-y: auto;
    padding: 16px;
    box-sizing: border-box;
    margin-right: 16px;
    :deep(.bk-timeline .bk-timeline-dot .bk-timeline-icon .bk-timeline-icon-inner>:first-child) {
      font-size: 20px !important;
    }
    :deep(.bk-timeline .bk-timeline-dot .bk-timeline-section) {
      display: flex;
      justify-content: space-between;
      align-items: center;
      .bk-timeline-title {
        padding-bottom: 0px;
        margin-top: 0;
      }
    }
    :deep(.bk-timeline .bk-timeline-dot) {
      border-left: 1px dashed #d8d8d8;
      &.bk-timeline-large {
        margin-top: 11px;
        &:before {
          top: -10px;
          left: -5px;
          width: 9px;
          height: 9px;
        }
      }
      .bk-timeline-icon {
        top: -12px;
        left: -6px;
        width: 9px;
        height: 9px;
      }
    }
  }
  .main-encoding {
    flex: 1;
    height: 100%;
  }
}
</style>
