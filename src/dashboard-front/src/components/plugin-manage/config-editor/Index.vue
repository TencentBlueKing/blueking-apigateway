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
  <div class="plugin-info">
    <main
      class="plugin-form-content"
      :class="{ 'pr-20px': showExample }"
    >
      <div
        v-if="!isAdd && isStage"
        class="info-alert mb-20px"
      >
        <BkAlert
          theme="warning"
          :title="t('修改插件配置将会直接影响线上环境，请谨慎操作')"
        />
      </div>
      <div class="info-header">
        <header class="choose-plugin">
          <div
            v-if="PLUGIN_ICONS.includes(choosePlugin)"
            class="cur-icon"
          >
            <svg class="icon svg-icon">
              <use
                :xlink:href="`#icon-ag-plugin-${choosePlugin}`"
                fill="#3a84f6"
              />
            </svg>
          </div>
          <div
            v-else-if="PLUGIN_ICONS_MIN.includes(choosePlugin)"
            class="cur-icon"
          >
            <svg class="icon svg-icon small">
              <use
                :xlink:href="`#icon-ag-plugin-${choosePlugin}`"
                fill="#3a84f6"
              />
            </svg>
          </div>
          <div
            v-else
            class="cur-icon"
          >
            {{ pluginCodeFirst(curPluginInfo?.code) }}
          </div>
          <div
            v-show="isAdd"
            @click="showChoosePlugin = true"
          >
            {{ t('切换插件') }}
          </div>
          <BkSelect
            v-show="showChoosePlugin"
            ref="pluginSelectRef"
            v-model="choosePlugin"
            :clearable="false"
            :disabled="isSubmitting"
            class="choose-plugin-select"
            @change="handleChoosePlugin"
            @blur="() => showChoosePlugin = false"
          >
            <BkOption
              v-for="item in pluginList"
              :id="item.code"
              :key="item.code"
              :name="item.name"
              :disabled="isBound(item)"
            />
          </BkSelect>
        </header>
        <main class="cur-text">
          <div class="cur-info">
            <span class="cur-name">{{ curPluginInfo?.name }}</span>
            <ul class="cur-binding-info">
              <li>
                {{ t('当前版本：') }}
                <span class="cur-version">{{ t('1.0.0') }}</span>
              </li>
              <li>
                {{ t('已绑定的资源：') }}
                <span :class="[curPluginInfo?.related_scope_count?.resource === 0 ? 'empty' : 'bound',]">
                  {{ curPluginInfo?.related_scope_count?.resource }}
                </span>
              </li>
              <li>
                {{ t('已绑定的环境：') }}
                <span :class="[curPluginInfo?.related_scope_count?.stage === 0 ? 'empty' : 'bound',]">
                  {{ curPluginInfo?.related_scope_count?.stage }}
                </span>
              </li>
            </ul>
          </div>
          <div class="cur-describe">
            {{ curPluginInfo?.notes }}
          </div>
        </main>
        <aside class="plugin-example-btn">
          <div class="flex flex-col items-start gap-12px">
            <IconButton
              text
              theme="primary"
              icon="bulk-edit"
              @click="toggleShowExample"
            >
              {{ t('填写示例') }}
            </IconButton>
            <IconButton
              text
              theme="primary"
              icon="jump"
              @click="handleDocClick"
            >
              {{ t('说明文档') }}
            </IconButton>
          </div>
        </aside>
      </div>
      <div class="info-form-container mt-20px">
        <PluginFormRenderer
          :key="editorKey"
          ref="editorRef"
          :definition="pluginDefinition"
          :code="choosePlugin"
          :type="type"
          :initial-yaml="editPlugin?.yaml"
        />
      </div>
      <div class="info-btn mt-20px">
        <div class="last-step">
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
              class="default-btn"
              :disabled="!canSubmit"
              :loading="isSubmitting"
            >
              {{ t('确定') }}
            </BkButton>
          </BkPopConfirm>
          <BkButton
            v-else
            theme="primary"
            class="default-btn"
            :disabled="!canSubmit"
            :loading="isSubmitting"
            @click="handleAdd"
          >
            {{ t('确定') }}
          </BkButton>
          <BkButton
            v-if="isAdd"
            class="prev-btn ml-8px"
            :disabled="isSubmitting"
            @click="handlePre"
          >
            {{ t('上一步') }}
          </BkButton>
          <BkButton
            class="default-btn ml-8px"
            :disabled="isSubmitting"
            @click="handleCancel"
          >
            {{ t('取消') }}
          </BkButton>
        </div>
      </div>
    </main>
    <!--  右侧插件使用示例  -->
    <aside
      v-if="showExample"
      class="plugin-example-content"
    >
      <header class="example-content-header">
        <span class="header-title">{{ t('插件配置示例') }}</span>
        <AgIcon
          class="close-btn"
          size="24"
          name="icon-close"
          @click="toggleShowExample"
        />
      </header>
      <main class="example-main">
        <pre
          v-bk-xss-html="exampleHtml"
          class="example-pre"
        />
      </main>
    </aside>
  </div>
</template>

<script setup lang="ts">
import { snakeCase } from 'lodash-es';
import type { ComponentPublicInstance } from 'vue';
import { createPlugin, updatePluginConfig } from '@/services/source/plugin-manage';
import type { IPluginConfigRetrieveOutput } from '@/services/types/responses/gateways';
import { Message } from 'bkui-vue';
import { useEnv, useStage } from '@/stores';
import { onClickOutside } from '@vueuse/core';
import { PLUGIN_ICONS, PLUGIN_ICONS_MIN } from '@/constants';
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
const showChoosePlugin = ref(false);
const isSubmitting = ref(false);
const editorRef = useTemplateRef<InstanceType<typeof PluginFormRenderer>>('editorRef');
const pluginSelectRef = useTemplateRef<ComponentPublicInstance & { isFocus?: boolean }>('pluginSelectRef');

const isAdd = computed(() => type === 'add');
const isStage = computed(() => scopeInfo.scopeType === 'stage');
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

const pluginCodeFirst = (code?: string) => code?.charAt(3)?.toUpperCase();

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

onClickOutside(pluginSelectRef, () => {
  if (pluginSelectRef.value?.isFocus === false) {
    showChoosePlugin.value = false;
  }
});

defineExpose({ clearValidate });
</script>

<style lang="scss" scoped>
.plugin-info {
  display: flex;

  .plugin-form-content {
    flex-grow: 1;
  }

  .plugin-example-content {
    width: 400px;
    padding: 0 0 20px 20px;
    border-left: 1px solid #dcdee5;
    flex-shrink: 0;

    .example-content-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;

      .header-title {
        height: 24px;
        font-size: 16px;
        line-height: 24px;
        color: #313238;
      }

      .close-btn {
        color: #979BA5;
        cursor: pointer;

        &:hover {
          color: #63656e;
        }
      }
    }

    .example-main {

      .example-pre {
        overflow-x: auto;
        font-family: inherit;
        font-size: 14px;
        line-height: 22px;
        color: #4D4F56;
        word-wrap: break-word;
        white-space: pre-wrap;
      }
    }
  }
}

.info-header {
  display: flex;
  padding: 12px 24px;
  background-color: #f5f7fa;
  border-radius: 2px;
  align-items: flex-start;
  gap: 24px;

  .choose-plugin {
    flex-shrink: 0;
    position: relative;
    display: flex;
    flex-direction: column;
    align-content: center;
    gap: 4px;
    font-size: 14px;
    color: #3A84FF;
    cursor: pointer;

    .cur-icon {
      display: flex;
      width: 56px;
      height: 56px;
      font-size: 28px;
      font-weight: 700;
      line-height: 56px;
      color: #3a84f6;
      background: #EAEBF0;
      border-radius: 50%;
      justify-content: center;
      align-items: center;

      .svg-icon {
        width: 56px;
        height: 56px;

        &.small {
          width: 28px;
          height: 28px;
        }
      }
    }
  }

  .cur-text {
    flex-grow: 1;

    .cur-info {
      display: flex;
      margin-top: 12px;
      margin-bottom: 10px;
      align-items: center;

      .cur-name {
        margin-right: 24px;
        font-size: 16px;
        font-weight: 700;
        color: #313238;
      }

      .cur-binding-info {
        display: flex;
        font-size: 12px;
        color: #979ba5;
        align-items: center;

        li:not(:nth-last-child(1)) {
          margin-right: 32px;
        }

        .cur-version {
          font-weight: 700;
          color: #313238;
        }

        .empty {
          font-weight: 700;
          color: #3a84ff;
        }

        .bound {
          font-weight: 700;
          color: #3a84ff;
        }
      }
    }

    .cur-describe {
      font-size: 12px;
      color: #63656E;
    }
  }

  .plugin-example-btn {
    margin-top: 16px;
    font-size: 14px;
    flex-shrink: 0;
  }
}

.last-step {
  font-size: 0;

  .default-btn {
    min-width: 88px;
  }

  .prev-btn {
    min-width: 74px;
  }
}

.choose-plugin-select {
  position: absolute;
  top: 85px;
  left: 0;
  z-index: 1;
  width: 300px;

  :deep(.bk-input) {
    border: 1px solid #DCDEE5;

    .angle-up {
      color: #DCDEE5;
    }
  }
}
</style>
