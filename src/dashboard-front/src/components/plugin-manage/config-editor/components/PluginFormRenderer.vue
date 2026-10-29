<template>
  <div>
    <BkAlert
      v-if="errorMessage"
      theme="error"
      :title="t(errorMessage)"
    />
    <template v-else-if="definition">
      <BkAlert
        v-if="definition.notice"
        class="mb-16px"
        theme="warning"
        :title="t(definition.notice)"
      />
      <Component
        :is="editor.component"
        v-if="editor?.kind === 'custom'"
        :key="formVersion"
        ref="formRef"
        :data="formData"
      />
      <Component
        :is="editor.component"
        v-else-if="editor?.kind === 'schema'"
        :key="formVersion"
        ref="formRef"
        v-model="formData"
        :route-mode="code"
        :schema="formConfig?.schema"
        :layout="formConfig?.layout"
      />
      <Component
        :is="editor.component"
        v-else-if="editor?.kind === 'whitelist'"
        :key="formVersion"
        ref="formRef"
        class="white-list"
        :type="type"
        :yaml-str="whitelistYaml"
      />
      <div
        v-else-if="editor?.kind === 'none'"
        class="color-#63656e text-14px"
      >
        {{ t('该插件无需任何参数') }}
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import {
  PluginEditorError,
  collectPluginYaml,
  parsePluginConfig,
  serializePluginConfig,
} from '../form-adapter';
import type { IPluginDefinition, PluginFormHandle } from '../types';

interface IProps {
  definition?: IPluginDefinition
  code: string
  type: 'add' | 'edit'
  initialYaml?: string | null
}

const { definition = undefined, code, type, initialYaml = null } = defineProps<IProps>();

const { t, locale } = useI18n();

const formData = ref<Record<string, any>>({});
const formVersion = ref(0);
const initializationError = ref('');
const whitelistYaml = ref('');
const formRef = ref<PluginFormHandle | null>(null);

const editor = computed(() => definition?.editor);
// 切换语言时只更新标签和布局，保留用户当前的配置草稿。
const formConfig = computed(() => editor.value?.kind === 'schema'
  ? editor.value.getFormConfig(locale.value)
  : undefined);
const errorMessage = computed(() => {
  if (!definition) {
    return '暂不支持配置此插件';
  }
  if (editor.value?.kind === 'schema' && !formConfig.value?.schema) {
    return '表单加载失败';
  }
  return initializationError.value;
});
const isReady = computed(() => !errorMessage.value && (editor.value?.kind === 'none' || !!formRef.value));

const resetForm = () => {
  initializationError.value = '';
  formData.value = {};
  whitelistYaml.value = '';
  formVersion.value++;
  try {
    if (editor.value?.kind === 'none') {
      return;
    }
    const config = type === 'edit' ? parsePluginConfig(initialYaml) : {};
    if (editor.value?.kind === 'whitelist' && type === 'edit') {
      config.exempted_apps ??= [];
      if (!Array.isArray(config.exempted_apps)) {
        throw new PluginEditorError('插件配置格式错误，请检查后重试');
      }
      whitelistYaml.value = serializePluginConfig(config);
    }
    formData.value = config;
  }
  catch (error) {
    initializationError.value = error instanceof PluginEditorError ? error.message : '表单加载失败';
  }
};

watch(() => [code, type, initialYaml, definition] as const, resetForm, { immediate: true });

const getYaml = async () => {
  if (!isReady.value || !editor.value) {
    throw new PluginEditorError(errorMessage.value || '表单加载失败');
  }
  return await collectPluginYaml(editor.value, formRef.value);
};

const clearValidate = () => {
  if (formRef.value && 'clearValidate' in formRef.value) {
    formRef.value.clearValidate?.();
  }
};

defineExpose({
  getYaml,
  clearValidate,
  isReady,
});
</script>
