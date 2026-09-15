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
    :columns="columns as PrimaryTableProps['columns']"
    table-row-key="name"
    local-page
    :resizable="false"
    v-bind="$attrs"
  />
</template>

<script setup lang="tsx">
import { type ILocalImportedResource } from '@/types/resource';
import type { PrimaryTableProps } from '@blueking/tdesign-ui';
import AgTable from '@/components/ag-table/Index.vue';
import { RESOURCE_TYPE_LIST } from '@/constants';
import { METHOD_THEMES } from '@/enums';
import { useTextGetter } from '@/hooks';

interface IProps {
  tableData?: ILocalImportedResource[]
  showDoc?: boolean
  isAiGateway?: boolean
}

const {
  tableData = [],
  showDoc = true,
  isAiGateway = false,
} = defineProps<IProps>();

const emit = defineEmits<{
  'show-row-doc': [row: ILocalImportedResource]
  'show-row-plugin': [row: ILocalImportedResource]
  'toggle-row-unchecked': [row: ILocalImportedResource]
}>();

const {
  getAuthConfigText,
  getPermRequiredText,
  getPublicSettingText,
  getAllowApplyPermissionText,
} = useTextGetter();

const { t } = useI18n();

const tableRef = useTemplateRef('tableRef');

const columns = computed<PrimaryTableProps<ILocalImportedResource>['columns']>(() => [
  {
    title: t('资源名称'),
    colKey: 'name',
    fixed: 'left',
    width: 160,
    minWidth: 160,
    ellipsis: true,
  },
  ...(isAiGateway
    ? [{
      title: t('资源类型'),
      colKey: 'kind',
      minWidth: 100,
      ellipsis: true,
      cell: (h: unknown, { row }: { row: ILocalImportedResource }) => (
        <bk-tag theme={getResourceTypeData(row.kind)?.theme ?? 'default'}>
          {getResourceTypeData(row.kind)?.label ?? t('普通 API')}
        </bk-tag>
      ),
    }]
    : []),
  {
    title: t('认证方式'),
    colKey: 'auth_config',
    ellipsis: true,
    cell: (h: unknown, { row }: { row: ILocalImportedResource }) => (
      <span
        v-bk-tooltips={{
          content: `${getAuthConfigText(row?.auth_config)}`,
          placement: 'top',
        }}
      >
        {getAuthConfigText(row?.auth_config)}
      </span>
    ),
  },
  {
    title: t('校验应用权限'),
    colKey: 'resource_perm_required',
    ellipsis: true,
    cell: (h: unknown, { row }: { row: ILocalImportedResource }) => (
      <span class={{ 'color-#ffb400': getPermRequiredText(row?.auth_config) === t('是') }}>
        {getPermRequiredText(row?.auth_config)}
      </span>
    ),
  },
  {
    title: t('是否公开'),
    colKey: 'is_public',
    ellipsis: true,
    cell: (h: unknown, { row }: { row: ILocalImportedResource }) => (
      <span class={{ 'color-#ffb400': getPublicSettingText(row.is_public) === t('是') }}>
        {getPublicSettingText(row.is_public)}
      </span>
    ),
  },
  {
    title: t('允许申请权限'),
    colKey: 'allow_apply_permission',
    ellipsis: true,
    cell: (h: unknown, { row }: { row: ILocalImportedResource }) => (
      <span class={{ 'color-#ffb400': getAllowApplyPermissionText(row.allow_apply_permission) === t('是') }}>
        {getAllowApplyPermissionText(row.allow_apply_permission)}
      </span>
    ),
  },
  {
    title: t('前端请求路径'),
    colKey: 'path',
    minWidth: 160,
    ellipsis: true,
    cell: (h: unknown, { row }: { row: ILocalImportedResource & { path_display?: string } }) => (
      <span>{row.match_subpath ? row.path_display : row.path}</span>
    ),
  },
  {
    title: t('前端请求方法'),
    colKey: 'method',
    cell: (h: unknown, { row }: { row: ILocalImportedResource }) => (
      <bk-tag theme={(METHOD_THEMES as any)[row.method!]}>
        {row.method}
      </bk-tag>
    ),
  },
  {
    title: isAiGateway ? t('后端/模型服务') : t('后端服务'),
    colKey: 'backend',
    ellipsis: true,
    cell: (h: unknown, { row }: { row: ILocalImportedResource }) => row.backend?.name ?? 'default',
  },
  ...(!isAiGateway
    ? [
      {
        title: t('后端请求方法'),
        colKey: 'backend_method',
        cell: (h: unknown, { row }: { row: ILocalImportedResource }) => (
          <bk-tag theme={(METHOD_THEMES as any)[(row.backend?.config.method ?? row.method)!]}>
            {row.backend?.config.method ?? row.method}
          </bk-tag>
        ),
      },
      {
        title: t('后端请求路径'),
        colKey: 'backend_path',
        minWidth: 160,
        ellipsis: true,
        cell: (h: unknown, { row }: { row: ILocalImportedResource }) => (
          row.backend?.config?.path ?? row.backend?.path ?? row.path
        ),
      },
    ]
    : []),
  {
    title: t('资源文档'),
    colKey: 'doc',
    ellipsis: true,
    cell: (h: unknown, { row }: { row: ILocalImportedResource }) => (
      showDoc
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
    cell: (h: unknown, { row }: { row: ILocalImportedResource }) => (
      <bk-button theme="primary" text class="text-12px!" onClick={() => handleShowPluginsSlider(row)}>
        <span v-bk-tooltips={{ content: `${row.plugin_configs?.map(c => c.name || c.type).join('，') || t('无插件')}` }}>
          {row.plugin_configs?.length ?? 0}
        </span>
      </bk-button>
    ),
  },
  {
    title: t('操作'),
    colKey: 'act',
    fixed: 'right',
    width: 100,
    ellipsis: true,
    cell: (h: unknown, { row }: { row: ILocalImportedResource }) => (
      <bk-button text theme="primary" onClick={() => toggleRowUnchecked(row)}>
        {t('恢复导入')}
      </bk-button>
    ),
  },
]);

// 恢复导入后，保持原表格在页码越界时回到第一页的行为。
watch(() => tableData.length, (count) => {
  const { current = 1, pageSize = 10 } = tableRef.value?.getPagination() ?? {};
  if (current > Math.max(Math.ceil(count / pageSize), 1)) {
    tableRef.value?.setPagination({
      current: 1,
      pageSize,
    });
  }
});

const getResourceTypeData = (kind?: ILocalImportedResource['kind']) => {
  return RESOURCE_TYPE_LIST.find(item => item.value === kind);
};

const handleShowResourceDoc = (row: ILocalImportedResource) => {
  emit('show-row-doc', row);
};

const handleShowPluginsSlider = (row: ILocalImportedResource) => {
  emit('show-row-plugin', row);
};

const toggleRowUnchecked = (row: ILocalImportedResource) => {
  emit('toggle-row-unchecked', row);
};

</script>
