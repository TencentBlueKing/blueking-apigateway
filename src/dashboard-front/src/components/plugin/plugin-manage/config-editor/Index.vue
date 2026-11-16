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
  <BkResizeLayout
    class="plugin-info"
    :border="false"
    :placement="isNarrow ? 'bottom' : 'right'"
    :initial-divide="showExample ? exampleSize : 0"
    :min="showExample ? minExampleSize : 0"
    :max="maxExampleSize"
    :disabled="!showExample"
    :class="{ 'is-example-hidden': !showExample }"
    @after-resize="handleExampleResize"
  >
    <template #main>
      <div class="plugin-form-content">
        <BkAlert
          v-if="!isAdd && isStage"
          class="mb-24px"
          theme="warning"
          :title="t('修改插件配置将会直接影响线上环境，请谨慎操作')"
        />
        <header
          ref="pluginHeader"
          class="info-header"
          :class="{ 'is-switching': isSwitching }"
        >
          <PluginIcon :code="choosePlugin" />
          <div class="plugin-summary">
            <div class="plugin-summary-heading">
              <span class="plugin-name">{{ curPluginInfo?.name }}</span>
              <ul class="plugin-metadata">
                <li>{{ t('版本：') }} V1.0.0</li>
                <li>
                  {{ t('已绑环境：') }}
                  <span>{{ curPluginInfo?.related_scope_count?.stage ?? '--' }}</span>
                </li>
                <li>
                  {{ t('已绑资源：') }}
                  <span>{{ curPluginInfo?.related_scope_count?.resource ?? '--' }}</span>
                </li>
              </ul>
            </div>
            <p
              v-if="curPluginInfo?.notes"
              class="plugin-description"
            >
              {{ curPluginInfo.notes }}
            </p>
            <div class="plugin-links">
              <AgIconButton
                text
                theme="primary"
                icon="jump"
                @click="handleDocClick"
              >
                {{ t('说明文档') }}
              </AgIconButton>
              <AgIconButton
                v-if="exampleHtml"
                text
                theme="primary"
                icon="bulk-edit"
                :aria-expanded="showExample"
                @click="toggleShowExample"
              >
                {{ t('填写示例') }}
              </AgIconButton>
            </div>
          </div>
          <BkSelect
            v-if="isAdd"
            v-model="choosePlugin"
            class="plugin-switch"
            :clearable="false"
            :filterable="false"
            :input-search="false"
            :show-selected-icon="false"
            :disabled="isSubmitting"
            :scroll-height="332"
            :popover-options="switchPopoverOptions"
            @change="handleChoosePlugin"
            @toggle="isSwitching = $event"
          >
            <template #trigger>
              <BkButton
                theme="primary"
                size="small"
                :disabled="isSubmitting"
                :aria-expanded="isSwitching"
              >
                {{ t('切换插件') }}
              </BkButton>
            </template>
            <BkOption
              v-for="item in pluginList"
              :id="item.code"
              :key="item.code"
              :name="item.name"
              :disabled="isBound(item)"
              class="plugin-switch-option"
            >
              <div class="plugin-switch-row">
                <PluginIcon :code="item.code" />
                <div class="plugin-switch-info">
                  <div class="plugin-switch-name">
                    {{ item.name }}
                  </div>
                  <div
                    v-if="item.notes"
                    class="plugin-switch-description"
                  >
                    {{ item.notes }}
                  </div>
                </div>
              </div>
            </BkOption>
          </BkSelect>
        </header>
        <PluginFormRenderer
          :key="editorKey"
          ref="editorRef"
          class="plugin-config-form"
          :definition="pluginDefinition"
          :code="choosePlugin"
          :type="type"
          :initial-yaml="editPlugin?.yaml"
        />
        <div class="plugin-form-actions">
          <BkPopConfirm
            v-if="isStage"
            :title="t(
              '确认{optType}插件（{name}）到 {stage} 环境？',
              {
                optType: isAdd ? t('添加') : t('修改'),
                name: curPluginInfo?.name,
                stage: stageStore?.curStageData?.name
              }
            )"
            :content="t('插件配置变更后，将立即影响线上环境，请确认。')"
            trigger="click"
            @confirm="handleAdd"
          >
            <BkButton
              theme="primary"
              :disabled="!canSubmit"
              :loading="isSubmitting"
            >
              {{ t('确定') }}
            </BkButton>
          </BkPopConfirm>
          <BkButton
            v-else
            theme="primary"
            :disabled="!canSubmit"
            :loading="isSubmitting"
            @click="handleAdd"
          >
            {{ t('确定') }}
          </BkButton>
          <BkButton
            v-if="isAdd"
            :disabled="isSubmitting"
            @click="handlePre"
          >
            {{ t('上一步') }}
          </BkButton>
          <BkButton
            :disabled="isSubmitting"
            @click="handleCancel"
          >
            {{ t('取消') }}
          </BkButton>
        </div>
      </div>
    </template>
    <template #aside>
      <aside
        v-if="showExample"
        class="plugin-example-content"
      >
        <header class="example-content-header">
          <span>{{ t('插件配置示例') }}</span>
          <BkButton
            text
            class="example-close"
            :aria-label="t('关闭')"
            @click="toggleShowExample"
          >
            <AgIcon
              name="icon-close"
              size="24"
              aria-hidden="true"
            />
          </BkButton>
        </header>
        <pre
          v-bk-xss-html="exampleHtml"
          class="example-pre"
        />
      </aside>
    </template>
  </BkResizeLayout>
</template>

<script setup lang="ts">
import { snakeCase } from 'lodash-es';
import { createPlugin, updatePluginConfig } from '@/services/source/gateway/plugin';
import type { IPluginConfigRetrieveOutput } from '@/services/types/responses/gateways';
import { Message } from 'bkui-vue';
import { useEnv, useStage } from '@/stores';
import { useElementSize, useWindowSize } from '@vueuse/core';
import PluginIcon from '../components/PluginIcon.vue';
import PluginFormRenderer from './components/PluginFormRenderer.vue';
import { getPluginDefinition, getPluginExample } from './definitions';
import { PluginEditorError } from './form-adapter';

interface IPluginInfoItem {
  code: string
  name: string
  id?: number
  notes?: string
  related_scope_count?: {
    resource: number
    stage: number
  }
}

interface IScopeInfo {
  scopeType: string
  scopeId: number
  apigwId: number
}

interface IProps {
  curPlugin: IPluginInfoItem | null
  scopeInfo: IScopeInfo
  editPlugin?: IPluginConfigRetrieveOutput | null
  type: 'add' | 'edit'
  pluginList?: IPluginInfoItem[]
  bindingPlugins?: IPluginInfoItem[]
}

interface IEmits {
  'on-change': [type: 'pre' | 'addCancel' | 'editCancel' | 'addSuccess' | 'editSuccess']
  'choose-plugin': [plugin: IPluginInfoItem]
}

const showExample = defineModel<boolean>('showExample', { default: false });

const {
  curPlugin,
  scopeInfo,
  editPlugin = null,
  type,
  pluginList = [],
  bindingPlugins = [],
} = defineProps<IProps>();

const emit = defineEmits<IEmits>();

const { t, locale } = useI18n();
const stageStore = useStage();
const envStore = useEnv();

const choosePlugin = ref(curPlugin?.code ?? '');
const isSwitching = ref(false);
const exampleWidth = ref(400);
const exampleHeight = ref(240);
const isSubmitting = ref(false);
const editorRef = useTemplateRef<InstanceType<typeof PluginFormRenderer>>('editorRef');
const pluginHeader = useTemplateRef<HTMLElement>('pluginHeader');
const { width: headerWidth } = useElementSize(pluginHeader, undefined, { box: 'border-box' });
const { width: viewportWidth, height: viewportHeight } = useWindowSize();

const isAdd = computed(() => type === 'add');
const isStage = computed(() => scopeInfo.scopeType === 'stage');
const isNarrow = computed(() => viewportWidth.value < 960);
const minExampleSize = computed(() => isNarrow.value ? 120 : 260);
const maxExampleSize = computed(() => isNarrow.value
  ? Math.max(minExampleSize.value, Math.floor(viewportHeight.value * 0.5))
  : Math.min(640, viewportWidth.value - 640));
const exampleSize = computed(() => Math.min(
  isNarrow.value ? exampleHeight.value : exampleWidth.value,
  maxExampleSize.value,
));
const switchPopoverOptions = computed(() => ({
  width: headerWidth.value,
  floatingReference: pluginHeader.value,
}));
const selectedPlugin = computed(() => pluginList.find(plugin => plugin.code === choosePlugin.value));
const curPluginInfo = computed(() => {
  if (curPlugin?.code === choosePlugin.value) {
    return {
      ...selectedPlugin.value,
      ...curPlugin,
    };
  }
  return selectedPlugin.value;
});
const pluginDefinition = computed(() => getPluginDefinition(choosePlugin.value));
const editorKey = computed(() => [
  scopeInfo.apigwId,
  scopeInfo.scopeType,
  scopeInfo.scopeId,
  choosePlugin.value,
  type,
  editPlugin?.id ?? '',
].join(':'));
const canSubmit = computed(() => {
  const typeId = isAdd.value ? selectedPlugin.value?.id : editPlugin?.type_id;
  return !!curPluginInfo.value && !!typeId && !!editorRef.value?.isReady;
});
const exampleHtml = computed(() => getPluginExample(choosePlugin.value, locale.value));

watch(() => curPlugin?.code, (code) => {
  choosePlugin.value = code ?? '';
});

watch(exampleHtml, (example) => {
  if (!example) {
    showExample.value = false;
  }
});

const isBound = (plugin: IPluginInfoItem) => bindingPlugins.some(item => item.code === plugin.code);

const clearValidate = () => {
  editorRef.value?.clearValidate();
};

const handlePre = () => {
  clearValidate();
  emit('on-change', 'pre');
};

const handleAdd = async () => {
  if (isSubmitting.value || !canSubmit.value || !editorRef.value || !curPluginInfo.value) {
    return;
  }

  const submissionKey = editorKey.value;
  const adding = isAdd.value;
  const plugin = curPluginInfo.value;
  const currentEditPlugin = editPlugin;
  const typeId = selectedPlugin.value?.id;
  const { scopeType, scopeId, apigwId } = scopeInfo;
  const code = choosePlugin.value;
  isSubmitting.value = true;
  try {
    const yaml = await editorRef.value.getYaml();
    if (submissionKey !== editorKey.value) {
      return;
    }
    if (adding) {
      if (!typeId) {
        return;
      }
      await createPlugin(apigwId, scopeType, scopeId, code, {
        name: plugin.name,
        type_id: typeId,
        yaml,
      });
    }
    else {
      if (!currentEditPlugin) {
        return;
      }
      await updatePluginConfig(apigwId, scopeType, scopeId, code, currentEditPlugin.id, {
        name: currentEditPlugin.name ?? plugin.name,
        type_id: currentEditPlugin.type_id,
        yaml,
      });
    }
    if (submissionKey !== editorKey.value) {
      return;
    }
    Message({
      message: adding ? t('添加成功') : t('修改成功'),
      theme: 'success',
      width: 'auto',
    });
    emit('on-change', adding ? 'addSuccess' : 'editSuccess');
  }
  catch (error) {
    if (error instanceof PluginEditorError) {
      Message({
        message: t(error.message),
        theme: 'error',
      });
    }
    // 表单自行展示字段校验错误，请求错误由 HTTP 层统一处理。
  }
  finally {
    isSubmitting.value = false;
  }
};

const handleCancel = () => {
  clearValidate();
  emit('on-change', isAdd.value ? 'addCancel' : 'editCancel');
};

const handleChoosePlugin = () => {
  if (selectedPlugin.value) {
    emit('choose-plugin', selectedPlugin.value);
  }
};

const toggleShowExample = () => {
  showExample.value = !showExample.value;
};

const handleDocClick = () => {
  const pluginNameInSnakeCase = snakeCase(choosePlugin.value).toUpperCase();
  const link = envStore.env.DOC_LINKS[`PLUGIN_${pluginNameInSnakeCase}` as keyof typeof envStore.env.DOC_LINKS];
  if (link) {
    window.open(link, '_blank');
  }
};

const handleExampleResize = (size: number) => {
  if (!Number.isFinite(size)) {
    return;
  }
  if (isNarrow.value) {
    exampleHeight.value = size;
  }
  else {
    exampleWidth.value = size;
  }
};

defineExpose({ clearValidate });
</script>

<style lang="scss" scoped>
.plugin-info {
  min-width: 0;
  min-height: 0;

  :deep(.bk-resize-layout-main) {
    min-width: 0;
    min-height: 0;
  }

  :deep(.bk-resize-layout-aside) {
    flex-shrink: 0;
  }

  // 底部示例栏的拖拽辅助线在首次拖拽前也需要定位在容器内。

  :deep(.bk-resize-proxy.bottom) {
    bottom: 0;
  }

  &.is-example-hidden :deep(.bk-resize-layout-aside) {
    display: none;
  }
}

.plugin-form-content {
  height: 100%;
  padding: 24px;
  overflow: auto;
}

.info-header {
  display: flex;
  padding: 16px;
  background-color: #f5f7fa;
  border-radius: 2px;
  align-items: flex-start;
  gap: 16px;

  &.is-switching {
    background-color: #f0f5ff;
  }
}

.plugin-summary {
  min-width: 0;
  flex: 1;
}

.plugin-summary-heading,
.plugin-metadata,
.plugin-links {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}

.plugin-summary-heading {
  min-height: 24px;
  gap: 4px 24px;
}

.plugin-name,
.plugin-switch-name {
  font-size: 14px;
  font-weight: 700;
  line-height: 24px;
  color: #313238;
  overflow-wrap: anywhere;
}

.plugin-metadata {
  margin: 0;
  font-size: 12px;
  line-height: 20px;
  color: #979ba5;
  gap: 0 16px;

  span {
    color: #63656e;
  }
}

.plugin-description,
.plugin-switch-description {
  margin: 8px 0 0;
  font-size: 12px;
  line-height: 20px;
  color: #4d4f56;
  overflow-wrap: anywhere;
}

.plugin-links {
  margin-top: 8px;
  gap: 4px 16px;

  :deep(.bk-button) {
    height: 20px;
    padding: 0;
    font-size: 12px;
    line-height: 20px;
  }
}

.plugin-switch {
  align-self: center;
  flex: none;

  :deep(.bk-button) {
    min-width: 92px;
  }
}

.plugin-switch-info {
  min-width: 0;
  flex: 1;
}

.plugin-switch-row {
  display: flex;
  width: 100%;
  min-height: 80px;
  padding: 16px 4px;
  border-bottom: 1px solid #eaebf0;
  align-items: center;
  gap: 16px;
}

.plugin-switch-option.is-selected .plugin-switch-name,
.plugin-switch-option.is-selected .plugin-switch-description {
  color: #1768ef;
}

.plugin-switch-option.is-disabled .plugin-switch-name,
.plugin-switch-option.is-disabled .plugin-switch-description {
  color: #979ba5;
}

.plugin-switch-description {
  margin-top: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.plugin-config-form {
  margin-top: 24px;
}

.plugin-form-actions {
  display: flex;
  margin-top: 8px;
  flex-wrap: wrap;
  gap: 8px;

  .bk-button {
    min-width: 88px;
  }
}

.plugin-example-content {
  display: flex;
  height: 100%;
  min-height: 0;
  background-color: #fff;
  flex-direction: column;
}

.example-content-header {
  display: flex;
  min-height: 48px;
  padding: 0 24px;
  font-size: 14px;
  color: #313238;
  border-bottom: 1px solid #eaebf0;
  align-items: center;
  flex: none;
  justify-content: space-between;
}

.example-close.bk-button {
  padding: 0;
  color: #979ba5;

  &:hover {
    color: #63656e;
  }
}

.example-pre {
  padding: 20px;
  margin: 0;
  overflow: auto;
  font-family: inherit;
  font-size: 13px;
  line-height: 20px;
  color: #313238;
  white-space: pre-wrap;
  flex: 1;
  overflow-wrap: anywhere;
}

@media (width <= 560px) {

  .plugin-form-content {
    padding: 16px;
  }

  .info-header {
    flex-wrap: wrap;
  }

  .plugin-summary {
    flex-basis: calc(100% - 64px);
  }

  .plugin-switch {
    margin-left: 64px;
  }
}
</style>
