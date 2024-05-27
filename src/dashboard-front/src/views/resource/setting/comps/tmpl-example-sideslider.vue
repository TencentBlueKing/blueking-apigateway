<template>
  <div class="tmpl-example-sideslider-wrapper">
    <bk-sideslider
      v-model:isShow="renderShow"
      quick-close
      :title="t('模板示例')"
      width="660"
      ext-cls="stage-sideslider-cls"
      @hidden="handleHidden">
      <div class="tmpl-example-monaco-editor">
        <editor-monaco v-model="editorText" :read-only="true" />
      </div>
    </bk-sideslider>
  </div>
</template>
<script setup lang="ts">
import { ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';

import editorMonaco from '@/components/ag-editor.vue';
import exampleData from '@/constant/example-data';

const { t } = useI18n();
const props = defineProps({
  isShow: { type: Boolean, default: false },
});

const emits = defineEmits<(event: 'on-hidden') => void>();

const renderShow = ref(props.isShow);
const editorText = ref<string>(exampleData.content);

const handleHidden = () => {
  renderShow.value = false;
  emits('on-hidden');
};

watch(() => props.isShow, (val) => {
  renderShow.value = val;
});

</script>
<style scoped lang="scss">
.tmpl-example-monaco-editor {
  width: 100%;
  height: calc(100vh - 52px);
}
</style>
