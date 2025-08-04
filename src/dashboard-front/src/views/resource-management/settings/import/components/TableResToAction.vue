/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
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
  <BkTable
    :data="tableData"
    :pagination="pagination"
    row-key="name"
    show-overflow-tooltip
    v-bind="$attrs"
  >
    <BkTableColumn
      :label="t('资源名称')"
      :min-width="160"
      fixed="left"
      prop="name"
      width="160"
    />
    <!--  认证方式列  -->
    <BkTableColumn
      :label="() => renderAuthConfigColLabel()"
      :show-overflow-tooltip="false"
      width="100"
    >
      <template #default="{ row }: { row: ILocalImportedResource }">
        <span v-bk-tooltips="{ content: `${getAuthConfigText(row?.auth_config)}`, placement: 'top' }">
          {{ getAuthConfigText(row?.auth_config) }}
        </span>
      </template>
    </BkTableColumn>
    <BkTableColumn
      :label="t('校验应用权限')"
    >
      <template #default="{ row }: { row: ILocalImportedResource }">
        <span
          :class="{ 'color-#ffb400': getPermRequiredText(row?.auth_config) === '是' }"
        >{{ getPermRequiredText(row?.auth_config) }}</span>
      </template>
    </BkTableColumn>
    <!--  “是否公开”列  -->
    <BkTableColumn
      :label="() => renderIsPublicColLabel()"
      width="100"
    >
      <template #default="{ row }: { row: ILocalImportedResource }">
        <span :class="{ 'color-#ffb400': getPublicSettingText(row.is_public) === '是' }">
          {{ getPublicSettingText(row.is_public) }}
        </span>
      </template>
    </BkTableColumn>
    <BkTableColumn
      :label="t('允许申请权限')"
    >
      <template #default="{ row }: { row: ILocalImportedResource }">
        <span :class="{ 'color-#ffb400': getAllowApplyPermissionText(row.allow_apply_permission) === '是' }">
          {{ getAllowApplyPermissionText(row.allow_apply_permission) }}
        </span>
      </template>
    </BkTableColumn>
    <BkTableColumn
      :label="t('前端请求路径')"
      :min-width="160"
      :width="160"
    >
      <template #default="{ row }">
        <span>{{ row.match_subpath ? row.path_display : row.path }}</span>
      </template>
    </BkTableColumn>
    <BkTableColumn
      :label="t('前端请求方法')"
      :show-overflow-tooltip="false"
      prop="method"
    >
      <template #default="{ row }: { row: ILocalImportedResource }">
        <BkTag :theme="METHOD_THEMES[row.method ?? 'GET']">
          {{ row.method }}
        </BkTag>
      </template>
    </BkTableColumn>
    <BkTableColumn
      :label="t('后端服务')"
      prop="method"
    >
      <template #default="{ row }: { row: ILocalImportedResource }">
        {{ row.backend?.name ?? 'default' }}
      </template>
    </BkTableColumn>
    <BkTableColumn
      :label="t('后端请求方法')"
      :show-overflow-tooltip="false"
      prop="method"
    >
      <template #default="{ row }: { row: ILocalImportedResource }">
        <BkTag
          :theme="METHOD_THEMES[row.backend?.config.method ?? row?.method ?? 'GET']"
        >
          {{ row.backend?.config.method ?? row.method }}
        </BkTag>
      </template>
    </BkTableColumn>
    <BkTableColumn
      :label="t('后端请求路径')"
      :min-width="160"
      :width="160"
    >
      <template #default="{ row }: { row: ILocalImportedResource }">
        {{ row.backend?.config?.path ?? row.backend?.path ?? row.path }}
      </template>
    </BkTableColumn>
    <BkTableColumn
      :label="() => action === 'add' ? renderDocColLabel() : t('资源文档')"
    >
      <template #default="{ row }: { row: ILocalImportedResource }">
        <BkButton
          v-if="docConfig.showDoc"
          text
          theme="primary"
          @click="() => handleShowResourceDoc(row)"
        >
          <AgIcon
            name="doc-2"
            class="mr-4px color-#3A84FF"
          />{{ t('详情') }}
        </BkButton>
        <span v-else>{{ t('未生成') }}</span>
      </template>
    </BkTableColumn>
    <BkTableColumn
      :label="t('插件数量')"
      width="85"
    >
      <template #default="{ row }: { row: ILocalImportedResource }">
        <BkButton
          class="text-12px!"
          text
          theme="primary"
          @click="() => handleShowPluginsSlider(row)"
        >
          <span
            v-bk-tooltips="{ content: `${row.plugin_configs?.map((c)=>c.name || c.type).join('，') || '无插件'}` }"
          >
            {{ row.plugin_configs?.length ?? 0 }}
          </span>
        </BkButton>
      </template>
    </BkTableColumn>
    <BkTableColumn
      :label="t('操作')"
      fixed="right"
      prop="act"
      width="150"
    >
      <template #default="{ row }: { row: ILocalImportedResource }">
        <div class="flex gap-12px">
          <BkButton
            text
            theme="primary"
            @click="() => handleEdit(row)"
          >
            {{ t('修改配置') }}
          </BkButton>
          <BkButton
            class="px-10px"
            text
            theme="primary"
            @click="() => toggleRowUnchecked(row)"
          >
            {{ t('不导入') }}
          </BkButton>
        </div>
      </template>
    </BkTableColumn>
    <template #empty>
      <TableEmpty
        :keyword="keyword"
        @clear-filter="handleClearFilter"
      />
    </template>
  </BkTable>
</template>

<script lang="tsx" setup>
import {
  type ActionType,
  type IAuthConfig,
  type ILocalImportedResource,
  type IPublicConfig,
} from '@/types/resource';
import { METHOD_THEMES } from '@/enums';
import { useTextGetter } from '@/hooks';
import TableEmpty from '@/components/table-empty/Index.vue';
import { type IDocConfig } from '../Index.vue';

interface IProps {
  tableData?: ILocalImportedResource[]
  action?: ActionType
  keyword?: string
  docConfig?: IDocConfig
}

const tempAuthConfig = defineModel<IAuthConfig>('tempAuthConfig', { required: true });

const tempPublicConfig = defineModel<IPublicConfig>('tempPublicConfig', { required: true });

const {
  tableData = [],
  action = 'add',
  keyword = '',
  docConfig = {
    showDoc: true,
    language: 'zh',
  },
} = defineProps<IProps>();

const emit = defineEmits<{
  'show-row-doc': [row: ILocalImportedResource]
  'show-row-plugin': [row: ILocalImportedResource]
  'show-row-edit': [row: ILocalImportedResource]
  'toggle-row-unchecked': [row: ILocalImportedResource]
  'confirm-auth-config': [action: ActionType]
  'confirm-pub-config': [action: ActionType]
  'confirm-doc-config': [docConfig: IDocConfig]
  'clear-filter': [action: ActionType]
}>();

const {
  getAuthConfigText,
  getPermRequiredText,
  getPublicSettingText,
  getAllowApplyPermissionText,
} = useTextGetter();

const { t } = useI18n();

const pagination = ref({
  count: tableData.length,
  limit: 10,
});

const localDocConfig = ref({ ...docConfig });

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
  emit('confirm-auth-config', action);
};

// 批量修改认证方式取消后
const handleCancelAuthConfig = () => {
  tempAuthConfig.value = {
    app_verified_required: false,
    auth_verified_required: false,
    resource_perm_required: false,
  };
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

const handleConfirmDocConfig = () => {
  emit('confirm-doc-config', localDocConfig.value);
};

const renderAuthConfigColLabel = () => {
  return (
    <div>
      <div class="auth-config-col-label">
        <span>{t('认证方式')}</span>
        <BkPopConfirm
          width="430"
          trigger="click"
          title={<span style="font-size: 16px;color: #313238;">{t('批量修改认证方式')}</span>}
          content={(
            <div class="multi-edit-popconfirm-wrap auth-config" style="margin-bottom: -12px;">
              <BkForm model={tempAuthConfig.value} labelWidth="110" labelPosition="right">
                <BkFormItem label={t('认证方式')} required={true} style="margin-bottom: 12px;">
                  <BkCheckbox
                    v-model={tempAuthConfig.value.app_verified_required}
                  >
                    <span class="bottom-line" v-bk-tooltips={{ content: t('请求方需提供蓝鲸应用身份信息') }}>
                      {t('蓝鲸应用认证')}
                    </span>
                  </BkCheckbox>
                  <BkCheckbox class="ml-40px" v-model={tempAuthConfig.value.auth_verified_required}>
                    <span class="bottom-line" v-bk-tooltips={{ content: t('请求方需提供蓝鲸用户身份信息') }}>
                      {t('用户认证')}
                    </span>
                  </BkCheckbox>
                </BkFormItem>
                {tempAuthConfig.value.app_verified_required
                  ? (
                    <BkFormItem
                      label={t('检验应用权限')}
                      description={t('蓝鲸应用需申请资源访问权限')}
                      style="margin-bottom: 12px;"
                    >
                      <BkSwitcher
                        v-model={tempAuthConfig.value.resource_perm_required}
                        theme="primary"
                        size="small"
                      />
                    </BkFormItem>
                  )
                  : ''}
              </BkForm>
            </div>
          )}
          onConfirm={() => handleConfirmAuthConfig()}
          onCancel={() => handleCancelAuthConfig()}
        >
          <AgIcon
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
        </BkPopConfirm>
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
        <BkPopConfirm
          width="360"
          trigger="click"
          title={<span class="text-16px color-#313238">{t('批量修改公开设置')}</span>}
          content={(
            <div class="multi-edit-popconfirm-wrap public-config" style="margin-bottom: -12px;">
              <BkForm model={tempPublicConfig.value} labelWidth="100" labelPosition="right">
                <BkFormItem
                  label={t('是否公开')}
                  required={true}
                  description={t('公开，则用户可查看资源文档、申请资源权限；不公开，则资源对用户隐藏')}
                  style="margin-bottom: 12px;"
                >
                  <BkSwitcher
                    v-model={tempPublicConfig.value.is_public}
                    theme="primary"
                    size="small"
                  />
                </BkFormItem>
                {tempPublicConfig.value.is_public
                  ? (
                    <BkFormItem style="margin-bottom: 12px;">
                      <BkCheckbox
                        v-model={tempPublicConfig.value.allow_apply_permission}
                      >
                        <span class="bottom-line">
                          {t('允许申请权限')}
                        </span>
                      </BkCheckbox>
                    </BkFormItem>
                  )
                  : ''}
              </BkForm>
            </div>
          )}
          onConfirm={() => handleConfirmPublicConfig()}
          onCancel={() => handleCancelPublicConfig()}
        >
          <AgIcon
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
        </BkPopConfirm>
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
        <BkPopConfirm
          width="360"
          trigger="click"
          title={<span class="text-16px color-#313238">{t('批量修改资源文档')}</span>}
          content={(
            <div class="multi-edit-popconfirm-wrap public-config" style="margin-bottom: -12px;">
              <BkForm model={localDocConfig.value} labelWidth="100" labelPosition="right">
                <BkFormItem
                  label={t('生成文档')}
                  style="margin-bottom: 12px;"
                >
                  <BkSwitcher
                    v-model={localDocConfig.value.showDoc}
                    theme="primary"
                    size="small"
                  />
                </BkFormItem>
                {localDocConfig.value.showDoc
                  ? (
                    <BkFormItem
                      label={t('文档语言')}
                      style="margin-bottom: 12px;"
                    >
                      <BkRadioGroup v-model={localDocConfig.value.language} size="small">
                        <BkRadio label="zh">{t('中文文档')}</BkRadio>
                        <BkRadio label="en">{t('英文文档')}</BkRadio>
                      </BkRadioGroup>
                    </BkFormItem>
                  )
                  : ''}
              </BkForm>
            </div>
          )}
          onConfirm={() => handleConfirmDocConfig()}
        >
          <AgIcon
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
        </BkPopConfirm>
      </div>
    </div>
  );
};
</script>
