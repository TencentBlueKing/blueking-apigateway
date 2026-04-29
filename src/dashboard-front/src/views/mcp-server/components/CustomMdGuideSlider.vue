/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2026 Tencent. All rights reserved.
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
import type { IFormMethod, IMavonEditorProps } from '@/types/common';
import { addCustomServerGuideDoc, updateCustomServerGuideDoc } from '@/services/source/mcp-server';
import AgSideSlider from '@/components/ag-sideslider/Index.vue';

interface IProps {
  gatewayId?: number
  guideType?: string
  markdownText?: string
}

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

const route = useRoute();
const { t } = useI18n();

const formRef = ref<InstanceType<typeof Form> & IFormMethod>();
const markdownRef = ref<any>(null);
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
const customToolbars: IMavonEditorProps['toolbars'] = {
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
};

const serverId = computed(() => Number(route.params.serverId));

const setFormData = ({ content }: { content: string }) => {
  [defaultFormData.value, formData.value] = [cloneDeep({ content }), cloneDeep({ content })];
};

watch(() => markdownText, (newVal: string) => {
  setFormData({ content: newVal });
}, { immediate: true });

const handleCompare = (callback: any) => {
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
    emit('confirm', formData.value.content ?? '');
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
  height: calc(100vh - 124px);
  margin-right: 24px;
  margin-left: 40px;
  border: 1px solid #e5e5e5;
  border-radius: 2px;

  :deep(.bk-form-content) {
    height: 100%;
  }

  :deep(.markdown-body) {
    height: 100%;

    .v-note-op {
      border-bottom: 1px solid #dcdee5;

      .op-icon {

        &.selected {
          color: #3a84ff;
          background-color: #e1ecff;
        }

         &.fa-mavon-compress {
            margin: 0 8px;
          }
      }
    }

    .v-note-panel {

      .divarea-wrapper .content-input-wrapper,
      .auto-textarea-wrapper .auto-textarea-input {
        font-size: 14px;
        color: #4d4f56 !important;
        background-color: transparent !important;
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
