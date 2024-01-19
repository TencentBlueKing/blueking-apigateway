<template>
  <bk-sideslider v-model:isShow="isShow" :width="1050" quick-close>
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
            {{ state.totalDuration }} s
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
              @select="handleTimelineChange"
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
  objectSteps: [],
  totalDuration: 0,
});
const logBody = ref<string>('');

let timeId: any = null;

// 改变当前选中值
const handleTimelineChange = (data: any) => {
  const { tag } = data;
  let detail = '';
  for (let i = 0; i < state.objectSteps?.length; i++) {
    const item = state.objectSteps[i];
    if (item?.tag === tag) {
      detail = item?.detail;
      break;
    }
  }
  logBody.value = detail || '';
};

// 获取日志列表
const getLogsList = async () => {
  try {
    const res = await getLogs(apigwId.value, props.historyId);
    if (res.status !== 'doing') {
      clearInterval(timeId);
    }
    logDetails.value = res;

    // 整理步骤
    const steps: any = [];
    state.totalDuration = 0;
    const subStep = res?.events[res?.events?.length - 1]?.step || 0;

    res?.events_template?.forEach((item: any, index: number) => {
      item.size = 'large';

      if (item?.step < subStep) {
        item.color = 'green';
        item.filled = true;
      } else if (item?.step === subStep) {
        if (res?.status === 'success') {
          item.color = 'green';
          item.filled = true;
        } else if (res?.status === 'doing') {
          item.color = 'blue';
          item.icon = Spinner;
        } else {
          item.color = 'red';
        }
      }

      steps[index] = { ...item, tag: item.description };

      const children: any = [];
      res?.events?.forEach((subItem: any) => {
        if (item?.step === subItem?.step) {
          children.push(subItem);
        }
      });
      const firstChild = children[0];
      const lastChild = children[children.length - 1];

      const date1 = dayjs(firstChild?.created_time);
      const date2 = dayjs(lastChild?.created_time);

      const duration = date2.diff(date1, 's', true);
      state.totalDuration += duration;

      const itemLogs: string[] = [];
      children?.forEach((c: any) => {
        itemLogs?.push(`${c.created_time}  ${c.name}  ${c.status}`);
        if (c.detail?.err_msg && c.status === 'failure') {
          itemLogs?.push(`  err_msg: ${c.detail?.err_msg}`);
        }
      });

      steps[index].children = children;
      steps[index].content = `<span style="font-size: 12px;">${duration} s</span>`;
      steps[index].detail = itemLogs.join('\n');
    });
    state.objectSteps = steps;
    logBody.value = steps[subStep]?.detail || '';
  } catch (e) {
    clearInterval(timeId);
    console.log(e);
  }
};

const showSideslider = () => {
  isShow.value = true;
};

const emit = defineEmits<(e: 'release-success') => void>();

watch(
  () => isShow.value,
  (v) => {
    if (!v && logDetails.value?.status === 'success') {
      emit('release-success');
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
      }
    }
  }
  .main-encoding {
    flex: 1;
    height: 100%;
  }
}
</style>
