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
        <div class="title-publish-info">{{ t('耗时') }}: <span>{{ logDetails?.duration }} s</span></div>
      </div>
    </template>
    <template #default>
      <div class="log-details-main">
        <div class="main-process">
          <div>
            <bk-steps
              direction="vertical"
              size="small"
              theme="success"
              ext-cls="logs-steps"
              :controllable="state.controllable"
              :cur-step="state.curStep"
              :steps="state.objectSteps"
              class="mb20"
              @click="stepChanged"
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
import { ref, reactive, watch } from 'vue';
import { useRoute } from 'vue-router';
import dayjs from 'dayjs';
import { getLogs } from '@/http';
import { useI18n } from 'vue-i18n';
import editorMonaco from '@/components/ag-editor.vue';

const props = defineProps({
  historyId: {
    type: Number,
  },
});

const { t } = useI18n();

const route = useRoute();
const apigwId = +route.params?.id;

const isShow = ref(false);
const logCodeViewer: any = ref<InstanceType<typeof editorMonaco>>();

const logDetails = ref<any>();
const state = reactive({
  objectSteps: [],
  curStep: 1,
  controllable: true,
});
const logBody = ref<string>('');

let timeId: any = null;

// 改变当前选中值
const stepChanged = (index: number) => {
  // state.curStep = index;
  logBody.value = state.objectSteps[index - 1]?.detail?.start_time || '';
};

// 获取日志列表
const getLogsList = async () => {
  try {
    const res = await getLogs(apigwId, props.historyId);
    if (res.status !== 'doing') {
      clearInterval(timeId);
    }
    logDetails.value = res;

    // 计算每个小节点的耗时
    res?.events?.forEach((item: any, index: number) => {
      if (res?.events[index + 1]?.created_time) {
        const date1 = dayjs(res?.events[index + 1]?.created_time);
        const date2 = dayjs(item?.created_time);
        item.description = `${dayjs(date1.diff(date2)).format('sS')}`;
      }

      if (index === res?.events?.length - 1) {
        item.curStep = true;
      }
    });

    // 整理步骤
    const steps: any = [];
    res?.events_template?.forEach((item: any, index: number) => {
      item.status = item.status === 'doing' ? 'loading' : item.status === 'failure' ? 'error' : item.status;
      steps[index] = [{ ...item, title: item.description, description: '', isFirst: true }];

      res?.events?.forEach((subItem: any) => {
        if (item?.step === subItem?.step) {
          subItem.status = subItem.status === 'doing' ? 'loading' : subItem.status === 'failure' ? 'error' : subItem.status;
          steps[index]?.push({ ...subItem, title: subItem.name });
        }
      });
    });

    state.objectSteps = steps?.flat();
    // 是否为正在进行的节点
    state.objectSteps?.forEach((item: any, index: number) => {
      if (item?.curStep) {
        state.curStep = index + 1;
        if (res?.status === 'success') {
          state.curStep = index + 2;
        }
      }
    });
    logBody.value = state.objectSteps[state.curStep - 1]?.detail?.start_time || '';
  } catch (e) {
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
  },
);

watch(
  () => props.historyId,
  (v) => {
    if (v) {
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
  }
  .main-encoding {
    flex: 1;
    height: 100%;
  }
}
</style>

<style lang="scss">
.logs-steps.bk-steps {
  .bk-step {
    display: flex;
    margin-bottom: 0;
    padding-bottom: 18px;
    .bk-step-content {
      display: flex;
      flex: 1;
      align-items: center;
      justify-content: space-between;
    }
    &:last-child:after {
      height: 0;
    }
    .bk-step-indicator {
      >span {
        display: none;
      }
    }
  }
  .bk-step:after {
    z-index: 999;
    top: 22px;
    height: 18px;
  }
}
</style>
