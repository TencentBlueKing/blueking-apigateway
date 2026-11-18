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
    class="imported-resources-wrap"
  >
    <header class="res-counter-banner">
      <main>
        <AgIcon
          name="info"
          size="16"
          class="mr-5px color-#3A84FF"
        />
        <span>{{ t('共') }}<span class="font-bold px-5px">{{ resourceCount }}</span>{{ t('个资源，新增') }}<span
          class="font-bold color-#34d97b px-5px"
        >{{ groups.add.length }}</span>{{ t('个，更新') }}<span
          class="font-bold color-#ffb400 px-5px"
        >{{ groups.update.length }}</span>{{ t('个，配置未变化') }}<span
          class="font-bold color-#63656e px-5px"
        >{{ groups.unchanged.length }}</span>{{ t('个，取消导入') }}<span class="font-bold color-#ff5656 px-5px">{{
          groups.excluded.length
        }}</span>{{ t('个') }}</span>
      </main>
      <aside>
        <BkButton
          text
          theme="primary"
          @click="emit('restore-all')"
        >
          <AgIcon
            name="undo-2"
            size="16"
            class="mr-4px color-#3A84FF"
          />
          {{ t('恢复取消导入的资源') }}
        </BkButton>
      </aside>
    </header>
    <section class="res-content-wrap">
      <BkCollapse
        v-model="panelNamesList"
        class="collapse-cls"
        use-card-theme
      >
        <!--  新增的资源  -->
        <BkCollapsePanel name="add">
          <template #header>
            <div class="panel-header">
              <main class="flex items-center">
                <AngleUpFill
                  :class="[panelNamesList.includes('add') ? 'panel-header-show' : 'panel-header-hide']"
                />
                <div class="title">
                  {{ t('新增的资源（共') }}
                  <span class="color-#34b97b">{{ groups.add.length }}</span>
                  {{ t('个）') }}
                </div>
              </main>
              <aside @click.stop.prevent>
                <BkInput
                  v-model="filterDraft.add"
                  clearable
                  :placeholder="t('请输入资源名称/路径，按Enter搜索')"
                  class="w-578px!"
                  @enter="() => applyResourceFilter('add')"
                  @clear="() => applyResourceFilter('add')"
                >
                  <template #prefix>
                    <aside
                      class="flex items-center ml-10px"
                      @click="() => applyResourceFilter('add')"
                    >
                      <AgIcon name="search" />
                    </aside>
                  </template>
                </BkInput>
              </aside>
            </div>
          </template>
          <template #content>
            <div class="pb-24px">
              <!--  新增资源 table  -->
              <PendingResourceTable
                v-model:temp-auth-config="tempAuthConfig"
                v-model:temp-public-config="tempPublicConfig"
                action="add"
                :table-data="tableDataToAdd"
                :keyword="filterKeyword.add"
                :doc-config="docConfig"
                :is-ai-gateway="isAiGateway"
                @show-row-doc="handleShowResourceDoc"
                @show-row-plugin="handleShowPluginsSlider"
                @show-row-edit="handleEdit"
                @toggle-row-unchecked="emit('toggle-resource', $event)"
                @confirm-auth-config="handleConfirmAuthConfigPopConfirm"
                @confirm-pub-config="handleConfirmPublicConfigPopConfirm"
                @confirm-doc-config="emit('update-doc-config', $event)"
                @clear-filter="clearFilterInput"
              />
            </div>
          </template>
        </BkCollapsePanel>
        <!--  更新的资源  -->
        <BkCollapsePanel name="update">
          <template #header>
            <div class="panel-header">
              <main class="flex items-center">
                <AngleUpFill
                  :class="[panelNamesList.includes('update') ? 'panel-header-show' : 'panel-header-hide']"
                />
                <div class="title">
                  {{ t('更新的资源（共') }}
                  <span class="color-#ffb400">{{ groups.update.length }}</span>
                  {{ t('个）') }}
                </div>
              </main>
              <aside @click.stop.prevent>
                <BkInput
                  v-model="filterDraft.update"
                  clearable
                  :placeholder="t('请输入资源名称/路径，按Enter搜索')"
                  class="w-578px!"
                  @enter="() => applyResourceFilter('update')"
                  @clear="() => applyResourceFilter('update')"
                >
                  <template #prefix>
                    <aside
                      class="flex items-center ml-10px"
                      @click="() => applyResourceFilter('update')"
                    >
                      <AgIcon name="search" />
                    </aside>
                  </template>
                </BkInput>
              </aside>
            </div>
          </template>
          <template #content>
            <div class="pb-24px">
              <!--  更新资源 table  -->
              <PendingResourceTable
                v-model:temp-auth-config="tempAuthConfig"
                v-model:temp-public-config="tempPublicConfig"
                action="update"
                :table-data="tableDataToUpdate"
                :keyword="filterKeyword.update"
                :is-ai-gateway="isAiGateway"
                @show-row-doc="handleShowResourceDoc"
                @show-row-plugin="handleShowPluginsSlider"
                @show-row-edit="handleEdit"
                @toggle-row-unchecked="emit('toggle-resource', $event)"
                @confirm-auth-config="handleConfirmAuthConfigPopConfirm"
                @confirm-pub-config="handleConfirmPublicConfigPopConfirm"
                @clear-filter="clearFilterInput"
              />
            </div>
          </template>
        </BkCollapsePanel>
        <!--  配置未变化的资源仅展示，不参与导入  -->
        <BkCollapsePanel
          name="unchanged"
          class="unchanged-resources-panel"
        >
          <template #header>
            <div class="panel-header">
              <main class="flex items-center">
                <AngleUpFill
                  :class="[panelNamesList.includes('unchanged') ? 'panel-header-show' : 'panel-header-hide']"
                />
                <div class="title">
                  {{ t('配置未变化（共') }}
                  <span class="color-#63656e">{{ groups.unchanged.length }}</span>
                  {{ t('个）') }}
                </div>
              </main>
            </div>
          </template>
          <template #content>
            <div class="pb-24px">
              <ExcludedResourceTable
                :table-data="groups.unchanged"
                :is-ai-gateway="isAiGateway"
                :show-doc="docConfig.showDoc"
                readonly
              />
            </div>
          </template>
        </BkCollapsePanel>
        <!--  不导入的资源  -->
        <BkCollapsePanel name="uncheck">
          <template #header>
            <div class="panel-header">
              <main class="flex items-center">
                <AngleUpFill
                  :class="[panelNamesList.includes('uncheck') ? 'panel-header-show' : 'panel-header-hide']"
                />
                <div class="title">
                  {{ t('不导入的资源（共') }}
                  <span class="color-#ff5656">{{ groups.excluded.length }}</span>
                  {{ t('个）') }}
                </div>
              </main>
            </div>
          </template>
          <template #content>
            <div class="pb-24px">
              <ExcludedResourceTable
                :table-data="groups.excluded"
                :is-ai-gateway="isAiGateway"
                @show-row-doc="handleShowResourceDoc"
                @show-row-plugin="handleShowPluginsSlider"
                @toggle-row-unchecked="emit('toggle-resource', $event)"
              />
            </div>
          </template>
        </BkCollapsePanel>
      </BkCollapse>
    </section>
    <!--  编辑资源侧栏  -->
    <ResourceEditSlider
      :resource="editingResource"
      :is-slider-show="isSliderShow"
      @on-hidden="handleEditSliderHidden"
      @submit="emit('edit-resource', $event)"
    />
    <!-- 文档侧边栏 -->
    <ResourceDocSlider
      v-model="isResourceDocSliderVisible"
      :resource="(editingResource as any)"
      :show-footer="false"
      :show-create-btn="false"
      :is-preview="!editingResource.id"
      :preview-lang="docConfig.language"
    />
    <!--  查看插件侧边栏  -->
    <ResourcePluginPreviewSlider
      :plugins="(editingResource.plugin_configs as any)"
      :is-slider-show="isPluginsSliderShow"
      @on-hidden="isPluginsSliderShow = false"
    />
  </div>
</template>

<script setup lang="ts">
import { AngleUpFill } from 'bkui-vue/lib/icon';
import type { ActionType, IAuthConfig, ILocalImportedResource, IPublicConfig } from '@/types/resource';
import ResourceDocSlider from '../../../components/ResourceDocSlider.vue';
import type { IImportDocConfig, IImportPreviewGroups } from '../types';
import ExcludedResourceTable from './ExcludedResourceTable.vue';
import PendingResourceTable from './PendingResourceTable.vue';
import ResourceEditSlider from './ResourceEditSlider.vue';
import ResourcePluginPreviewSlider from './ResourcePluginPreviewSlider.vue';

interface IProps {
  groups: IImportPreviewGroups
  docConfig: IImportDocConfig
  isAiGateway: boolean
}

const { groups, docConfig, isAiGateway } = defineProps<IProps>();

const emit = defineEmits<{
  'toggle-resource': [row: ILocalImportedResource]
  'restore-all': []
  'edit-resource': [row: ILocalImportedResource]
  'update-auth-config': [action: ActionType, config: IAuthConfig]
  'update-public-config': [action: ActionType, config: IPublicConfig]
  'update-doc-config': [config: IImportDocConfig]
}>();

const { t } = useI18n();
const panelNamesList = ref(['add', 'update', 'unchanged', 'uncheck']);
const isResourceDocSliderVisible = ref(false);
const editingResource = ref<ILocalImportedResource>({
  name: '',
  description: '',
  label_ids: [],
  labels: [],
  auth_config: {
    auth_verified_required: true,
    app_verified_required: true,
    resource_perm_required: true,
  },
  is_public: true,
  allow_apply_permission: true,
  _localId: -1,
  _unchecked: false,
});
const isSliderShow = ref(false);
const isPluginsSliderShow = ref(false);
const tempAuthConfig = ref({
  app_verified_required: false,
  auth_verified_required: false,
  resource_perm_required: false,
});
const tempPublicConfig = ref({
  is_public: false,
  allow_apply_permission: false,
});

const filterDraft = reactive({
  add: '',
  update: '',
});
const filterKeyword = reactive({
  add: '',
  update: '',
});

const resourceCount = computed(() => groups.add.length + groups.update.length + groups.unchanged.length
  + groups.excluded.length);

const filterResources = (resources: ILocalImportedResource[], keyword: string) =>
  resources.filter(({ name, path }) => name?.includes(keyword) || path?.includes(keyword));

const tableDataToAdd = computed(() => filterResources(groups.add, filterKeyword.add));
const tableDataToUpdate = computed(() => filterResources(groups.update, filterKeyword.update));

watchEffect(() => {
  if (filterDraft.add === '') {
    filterKeyword.add = '';
  }
  if (filterDraft.update === '') {
    filterKeyword.update = '';
  }
});

const handleEditSliderHidden = () => {
  isSliderShow.value = false;
};

const setEditingResource = (localId: number) => {
  const resource = Object.values(groups).flat().find(row => row._localId === localId);
  if (resource) {
    editingResource.value = {
      ...editingResource.value,
      ...resource,
    };
  }
};

const handleEdit = (resource: ILocalImportedResource) => {
  setEditingResource(resource._localId);
  isSliderShow.value = true;
};

const handleShowResourceDoc = (resource: ILocalImportedResource) => {
  setEditingResource(resource._localId);
  isResourceDocSliderVisible.value = true;
};

const handleShowPluginsSlider = (resource: ILocalImportedResource) => {
  if (!resource.plugin_configs?.length) {
    return;
  }
  setEditingResource(resource._localId);
  isPluginsSliderShow.value = true;
};

const handleConfirmAuthConfigPopConfirm = (action: ActionType) => {
  if (!tempAuthConfig.value.app_verified_required) {
    tempAuthConfig.value.resource_perm_required = false;
  }
  emit('update-auth-config', action, tempAuthConfig.value);
};

const handleConfirmPublicConfigPopConfirm = (action: ActionType) => {
  emit('update-public-config', action, tempPublicConfig.value);
};

const applyResourceFilter = (action: ActionType) => {
  filterKeyword[action] = filterDraft[action];
};

const clearFilterInput = (action: ActionType) => {
  filterDraft[action] = '';
};
</script>

<style scoped lang="scss">
.imported-resources-wrap {
  margin: 20px 24px 0;

  // min-height: 768px;

  .res-counter-banner {
    display: flex;
    height: 40px;
    padding: 0 24px 0 12px;
    margin-bottom: 16px;
    background: #FFF;
    border-radius: 2px;
    box-shadow: 0 2px 4px 0 #1919290d;
    justify-content: space-between;
    align-items: center;
  }

  .res-content-wrap {
    height: calc(100vh - 285px);
    overflow-y: scroll;

    &::-webkit-scrollbar {
      width: 4px;
      height: 4px;
    }

    &::-webkit-scrollbar-thumb {
      background: #ddd;
      border-radius: 20px;
      box-shadow: inset 0 0 6px #cccccc4d;
    }

    :deep(.collapse-cls) {
      margin-bottom: 24px;

      .bk-collapse-item {
        margin-bottom: 16px;
        background: #fff;
        box-shadow: 0 2px 4px 0 #1919290d;
      }

      // 折叠让 .panel-header 粘滞固定到顶部

      > .bk-collapse-item > :first-child {
        position: sticky;
        top: 0;
        z-index: 3;
        background-color: #fff;
      }

      // 吸顶标题会遮住表格原有上边框，在标题下沿补画同一条线。

      > .unchanged-resources-panel.bk-collapse-item-active > :first-child::after {
        position: absolute;
        right: 24px;
        bottom: -1px;
        left: 24px;
        height: 1px;
        pointer-events: none;
        background-color: #dcdee5;
        content: '';
      }
    }

    :deep(.bk-collapse-content) {
      // 将表格固定列和表头的层级限制在内容区内，避免遮挡分区吸顶标题。
      isolation: isolate;
      padding-top: 0 !important;
      padding-bottom: 0 !important;
    }

    .panel-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 19px 24px;
      cursor: pointer;

      .title {
        margin-left: 8px;
        font-size: 14px;
        font-weight: 700;
        color: #313238;
      }

      .panel-header-show {
        transform: rotate(0deg);
        transition: .2s;
      }

      .panel-header-hide {
        transform: rotate(-90deg);
        transition: .2s;
      }
    }
  }
}

:deep(.bk-collapse-header) {
  display: flex;
  align-items: center;
}

:deep(.bk-collapse-header .bk-collapse-title) {
  flex-grow: 1;
  display: inline-flex;
  align-items: center;
}

:deep(.bk-collapse-content) {
  padding-right: 24px;
  padding-left: 24px;
}

:deep(.multi-edit-popconfirm-wrap .auth-config) {
  font-size: 12px;
}
</style>
