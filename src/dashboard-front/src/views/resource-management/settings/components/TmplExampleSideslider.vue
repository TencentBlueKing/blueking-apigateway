<template>
  <div class="tmpl-example-sideslider-wrapper">
    <BkSideslider
      v-model:is-show="renderShow"
      quick-close
      :title="t('模板示例')"
      width="660"
      ext-cls="stage-sideslider-cls"
      @hidden="handleHidden"
    >
      <div class="tmpl-example-monaco-editor">
        <editor-monaco
          v-model="editorText"
          read-only
        />
      </div>
    </BkSideslider>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';

import editorMonaco from '@/components/ag-editor/Index.vue';
import { RESOURCE_IMPORT_EXAMPLE } from '@/constants';

interface IProps { isShow?: boolean }

const { isShow = false } = defineProps<IProps>();

const emits = defineEmits<{ 'on-hidden': [void] }>();

const { t } = useI18n();

const renderShow = ref(isShow);
const editorText = ref<string>(RESOURCE_IMPORT_EXAMPLE.content);

const handleHidden = () => {
  renderShow.value = false;
  emits('on-hidden');
};

watch(() => isShow, (val) => {
  renderShow.value = val;
});

</script>

<style scoped lang="scss">
.tmpl-example-monaco-editor {
  width: 100%;
  height: calc(100vh - 52px);
}
</style>
