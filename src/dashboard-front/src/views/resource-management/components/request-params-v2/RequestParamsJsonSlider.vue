<!--
  TencentBlueKing is pleased to support the open source community by making
  蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
  Copyright (C) Tencent. All rights reserved.
  Licensed under the MIT License (the "License"); you may not use this file except
  in compliance with the License. You may obtain a copy of the License at

  http://opensource.org/licenses/MIT

  Unless required by applicable law or agreed to in writing, software distributed under
  the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
  either express or implied. See the License for the specific language governing permissions and
  limitations under the License.

  We undertake not to change the open source license (MIT license) applicable
  to the current version of the project delivered to anyone in the future.
-->

<template>
  <AgSideSlider
    v-model="visible"
    :scrollbar="false"
    :title="t('通过 JSON 生成')"
    render-directive="if"
  >
    <div class="request-params-json-slider">
      <div class="request-params-json-slider__actions">
        <IconButton
          icon="upload"
          theme="primary"
          @click="handleImportJSON"
        >
          {{ t('导入 JSON') }}
        </IconButton>
      </div>

      <BkAlert
        class="request-params-json-slider__alert"
        theme="info"
        :title="t('支持 OpenAPI Operation，或按 header、query、path、body 分组的请求 JSON；普通 JSON 将作为 Body 生成。')"
      />

      <div class="editor-layout">
        <header class="editor-toolbar">
          <span>{{ t('编辑 JSON') }}</span>
          <BkButton
            v-bk-tooltips="{ content: t('格式化') }"
            text
            @click="handleFormat"
          >
            <AgIcon
              name="geshihua"
              size="16"
            />
          </BkButton>
        </header>
        <main class="editor-main-content">
          <EditorMonaco
            ref="editorRef"
            :minimap="false"
            :model-value="source"
            language="json"
          />
        </main>
      </div>
    </div>

    <template #footer>
      <div class="request-params-json-slider__footer">
        <BkButton
          class="w-88px mr-8px"
          theme="primary"
          @click="handleEditorConfirm"
        >
          {{ t('确定') }}
        </BkButton>
        <BkButton
          class="w-88px"
          @click="visible = false"
        >
          {{ t('取消') }}
        </BkButton>
      </div>
    </template>
  </AgSideSlider>
</template>

<script lang="ts" setup>
import AgSideSlider from '@/components/ag-sideslider/Index.vue';
import EditorMonaco from '@/components/ag-editor/Index.vue';
import { useFileSystemAccess } from '@vueuse/core';
import { Message } from 'bkui-vue';

interface IEmits {
  confirm: [json: unknown]
}

const visible = defineModel<boolean>({ default: false });

const source = defineModel<string>('source', { default: '{}' });

const emit = defineEmits<IEmits>();

const { t } = useI18n();

const editorRef = useTemplateRef<InstanceType<typeof EditorMonaco>>('editorRef');

const {
  data: importedJsonText,
  fileSize,
  open,
} = useFileSystemAccess({
  dataType: 'Text',
  types: [{
    accept: {
      'application/json': ['.json'],
      'text/plain': ['.txt'],
    },
    description: 'JSON',
  }],
});

watch(visible, async (value) => {
  if (!value) {
    return;
  }

  await nextTick();
  editorRef.value?.setValue(source.value);
});

const handleImportJSON = async () => {
  await open();

  if (fileSize.value > 10 * 1024) {
    Message({
      message: t('文件大小超过 10KB'),
      theme: 'warning',
    });
    return;
  }

  if (typeof importedJsonText.value !== 'string' || !importedJsonText.value) {
    Message({
      message: t('请选择合法的 JSON'),
      theme: 'warning',
    });
    return;
  }

  source.value = importedJsonText.value;
  editorRef.value?.setValue(importedJsonText.value);
};

const handleEditorConfirm = () => {
  try {
    source.value = editorRef.value?.getValue() ?? source.value;
    emit('confirm', JSON.parse(source.value));
    visible.value = false;
  }
  catch {
    Message({
      message: t('请输入合法的 JSON'),
      theme: 'warning',
    });
  }
};

const handleFormat = () => {
  editorRef.value?.handleFormat();
};
</script>

<style lang="scss" scoped>
.request-params-json-slider {
  padding: 32px 40px 0;
  font-size: 12px;

  &__actions {
    margin-bottom: 16px;
  }

  &__alert {
    margin-bottom: 12px;
  }

  &__footer {
    padding-left: 40px;
  }
}

.editor-layout {
  display: flex;
  height: 520px;
  overflow: hidden;
  background: #1E1E1E;
  border-radius: 3px;
  flex-direction: column;

  .editor-toolbar {
    position: relative;
    z-index: 6;
    display: flex;
    flex: 0 0 40px;
    align-items: center;
    justify-content: space-between;
    height: 40px;
    padding: 0 12px 0 20px;
    font-size: 14px;
    color: #CCC;
    background: #2E2E2E;
    box-shadow: 0 2px 4px rgb(0 0 0 / 20%);

    :deep(.bk-button) {
      color: #999;

      &:hover {
        color: #CCC;
      }
    }
  }

  .editor-main-content {
    min-height: 0;
    flex: 1;
  }
}
</style>
