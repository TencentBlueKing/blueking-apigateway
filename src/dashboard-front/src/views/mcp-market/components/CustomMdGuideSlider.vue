<template>
  <AgSideSlider
    v-model="isShow"
    v-bind="$attrs"
    :width="960"
    :title="$t('自定义使用指引')"
    :init-data="defaultFormData"
    @compare="handleCompare"
    @closed="handleCancel"
  >
    <template #default>
      <BkForm
        ref="formRef"
        :model="formData"
        :rules="rules"
      >
        <BkFormItem
          property="content"
          :label-width="0"
          class="mb-0! h-full markdown-guide-editor"
          required
        >
          <mavon-editor
            ref="markdownRef"
            v-model="formData.content"
            :default-open="'preview'"
            toolbars-flag
            scroll-style
            :box-shadow="false"
            :tab-size="4"
            :font-size="'14'"
            :language="language"
            :subfield="isSubfield"
            :toolbars="customToolbars"
            @full-screen="handleFullscreen"
          />
        </BkFormItem>
      </BkForm>
    </template>
    <template #footer>
      <div class="flex p-l-40px">
        <BkButton
          theme="primary"
          class="min-w-88px"
          :loading="submitLoading"
          @click="handleConfirm"
        >
          {{ t('确认') }}
        </BkButton>
        <BkButton
          class="min-w-88px m-l-8px"
          @click="handleCancel"
        >
          {{ t('取消') }}
        </BkButton>
      </div>
    </template>
  </AgSideSlider>
</template>

<script setup lang="ts">
import { cloneDeep } from 'lodash-es';
import { Form, Message } from 'bkui-vue';
import { type MavonEditorProps, mavonEditor } from 'mavon-editor';
import type { IFormMethod } from '@/types/common';
import { addCustomServerGuideDoc, updateCustomServerGuideDoc } from '@/services/source/mcp-server';
import AgSideSlider from '@/components/ag-sideslider/Index.vue';

const isShow = defineModel('isShow', {
  type: Boolean,
  default: false,
});

const formData = defineModel('formData', {
  type: Object,
  default: { content: '' },
});

const {
  gatewayId = 0,
  guideType = '',
  markdownText = '',
} = defineProps<IProps>();

const emit = defineEmits<{ confirm: [content: string] }>();

enum GuideType {
  ADD = 'add',
  CUSTOM = 'CUSTOM',
}

interface IProps {
  gatewayId?: number
  guideType?: string
  markdownText?: string
}

const route = useRoute();
const { t } = useI18n();

const formRef = ref<InstanceType<typeof Form> & IFormMethod>();
const markdownRef = ref<InstanceType<typeof mavonEditor> | null>(null);
const submitLoading = ref(false);
const isSubfield = ref(true);
const isFullscreen = ref(false);
const language = ref<'zh' | 'en'>('zh');
const defaultFormData = ref({ content: '' });
const rules = reactive({
  content: [
    {
      required: true,
      message: t('请填写自定义使用指引'),
      trigger: 'change',
    },
  ],
});

// 自定义工具栏配置
const customToolbars: MavonEditorProps['toolbars'] = ({
  bold: true,
  italic: true,
  header: true,
  underline: true,
  strikethrough: true,
  mark: true,
  quote: true,
  ol: true,
  ul: true,
  link: true,
  image: true,
  table: true,
  fullscreen: true,
  subfield: true,
  preview: true,
  code: true,
  undo: true,
  redo: true,
});

const serverId = computed(() => route.params.serverId);

const setFormData = ({ content }: { content: string }) => {
  [defaultFormData.value, formData.value] = [cloneDeep({ content }), cloneDeep({ content })];
};

watch(() => markdownText, (newVal: string) => {
  setFormData({ content: newVal });
}, { immediate: true });

const handleCompare = (callback) => {
  callback(cloneDeep(formData.value));
};

const handleFullscreen = (isFull: boolean) => {
  isFullscreen.value = isFull;
};

const handleConfirm = async () => {
  try {
    await formRef.value?.validate();
    const isAdd = GuideType.ADD === guideType;
    if (isAdd) {
      await addCustomServerGuideDoc(gatewayId, serverId.value, formData.value);
    }
    else {
      await updateCustomServerGuideDoc(gatewayId, serverId.value, formData.value);
    }
    Message({
      message: t(isAdd ? '新增成功' : '编辑成功'),
      theme: 'success',
    });
    handleCancel();
    emit('confirm');
  }
  finally {
    submitLoading.value = false;
  }
};

const handleCancel = () => {
  nextTick(() => {
    if (isFullscreen.value) {
      markdownRef.value?.$el.querySelector('.fa-mavon-compress')?.click();
    }
    setFormData(defaultFormData.value);
    formRef.value?.clearValidate();
    isFullscreen.value = false;
    isShow.value = false;
  });
};
</script>

<style lang="scss" scoped>
.markdown-guide-editor {
  margin-left: 40px;
  margin-right: 24px;
  border: 1px solid #e5e5e5;
  border-radius: 2px;
  height: calc(100vh - 124px);

  :deep(.bk-form-content) {
    height: 100%;
  }

  :deep(.markdown-body) {
    height: 100%;

    .v-note-op {
      border-bottom: 1px solid #dcdee5;

      .op-icon {
        &.selected {
          background-color: #e1ecff;
          color: #3a84ff;
        }

         &.fa-mavon-compress {
            margin: 0 8px;
          }
      }
    }

    .v-note-panel {
      .divarea-wrapper .content-input-wrapper,
      .auto-textarea-wrapper .auto-textarea-input {
        background-color: transparent !important;
        color: #4d4f56 !important;
        font-size: 14px;
      }

      .v-show-content {
        background-color: #fafbfd !important;
        box-shadow: -1px 0 0 0 #dcdee5;
      }
    }
  }

  &.is-error {
    :deep(.markdown-body) {
      height: calc(100% - 22px);
    }
  }
}
</style>
