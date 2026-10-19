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
    :title="title"
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
        <BkButton
          text
          theme="primary"
          @click="handleLoadExample"
        >
          {{ t('填入示例') }}
        </BkButton>
      </div>

      <BkAlert
        class="request-params-json-slider__alert"
        theme="info"
        :title="description"
      />

      <div class="request-params-json-slider__overwrite-tip">
        {{ mode === 'openapi'
          ? t('将替换全部请求参数，片段中未定义的位置将被清空。')
          : t('仅替换 Body，保留已有 Header、Query、Path 参数。') }}
      </div>

      <BkAlert
        v-if="error || syntaxError"
        class="request-params-json-slider__alert"
        theme="error"
        :title="error || syntaxError"
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
            @change="handleEditorChange"
          />
        </main>
      </div>
    </div>

    <template #footer>
      <div class="request-params-json-slider__footer">
        <BkButton
          class="mr-8px"
          theme="primary"
          @click="handleEditorConfirm"
        >
          {{ mode === 'openapi' ? t('导入请求参数') : t('生成 Body') }}
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
import type { RequestParamsImportMode } from './types';

interface IProps {
  mode: RequestParamsImportMode
  error?: string
}

interface IEmits {
  'confirm': [json: unknown]
  'clear-error': []
}

const visible = defineModel<boolean>({ default: false });

const source = defineModel<string>('source', { default: '{}' });

const { mode, error = '' } = defineProps<IProps>();

const emit = defineEmits<IEmits>();

const { t } = useI18n();

const syntaxError = ref('');

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

const title = computed(() => mode === 'openapi' ? t('导入 OpenAPI 请求参数') : t('从 JSON 示例生成 Body'));

const description = computed(() => mode === 'openapi'
  ? t('仅支持单个 Operation 的 parameters 和 requestBody 请求定义；不支持完整 OpenAPI 文档、引用及非 JSON 请求体。')
  : t('整个 JSON 将作为 Body 示例推断字段类型，不推断必填、默认值或格式约束。'));

watch(visible, async (value) => {
  if (!value) {
    return;
  }

  syntaxError.value = '';
  await nextTick();
  editorRef.value?.setValue(source.value);
});

const handleImportJSON = async () => {
  try {
    await open();
  }
  catch (error) {
    if (!(error instanceof Error) || error.name !== 'AbortError') {
      syntaxError.value = t('读取文件失败，请重试或直接粘贴 JSON。');
    }
    return;
  }

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

/** 编辑后清除上一次确认的错误，协议解析成功后由父组件关闭侧栏。 */
const handleEditorChange = () => {
  syntaxError.value = '';
  emit('clear-error');
};

/** 仅负责 JSON 语法解析，输入类型由入口决定。 */
const handleEditorConfirm = () => {
  handleEditorChange();
  let json: unknown;
  try {
    const editorValue = editorRef.value?.getValue() ?? source.value;
    source.value = editorValue;
    json = JSON.parse(editorValue);
  }
  catch {
    syntaxError.value = t('请输入合法的 JSON');
    return;
  }
  emit('confirm', json);
};

/** 按入口提供可直接编辑的请求定义或真实请求体示例。 */
const handleLoadExample = () => {
  const example = mode === 'openapi'
    ? {
      parameters: [
        {
          in: 'header',
          name: 'X-Request-Id',
          schema: { type: 'string' },
        },
        {
          in: 'query',
          name: 'page',
          schema: {
            type: 'integer',
            minimum: 1,
          },
        },
        {
          in: 'path',
          name: 'id',
          required: true,
          schema: { type: 'string' },
        },
      ],
      requestBody: {
        required: true,
        content: {
          'application/json': {
            schema: {
              type: 'object',
              properties: {
                name: { type: 'string' },
                tags: {
                  type: 'array',
                  items: { type: 'string' },
                },
              },
              required: ['name'],
            },
          },
        },
      },
    }
    : {
      name: 'demo',
      enabled: true,
      tags: ['example'],
    };
  const text = JSON.stringify(example, null, 2);
  source.value = text;
  editorRef.value?.setValue(text);
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
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 16px;
  }

  &__alert {
    margin-bottom: 12px;
  }

  &__footer {
    padding-left: 40px;
  }

  &__overwrite-tip {
    margin-bottom: 8px;
    font-size: 12px;
    color: #63656E;
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
