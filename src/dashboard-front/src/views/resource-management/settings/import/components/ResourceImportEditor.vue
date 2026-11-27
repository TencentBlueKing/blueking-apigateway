/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) Tencent. All rights reserved.
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
  <div
    class="import-container"
  >
    <div class="import-header flex">
      <div class="flex items-center">
        <BkUpload
          theme="button"
          :custom-request="handleFileUpload"
          class="upload-cls"
          accept=".yaml,.json,.yml"
          :size="uploadMaxSize"
          @error="handleUploadError"
        >
          <div>
            <AgIcon
              class="icon"
              name="upload"
            />
            {{ t('上传文件') }}
          </div>
        </BkUpload>
        <span class="desc">{{ t('支持 Swagger 2.0 和 OpenAPI 3.0 规范的文件，文件格式支持 JSON、YAML') }}</span>
        <span class="desc">
          <BkLink
            theme="primary"
            :href="envStore.env.DOC_LINKS.SWAGGER"
            target="_blank"
            class="text-12px"
          >
            <span class="flex items-center">
              <Share
                width="12px"
                height="12px"
                fill="#3A84FF"
                class="mr-4px"
              />{{ t('使用指引') }}
            </span>
          </BkLink>
        </span>
      </div>
      <div class="flex items-center">
        <BkForm class="flex">
          <BkFormItem
            class="mb-0!"
            :label-width="20"
          >
            <BkCheckbox
              v-model="docConfig.showDoc"
              size="small"
            >
              {{ t('生成资源文档') }}
            </BkCheckbox>
          </BkFormItem>
          <BkFormItem
            v-if="docConfig.showDoc"
            class="mb-0!"
            :label="t('文档语言')"
            required
            :label-width="120"
          >
            <BkRadioGroup
              v-model="docConfig.language"
              size="small"
            >
              <BkRadio label="zh">
                {{ t('中文文档') }}
              </BkRadio>
              <BkRadio label="en">
                {{ t('英文文档') }}
              </BkRadio>
            </BkRadioGroup>
          </BkFormItem>
        </BkForm>
      </div>
      <div class="flex items-center ml-auto">
        <BkButton
          theme="primary"
          text
          class="text-12px!"
          @click="handleShowExample"
        >
          {{ t('模板示例') }}
        </BkButton>
      </div>
    </div>
    <!-- 代码编辑器 -->
    <div
      ref="editorWrapRef"
      class="import-editor"
      :class="{ 'hide-collapse-btn': visibleErrorReasons.length < 1 }"
    >
      <BkResizeLayout
        ref="resizeLayoutRef"
        placement="bottom"
        collapsible
        :border="false"
        :max="resizeLayoutAsideMax"
        :min="resizeLayoutAsideMin"
        class="h-full!"
        :is-collapsed="isErrorConsoleCollapsed"
        @collapse-change="updateIsEditorMsgCollapsed"
      >
        <template #main>
          <div class="editor-layout-main">
            <!--  顶部编辑器工具栏 -->
            <header class="editor-toolbar">
              <span
                class="p-10px pl-25px color-#ccc"
              >{{ t('代码编辑器') }}</span>
              <aside class="tool-items">
                <section
                  class="tool-item"
                  :class="{ 'active': isFindPanelVisible }"
                  @click="toggleFindToolClick"
                >
                  <AgIcon
                    name="search"
                    size="16"
                  />
                </section>
                <section
                  class="tool-item"
                  @click="handleFontSizeClick"
                >
                  <AgIcon
                    name="font"
                    size="16"
                  />
                </section>
                <section
                  class="tool-item"
                  @click="handleFullScreenClick"
                >
                  <AgIcon
                    name="gongneng-quanping2"
                    size="16"
                  />
                </section>
              </aside>
            </header>
            <main
              class="editor-main-content"
              :class="{ 'show-valid-msg': isCodeValid }"
            >
              <!--  编辑器本体  -->
              <AgCodeEditor
                ref="resourceEditorRef"
                v-model="editorText"
                @find-state-changed="isFindPanelVisible = $event"
              />
              <!--  右侧的代码 error, warning 计数器  -->
              <aside class="editor-side-bar">
                <main class="editor-error-counters">
                  <div
                    v-bk-tooltips="{ content: `Error: ${msgAsErrorNum}`, placement: 'left' }"
                    class="error-count-item"
                    :class="{ 'active': activeCodeMsgType === 'Error' }"
                    @click="() => handleErrorCountClick('Error')"
                  >
                    <AgIcon
                      name="exclamation-circle-fill"
                      size="12"
                      class="icon mb-0! color-#EA3636"
                    />
                    <span class="num color-#EA3636">{{ msgAsErrorNum }}</span>
                  </div>
                </main>
                <footer class="editor-error-shifts">
                  <div
                    class="shift-btn prev"
                    @click="() => setEditorCursor('top')"
                  >
                    <CollapseLeft
                      width="18px"
                      height="18px"
                      fill="#C4C6CC"
                    />
                  </div>
                  <div
                    class="shift-btn next"
                    @click="() => setEditorCursor('bottom')"
                  >
                    <CollapseLeft
                      width="18px"
                      height="18px"
                      fill="#C4C6CC"
                    />
                  </div>
                </footer>
              </aside>
            </main>
            <!--  底部“语法校验”按钮栏  -->
            <footer class="editor-footer-bar">
              <article
                v-if="isCodeValid"
                class="validation-message"
              >
                <Success
                  class="color-#34b97b"
                  width="14px"
                  height="14px"
                />
                <span class="msg-part msg-body">{{ t('校验通过') }}</span>
              </article>
              <article
                v-else
                class="editor-footer-validate-btn"
              >
                <BkButton
                  theme="primary"
                  size="small"
                  :loading="isDataLoading"
                  :disabled="isDataLoading"
                  @click="emit('validate')"
                >
                  <PlayShape />
                  {{ t('语法校验') }}
                </BkButton>
              </article>
            </footer>
          </div>
        </template>
        <!--  底部错误信息展示  -->
        <template #aside>
          <div
            class="editor-messages-wrapper"
            :class="{ 'has-error-msg': visibleErrorReasons.length > 0 }"
          >
            <article
              v-for="(reason, index) in visibleErrorReasons"
              :key="index"
              class="editor-message"
              :class="{ 'active': activeVisibleErrorMsgIndex === index }"
              @click="() => handleErrorMsgClick(reason, index)"
            >
              <span class="msg-part msg-icon">
                <AgIcon
                  name="exclamation-circle-fill"
                  size="12"
                  class="color-#B34747"
                />
              </span>
              <span class="msg-part msg-host" />
              <span class="msg-part msg-body">{{ reason.message }}</span>
              <span class="msg-part msg-error-code">{{ reason.json_path }}</span>
              <span
                v-if="reason.range"
                class="msg-part msgPos"
              >
                {{ `(${reason.range.startLineNumber}, ${reason.range.startColumn})` }}
              </span>
            </article>
          </div>
        </template>
      </BkResizeLayout>
    </div>
    <TmplExampleSideslider
      :is-show="isShowExample"
      @on-hidden="handleHiddenExample"
    />
  </div>
</template>

<script setup lang="ts">
import { Message, type ResizeLayout } from 'bkui-vue';
import type { editor } from 'monaco-editor';
import { CollapseLeft, PlayShape, Share, Success } from 'bkui-vue/lib/icon';
import AgCodeEditor from '@/components/base/ag-code-editor/Index.vue';
import { useEnv } from '@/stores';
import type { CodeErrorMsgType, ErrorReasonType } from '@/types/common';
import { getStrFromFile, messageError } from '@/utils';
import TmplExampleSideslider from '../../components/TmplExampleSideslider.vue';
import { createImportErrorLocator } from '../error-location';
import type { IImportCheckError, IImportDocConfig, IImportValidationFailure } from '../types';

interface IProps {
  isCodeValid: boolean
  isDataLoading: boolean
  validationFailure?: IImportValidationFailure
}

const editorText = defineModel<string>({ required: true });
const docConfig = defineModel<IImportDocConfig>('docConfig', { required: true });
const {
  isCodeValid,
  isDataLoading,
  validationFailure = undefined,
} = defineProps<IProps>();

const emit = defineEmits<{ validate: [] }>();

const { t } = useI18n();
const envStore = useEnv();

const resourceEditorRef = useTemplateRef<InstanceType<typeof AgCodeEditor>>('resourceEditorRef');
const resizeLayoutRef = useTemplateRef<InstanceType<typeof ResizeLayout>>('resizeLayoutRef');
const editorWrapRef = useTemplateRef<HTMLElement>('editorWrapRef');
const activeCodeMsgType = ref<CodeErrorMsgType>('All');
const errorReasons = ref<ErrorReasonType[]>([]);
const activeVisibleErrorMsgIndex = ref(-1);
const isFindPanelVisible = ref(false);
const isShowExample = ref(false);
const isErrorConsoleCollapsed = ref(true);
const resizeLayoutAsideMax = ref(100);
const resizeLayoutAsideMin = ref(50);
const uploadMaxSize = 10;

const visibleErrorReasons = computed(() => {
  const level = activeCodeMsgType.value;
  return level === 'All' ? errorReasons.value : errorReasons.value.filter(reason => reason.level === level);
});

const msgAsErrorNum = computed(() => errorReasons.value.filter(reason => reason.level === 'Error').length);

watch(editorText, () => {
  // 文本变化时父组件会使校验结果失效，错误和标记由校验结果的监听统一清理。
  isErrorConsoleCollapsed.value = true;
});

watch(() => isDataLoading, (loading) => {
  if (loading) {
    activeCodeMsgType.value = 'All';
  }
});

watch(() => isCodeValid, (valid) => {
  if (valid) {
    isErrorConsoleCollapsed.value = true;
  }
});

watch(() => validationFailure, (failure) => {
  activeVisibleErrorMsgIndex.value = -1;
  if (!failure || failure.content !== editorText.value) {
    clearEditorErrors();
    return;
  }

  errorReasons.value = getValidationErrors(failure.error, failure.content, resourceEditorRef.value?.getModel());
  updateEditorDecorations();
  updateEditorMarkers();
  isErrorConsoleCollapsed.value = errorReasons.value.length === 0;
});

const handleFileUpload = async ({ file }: { file: File }) => {
  if (!/\.(json|yaml|yml)/.test(file.name)) {
    Message({
      theme: 'error',
      message: t('仅支持 json, yaml 格式'),
    });
    return;
  }
  editorText.value = await getStrFromFile(file) as string;
  await nextTick();
  resourceEditorRef.value?.setValue(editorText.value);
  await nextTick();
  emit('validate');
};

const handleUploadError = (_1: any, _2: any, error: { message: string }) => {
  if (error.message === 'invalid file size') {
    messageError(t('文件大小超过{size}MB', { size: uploadMaxSize }));
  }
};

const clearEditorErrors = () => {
  errorReasons.value = [];
  resourceEditorRef.value?.setLineDecorations([]);
  resourceEditorRef.value?.setMarkers([]);
};

const getValidationErrors = (
  error: IImportCheckError | undefined,
  content: string,
  model: editor.ITextModel | null | undefined,
): ErrorReasonType[] => {
  if (error?.code !== 'INVALID' || error.message !== 'validate fail') {
    return [{
      message: error?.message ?? t('未知错误'),
      level: 'Error',
    }];
  }

  const locateError = model?.getValue() === content ? createImportErrorLocator(content) : undefined;
  return (error.data ?? []).map(({ json_path, message }) => {
    const reason: ErrorReasonType = {
      json_path,
      message: message ?? t('未知错误'),
      level: 'Error',
    };
    const offsets = locateError?.(json_path);
    if (model && offsets) {
      const start = model.getPositionAt(offsets[0]);
      const end = model.getPositionAt(offsets[1]);
      reason.range = {
        startLineNumber: start.lineNumber,
        startColumn: start.column,
        endLineNumber: end.lineNumber,
        endColumn: end.column,
      };
    }
    return reason;
  });
};

const getSourceSnapshot = () => {
  const content = editorText.value;
  const model = resourceEditorRef.value?.getModel();
  const version = model?.getVersionId();

  return {
    content,
    isCurrent: () => editorText.value === content
      && model === resourceEditorRef.value?.getModel()
      && version === model?.getVersionId(),
  };
};

const handleShowExample = () => {
  isShowExample.value = true;
};

const handleHiddenExample = () => {
  isShowExample.value = false;
};

// 触发编辑器高亮
const updateEditorDecorations = () => {
  const ranges = visibleErrorReasons.value.flatMap(({ range }) => range ? [range] : []);
  resourceEditorRef.value?.setLineDecorations(ranges);
};

// 触发编辑器添加下划波浪线
const updateEditorMarkers = () => {
  const markers = errorReasons.value.flatMap(({ range, message }) => range
    ? [{
      ...range,
      message,
    }]
    : []);
  resourceEditorRef.value?.setMarkers(markers);
};

// 处理代码错误消息点击事件，应跳转到编辑器对应行
const handleErrorMsgClick = (reason: ErrorReasonType, index: number) => {
  if (reason.range) {
    resourceEditorRef.value?.setCursorPos({
      lineNumber: reason.range.startLineNumber,
      column: reason.range.startColumn,
    });
  }
  activeVisibleErrorMsgIndex.value = index;
};

const setEditorCursor = (pos: 'top' | 'bottom') => {
  if (pos === 'top') {
    resourceEditorRef.value?.setCursorPos({ lineNumber: 1 });
  }
  else {
    resourceEditorRef.value?.setCursorPos({ toBottom: true });
  }
};

// 处理右侧错误类型计数器点击事件
const handleErrorCountClick = (type: CodeErrorMsgType) => {
  // 重复点击同一个类型，则重置选中态
  activeCodeMsgType.value = (type === activeCodeMsgType.value) ? 'All' : type;
  activeVisibleErrorMsgIndex.value = -1;
  updateEditorDecorations();
  // 如果有错误消息，点击后可以展开/收起错误消息栏
  if (visibleErrorReasons.value.length > 0) {
    isErrorConsoleCollapsed.value = !isErrorConsoleCollapsed.value;
  }
};

// 切换搜索面板
const toggleFindToolClick = () => {
  if (isFindPanelVisible.value) {
    resourceEditorRef.value?.closeFindPanel();
  }
  else {
    resourceEditorRef.value?.showFindPanel();
  }
};

// 切换字号
const handleFontSizeClick = () => {
  resourceEditorRef.value?.switchFontSize();
};

// 编辑器全屏
const handleFullScreenClick = () => {
  if (editorWrapRef?.value?.requestFullscreen) {
    editorWrapRef.value.requestFullscreen();
  }
};

// 记录编辑器错误消息栏折叠状态
const updateIsEditorMsgCollapsed = (collapsed: boolean) => {
  isErrorConsoleCollapsed.value = collapsed;
};

onMounted(() => {
  // 设置拉伸区高度范围
  const editorViewportHeight = resizeLayoutRef.value?.$el.clientHeight - 92;
  resizeLayoutAsideMax.value = Math.floor(editorViewportHeight * 0.8);
  resizeLayoutAsideMin.value = Math.ceil(editorViewportHeight * 0.2);
  // 更改编辑器主题和行号左边的提示列(glyph margin)
  resourceEditorRef.value?.setTheme('import-theme');
  resourceEditorRef.value?.updateOptions({ glyphMargin: true });
});

defineExpose({ getSourceSnapshot });
</script>

<style scoped lang="scss">
.import-container {
  padding: 20px 24px 18px;
  margin: 20px 24px;
  background-color: #FFF;
  box-shadow: 0 2px 4px 0 #1919290d;

  .import-header {

    .icon-ag-add-small {
      font-size: 16px;
    }

    .desc {
      margin-left: 12px;
      font-size: 12px;
      color: #979ba5;
    }
  }

  .import-editor {
    width: 100%;
    height: calc(100vh - 330px);
    margin-top: 10px;
    overflow: hidden;
    border-radius: 2px;

    .editor-layout-main {
      display: flex;
      height: 100%;
      flex-direction: column;

      .editor-toolbar {
        position: relative;
        z-index: 6;
        display: flex;
        height: 40px;
        background-color: #2e2e2e;
        box-shadow: 0 2px 4px 0 rgb(0 0 0 / 20%);
        justify-content: space-between;
        align-items: center;

        .tool-items {
          display: flex;
          height: 100%;
          padding-right: 16px;
          align-items: center;
          gap: 16px;

          .tool-item {
            display: flex;
            align-items: center;
            color: #999;
            cursor: pointer;

            &.active, &:hover {
              color: #ccc;
            }
          }
        }
      }

      .editor-main-content {
        display: flex;

        // 100% - 40px(.editor-toolbar高度) - 52px(.editor-footer-bar高度)
        height: calc(100% - 92px);

        :deep(.monaco-editor) {
          outline: none;
        }

        .editor-side-bar {
          display: flex;
          width: 32px;
          height: 100%;
          background-color: #212121;
          flex-direction: column;
          align-items: center;
          justify-content: space-between;

          .editor-error-counters {
            display: flex;
            width: 32px;
            flex-direction: column;
            align-items: center;

            .error-count-item {
              display: flex;
              width: 100%;
              height: 34px;
              font-size: 12px;
              line-height: 12px;
              cursor: pointer;
              border-bottom: 1px solid #222;
              flex-direction: column;
              justify-content: center;
              align-items: center;

              &:last-child {
                border-bottom: none;
              }

              &:hover, &.active {
                background-color: #3e3e3e;
              }

              .icon {
                margin-bottom: 2px;
              }

              .num {
                font-size: 12px;
                line-height: 14px;
              }
            }
          }

          .editor-error-shifts {
            display: flex;
            width: 100%;
            flex-direction: column;
            align-items: center;
            gap: 8px;

            .shift-btn {
              display: flex;
              width: 24px;
              height: 24px;
              cursor: pointer;
              background: #4D4D4D;
              border-radius: 2px;
              justify-content: center;
              align-items: center;

              &:active {
                background: #666;
              }
            }

            .shift-btn.prev {
              transform: rotate(-90deg);
            }

            .shift-btn.next {
              transform: rotate(90deg);
            }
          }
        }
      }

      .editor-footer-bar {
        z-index: 1;
        background-color: #1a1a1a;
        box-shadow: 0 -2px 4px 0 #00000029;

        .editor-footer-validate-btn {
          display: flex;
          height: 52px;
          padding-left: 24px;
          align-items: center;
        }

        .validation-message {
          display: flex;
          height: 52px;
          padding-right: 24px;
          padding-left: 24px;
          font-size: 12px;
          color: #DCDEE5;
          background-color: #212121;
          border-left: 4px solid #34d97b;
          align-items: center;
          gap: 8px;
        }
      }
    }

    .editor-messages-wrapper {
      position: relative;
      height: 100%;
      padding-top: 16px;
      font-size: 12px;
      background-color: #212121;
      border-left: 4px solid #1a1a1a;

      &.has-error-msg {
        border-left: 4px solid #B34747;
      }

      .editor-message {
        display: flex;
        height: 20px;
        padding: 0 4px 0 12px;
        margin-bottom: 6px;
        cursor: pointer;
        align-items: center;
        gap: 4px;

        &.active,
        &:hover {
          background-color: #333;
        }

        .msg-body {
          color: #ccc;
        }
      }
    }

    // 变更代码编辑器伸缩线样式

    :deep(.bk-resize-layout-bottom > .bk-resize-layout-aside) {
      background: #212121;
      border-top: 1px solid black;
    }

    // ResizeLayout 的折叠按钮样式

    :deep(.bk-resize-layout > .bk-resize-layout-aside .bk-resize-collapse) {
      margin-bottom: 9px;
      margin-left: -16px;
      background: #313238;

      &:hover {
        background-color: #63656E;
      }
    }

    &.hide-collapse-btn {
      // 隐藏 ResizeLayout 的折叠按钮

      :deep(.bk-resize-layout > .bk-resize-layout-aside .bk-resize-collapse) {
        display: none !important;
      }
    }

    // ResizeLayout 的折叠区应允许滚动

    :deep(.bk-resize-layout>.bk-resize-layout-aside .bk-resize-layout-aside-content) {
      overflow-y: auto;
    }
  }

  :deep(.upload-cls) {

    .bk-upload-list {
      display: none !important;
    }
  }

  // 编辑器错误行高亮样式

  :deep(.line-highlight-error) {
    background-color: #382322;
    opacity: 70%;
  }

  // 行号左侧图标样式

  :deep(.apigateway-icon.icon-ag-exclamation-circle-fill.f14) {
    color: #b34747;
  }

  // 让错误消息台的滚动条模仿 monaco editor 风格

  /* 整个滚动条 */

  ::-webkit-scrollbar {
    width: 14px; /* 滚动条宽度 */
  }

  /* 滚动条轨道 */

  ::-webkit-scrollbar-track {
    background: #1e1e1e;
  }

  /* 滚动条滑块 */

  ::-webkit-scrollbar-thumb {
    background: #4f4f4f;
  }

  /* 鼠标悬停时的滚动条滑块 */

  ::-webkit-scrollbar-thumb:hover {
    background: #555;
  }

  /* 鼠标按住时的滚动条滑块 */

  ::-webkit-scrollbar-thumb:active {
    background: #5e5e5e;
  }
}

:deep(.import-container .import-header .bk-form .bk-checkbox-label) {
  font-size: 12px;
}

:deep(.import-container .import-header .bk-form .bk-form-label) {
  font-size: 12px;
}

:deep(.import-container .import-header .bk-form .bk-form-content) {
  height: 32px;
}
</style>
