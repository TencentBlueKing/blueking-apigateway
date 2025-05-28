<template>
  <bk-sideslider
    v-model:is-show="isShow"
    :show-mask="false"
    :title="title"
    quick-close
    v-bind="$attrs"
    width="400"
  >
    <template #default>
      <div
        ref="target"
        class="content-wrapper"
      >
        <div class="msg-list">
          <div class="msg-item in">
            {{ message }}
          </div>
          <div v-if="response && !loading" class="msg-item out">
            {{ response }}
          </div>
        </div>
        <BkLoading v-if="loading" style="width: 100%;justify-content: center;" />
      </div>
    </template>
  </bk-sideslider>
</template>

<script lang="ts" setup>
import {
  ref,
  useTemplateRef,
  watch,
} from 'vue';
import { getAICompletion } from '@/http';
import { useCommon } from '@/store';
import { onClickOutside } from '@vueuse/core';

interface IProps {
  title?: string;
  message?: string;
  messageType?: string;
}

const isShow = defineModel<boolean>({
  required: true,
  default: false,
});

const {
  title = 'AI',
  message = '',
  messageType = 'log_analysis',
} = defineProps<IProps>();

const commonStore = useCommon();

const response = ref('');
const loading = ref(false);
const target = useTemplateRef<HTMLElement>('target');

watch(() => message, () => {
  getResponse();
});

const getResponse = async () => {
  if (!message) {
    return;
  }
  try {
    loading.value = true;
    response.value = '';
    const res = await getAICompletion(commonStore.apigwId, {
      inputs: {
        input: message,
        type: messageType,
        enable_streaming: false,
      },
    });
    response.value = res.content || '';
  } finally {
    loading.value = false;
  }
};

onClickOutside(target, () => {
  isShow.value = false;
});

</script>

<style lang="scss" scoped>
:deep(.bk-sideslider-header) {

  // 隐藏关闭按钮
  .bk-sideslider-close {
    display: none;
  }

  .bk-sideslider-title {
    padding-left: 16px;
  }
}

.content-wrapper {
  padding: 16px;

  .msg-list {
    .msg-item {
      margin: 0 0 24px 0;
      padding: 10px 12px;
      font-size: 14px;
      line-height: 1.5;
      color: #313238;
      word-break: break-all;
      white-space: pre-wrap;
      border-radius: 4px;

      &.in {
        background: #e1ecff;
      }

      &.out {
        background: #fafbfd;
      }
    }
  }
}
</style>
