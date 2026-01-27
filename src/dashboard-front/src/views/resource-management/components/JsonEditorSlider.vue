<template>
  <AgSideSlider
    v-model="visible"
    :title="t('通过 JSON 生成')"
    :scrollbar="false"
    render-directive="if"
  >
    <div class="px-40px pt-40px text-12px">
      <div class="mb-24px">
        <IconButton
          theme="primary"
          icon="upload"
          @click="handleImportJSON"
        >
          {{ t('导入 JSON') }}
        </IconButton>
      </div>
      <div class="editor-layout">
        <!--  顶部编辑器工具栏 -->
        <header class="editor-toolbar">
          <span class="p-10px pl-25px color-#ccc text-14px">{{ t('编辑 JSON') }}</span>
          <aside class="tool-items">
            <section
              class="tool-item"
              @click="handleFormat"
            >
              <AgIcon
                name="geshihua"
                size="16"
              />
            </section>
          </aside>
        </header>
        <main class="editor-main-content">
          <EditorMonaco
            ref="editorRef"
            :model-value="source"
            language="json"
            :minimap="false"
          />
        </main>
      </div>
    </div>
    <template #footer>
      <div class="pl-40px">
        <BkButton
          class="mr-8px w-88px"
          theme="primary"
          @click="handleEditorConfirm"
        >
          {{ t("确定") }}
        </BkButton>
        <BkButton
          class="w-88px"
        >
          {{ t("取消") }}
        </BkButton>
      </div>
    </template>
  </AgSideSlider>
</template>

<script setup lang="ts">
import AgSideSlider from '@/components/ag-sideslider/Index.vue';
import EditorMonaco from '@/components/ag-editor/Index.vue';
import { useFileSystemAccess } from '@vueuse/core';
import { Message } from 'bkui-vue';

const visible = defineModel<boolean>({ default: false });

const source = defineModel<string>('source', { default: '{}' });

const emit = defineEmits<{ confirm: [jsonObj: Record<string, any>] }>();

const { t } = useI18n();

const { data: importedJsonText, fileSize, open } = useFileSystemAccess({
  dataType: 'Text',
  types: [{
    description: 'text',
    accept: { 'text/plain': ['.txt', '.json'] },
  }],
});

const editorRef = ref<InstanceType<typeof EditorMonaco>>();

const handleImportJSON = async () => {
  await open();
  // 文件大小限制为 10KB
  if (fileSize.value > 10 * 1024) {
    Message({
      theme: 'warning',
      message: t('文件大小超过 10KB'),
    });
    return;
  }

  if (importedJsonText.value) {
    source.value = importedJsonText.value;
    editorRef.value!.setValue(importedJsonText.value);
  }
  else {
    Message({
      theme: 'warning',
      message: t('请选择合法的 JSON'),
    });
  }
};

const handleEditorConfirm = () => {
  try {
    emit('confirm', JSON.parse(source.value));
    visible.value = false;
  }
  catch {
    Message({
      theme: 'warning',
      message: t('请输入合法的 JSON'),
    });
  }
};

const handleFormat = () => {
  editorRef.value!.handleFormat();
};

</script>

<style scoped lang="scss">

.editor-layout {
  display: flex;
  height: 500px;
  flex-direction: column;

  .editor-toolbar {
    position: relative;
    z-index: 6;
    display: flex;
    height: 40px;
    margin-bottom: -26px;
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
    height: calc(100% - 92px);

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
}

</style>
