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
  <AgTable
    ref="tableRef"
    :table-data="tableData"
    :columns="columns"
    table-row-key="name"
    local-page
    :auto-height="false"
    :resizable="false"
    v-bind="$attrs"
  >
    <template #empty>
      <AgTableEmpty
        :empty-type="keyword ? 'search-empty' : 'empty'"
        @clear-filter="handleClearFilter"
      />
    </template>
  </AgTable>
</template>

<script lang="tsx" setup>
import {
  type ActionType,
  type ILocalImportedResource,
  type IPublicConfig,
  type IResourceAuthFormConfig,
} from '@/types/resource';
import AgTable, { type IAgTableInstance, type ITableColumn } from '@/components/base/ag-table';
import { useTextGetter } from '@/hooks';
import { useGateway } from '@/stores';
import { DEFAULT_AUTH_CONFIG, applyAuthKind } from '@/utils/auth-config';
import ResourceAuthSelector from '@/views/resource-management/components/ResourceAuthSelector.vue';
import LegacyResourceAuthSelector from '@/views/resource-management/components/LegacyResourceAuthSelector.vue';
import { useResourcePreviewColumns } from '../use-resource-preview-columns';
import AgTableEmpty from '@/components/base/ag-table-empty/Index.vue';
import type { IImportDocConfig } from '../types';

interface IProps {
  tableData?: ILocalImportedResource[]
  action?: ActionType
  keyword?: string
  docConfig?: IImportDocConfig
  isAiGateway?: boolean
}

const tempPublicConfig = defineModel<IPublicConfig>('tempPublicConfig', { required: true });

const {
  tableData = [],
  action = 'add',
  keyword = '',
  docConfig = {
    showDoc: true,
    language: 'zh',
  },
  isAiGateway = false,
} = defineProps<IProps>();

const emit = defineEmits<{
  'show-row-doc': [row: ILocalImportedResource]
  'show-row-plugin': [row: ILocalImportedResource]
  'show-row-edit': [row: ILocalImportedResource]
  'toggle-row-unchecked': [row: ILocalImportedResource]
  'confirm-auth-config': [action: ActionType, config: IResourceAuthFormConfig]
  'confirm-pub-config': [action: ActionType]
  'confirm-doc-config': [docConfig: IImportDocConfig]
  'clear-filter': [action: ActionType]
}>();

const {
  getAuthConfigText,
  getPermRequiredText,
  getPublicSettingText,
  getAllowApplyPermissionText,
} = useTextGetter();

const { t } = useI18n();
const gatewayStore = useGateway();
const allowNoAuth = computed(() => !!gatewayStore.currentGateway?.allow_update_gateway_auth);

const defaultBulkAuthConfig = () => gatewayStore.isResourceAuthV2
  ? { ...DEFAULT_AUTH_CONFIG }
  : applyAuthKind(DEFAULT_AUTH_CONFIG, '');
const tempAuthConfig = ref(defaultBulkAuthConfig());
const localDocConfig = ref({ ...docConfig });

const tableRef = useTemplateRef<IAgTableInstance<ILocalImportedResource>>('tableRef');

const sharedColumns = useResourcePreviewColumns(() => isAiGateway, 160);

const columns = computed<ITableColumn<ILocalImportedResource>[]>(() => [
  ...sharedColumns.value.identity,
  {
    title: () => renderAuthConfigColLabel(),
    colKey: 'auth_config',
    width: 100,
    cell: (_h, { row }) => (
      <span v-bk-tooltips={{ content: `${getAuthConfigText(row?.auth_config)}`,
        placement: 'top' }}
      >
        {getAuthConfigText(row?.auth_config)}
      </span>
    ),
  },
  {
    title: t('校验应用权限'),
    colKey: 'resource_perm_required',
    ellipsis: true,
    cell: (_h, { row }) => (
      <span class={{ 'color-#ffb400': getPermRequiredText(row?.auth_config) === t('是') }}>
        {getPermRequiredText(row?.auth_config)}
      </span>
    ),
  },
  {
    title: () => renderIsPublicColLabel(),
    colKey: 'is_public',
    width: 100,
    ellipsis: true,
    cell: (_h, { row }) => (
      <span class={{ 'color-#ffb400': getPublicSettingText(row.is_public) === t('是') }}>
        {getPublicSettingText(row.is_public)}
      </span>
    ),
  },
  {
    title: t('允许申请权限'),
    colKey: 'allow_apply_permission',
    ellipsis: true,
    cell: (_h, { row }) => (
      <span class={{ 'color-#ffb400': getAllowApplyPermissionText(row.allow_apply_permission) === t('是') }}>
        {getAllowApplyPermissionText(row.allow_apply_permission)}
      </span>
    ),
  },
  ...sharedColumns.value.requestAndBackend,
  {
    title: () => action === 'add' ? renderDocColLabel() : t('资源文档'),
    colKey: 'doc',
    ellipsis: true,
    cell: (_h, { row }) => (
      docConfig.showDoc
        ? (
          <bk-button text theme="primary" onClick={() => handleShowResourceDoc(row)}>
            <ag-icon name="doc-2" class="mr-4px color-#3A84FF" />
            {t('详情')}
          </bk-button>
        )
        : <span>{t('未生成')}</span>
    ),
  },
  {
    title: t('插件数量'),
    colKey: 'plugin_configs',
    width: 85,
    ellipsis: true,
    cell: (_h, { row }) => (
      <bk-button class="text-12px!" text theme="primary" onClick={() => handleShowPluginsSlider(row)}>
        <span v-bk-tooltips={{ content: `${row.plugin_configs?.map(c => c.name || c.type).join('，') || '无插件'}` }}>
          {row.plugin_configs?.length ?? 0}
        </span>
      </bk-button>
    ),
  },
  {
    title: t('操作'),
    colKey: 'act',
    fixed: 'right',
    width: 150,
    cell: (_h, { row }) => (
      <div class="flex gap-12px">
        <bk-button text theme="primary" onClick={() => handleEdit(row)}>
          {t('修改配置')}
        </bk-button>
        <bk-button class="px-10px" text theme="primary" onClick={() => toggleRowUnchecked(row)}>
          {t('不导入')}
        </bk-button>
      </div>
    ),
  },
]);

// 筛选或取消导入后，保持原表格在页码越界时回到第一页的行为。
watch(() => tableData.length, (count) => {
  const { current = 1, pageSize = 10 } = tableRef.value?.getPagination() ?? {};
  if (current > Math.max(Math.ceil(count / pageSize), 1)) {
    tableRef.value?.setPagination({
      current: 1,
      pageSize,
    });
  }
});

const handleShowResourceDoc = (row: ILocalImportedResource) => {
  emit('show-row-doc', row);
};

const handleShowPluginsSlider = (row: ILocalImportedResource) => {
  emit('show-row-plugin', row);
};

const handleEdit = (row: ILocalImportedResource) => {
  emit('show-row-edit', row);
};

const toggleRowUnchecked = (row: ILocalImportedResource) => {
  emit('toggle-row-unchecked', row);
};

// 批量修改认证方式确认后
const handleConfirmAuthConfig = () => {
  emit('confirm-auth-config', action, tempAuthConfig.value);
};

// 批量修改认证方式取消后
const handleCancelAuthConfig = () => {
  tempAuthConfig.value = defaultBulkAuthConfig();
};

// 点击清空搜索条件后
const handleClearFilter = () => {
  emit('clear-filter', action);
};

// 批量修改公开设置确认后
const handleConfirmPublicConfig = () => {
  emit('confirm-pub-config', action);
};

// 批量修改公开设置取消后
const handleCancelPublicConfig = () => {
  tempPublicConfig.value = {
    is_public: false,
    allow_apply_permission: false,
  };
};

const resetDocConfigDraft = () => {
  // 预览缓存会保留表格实例，每次打开弹层都从当前配置重新取值。
  localDocConfig.value = { ...docConfig };
};

const handleConfirmDocConfig = () => {
  emit('confirm-doc-config', localDocConfig.value);
};

const renderAuthConfigColLabel = () => {
  const AuthSelector = gatewayStore.isResourceAuthV2 ? ResourceAuthSelector : LegacyResourceAuthSelector;
  return (
    <div>
      <div class="auth-config-col-label">
        <span>{t('认证方式')}</span>
        <bk-pop-confirm
          width={gatewayStore.isResourceAuthV2 ? 620 : 430}
          trigger="click"
          title={<span style="font-size: 16px;color: #313238;">{t('批量修改认证方式')}</span>}
          content={(
            <div class="multi-edit-popconfirm-wrap" style="margin-bottom: -12px;">
              <AuthSelector
                {...{
                  'authConfig': tempAuthConfig.value,
                  'onUpdate:authConfig': (value: IResourceAuthFormConfig) => {
                    tempAuthConfig.value = value;
                  },
                }}
                {...(gatewayStore.isResourceAuthV2 && { allowNoAuth: allowNoAuth.value })}
                compact
              />
            </div>
          )}
          onConfirm={() => handleConfirmAuthConfig()}
          onCancel={() => handleCancelAuthConfig()}
        >
          <ag-icon
            name="bulk-edit"
            class="edit-action ml-5px color-#3A84FF"
            v-bk-tooltips={{
              content: (
                <div>
                  {t('批量修改认证方式')}
                </div>
              ),
            }}
          />
        </bk-pop-confirm>
      </div>
    </div>
  );
};

// 公开设置列 TSX
const renderIsPublicColLabel = () => {
  return (
    <div>
      <div class="public-config-col-label">
        <span>{t('是否公开')}</span>
        <bk-pop-confirm
          width="360"
          trigger="click"
          title={<span class="text-16px color-#313238">{t('批量修改公开设置')}</span>}
          content={(
            <div class="multi-edit-popconfirm-wrap public-config" style="margin-bottom: -12px;">
              <bk-form model={tempPublicConfig.value} labelWidth="100" labelPosition="right">
                <bk-form-item
                  label={t('是否公开')}
                  required={true}
                  description={t('公开，则用户可查看资源文档、申请资源权限；不公开，则资源对用户隐藏')}
                  style="margin-bottom: 12px;"
                >
                  <bk-switcher
                    v-model={tempPublicConfig.value.is_public}
                    theme="primary"
                    size="small"
                  />
                </bk-form-item>
                {tempPublicConfig.value.is_public
                  ? (
                    <bk-form-item style="margin-bottom: 12px;">
                      <bk-checkbox
                        v-model={tempPublicConfig.value.allow_apply_permission}
                      >
                        <span class="bottom-line">
                          {t('允许申请权限')}
                        </span>
                      </bk-checkbox>
                    </bk-form-item>
                  )
                  : ''}
              </bk-form>
            </div>
          )}
          onConfirm={() => handleConfirmPublicConfig()}
          onCancel={() => handleCancelPublicConfig()}
        >
          <ag-icon
            name="bulk-edit"
            class="edit-action ml-5px color-#3A84FF"
            v-bk-tooltips={{
              content: (
                <div>
                  {t('批量修改公开设置')}
                </div>
              ),
            }}
          />
        </bk-pop-confirm>
      </div>
    </div>
  );
};

// 是否生成文档列 TSX
const renderDocColLabel = () => {
  return (
    <div>
      <div class="public-config-col-label">
        <span>{t('资源文档')}</span>
        <bk-pop-confirm
          width="360"
          trigger="click"
          title={<span class="text-16px color-#313238">{t('批量修改资源文档')}</span>}
          content={(
            <div class="multi-edit-popconfirm-wrap public-config" style="margin-bottom: -12px;">
              <bk-form model={localDocConfig.value} labelWidth="100" labelPosition="right">
                <bk-form-item
                  label={t('生成文档')}
                  style="margin-bottom: 12px;"
                >
                  <bk-switcher
                    v-model={localDocConfig.value.showDoc}
                    theme="primary"
                    size="small"
                  />
                </bk-form-item>
                {localDocConfig.value.showDoc
                  ? (
                    <bk-form-item
                      label={t('文档语言')}
                      style="margin-bottom: 12px;"
                    >
                      <bk-radio-group v-model={localDocConfig.value.language} size="small">
                        <bk-radio label="zh">{t('中文文档')}</bk-radio>
                        <bk-radio label="en">{t('英文文档')}</bk-radio>
                      </bk-radio-group>
                    </bk-form-item>
                  )
                  : ''}
              </bk-form>
            </div>
          )}
          onAfterShow={resetDocConfigDraft}
          onConfirm={() => handleConfirmDocConfig()}
        >
          <ag-icon
            name="bulk-edit"
            class="edit-action ml-5px color-#3A84FF"
            v-bk-tooltips={{
              content: (
                <div>
                  {t('批量修改资源文档')}
                </div>
              ),
            }}
          />
        </bk-pop-confirm>
      </div>
    </div>
  );
};
</script>
