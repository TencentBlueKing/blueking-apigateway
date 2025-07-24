<template>
  <BkTable
    :data="tableData"
    row-key="name"
    show-overflow-tooltip
    :pagination="pagination"
    v-bind="$attrs"
  >
    <BkTableColumn
      :label="t('资源名称')"
      prop="name"
      :min-width="160"
      width="160"
      fixed="left"
    />
    <BkTableColumn
      :label="t('认证方式')"
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
    <BkTableColumn
      :label="t('是否公开')"
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
    >
      <template #default="{ row }">
        <span>{{ row.match_subpath ? row.path_display : row.path }}</span>
      </template>
    </BkTableColumn>
    <BkTableColumn
      :label="t('前端请求方法')"
      prop="method"
      :show-overflow-tooltip="false"
    >
      <template #default="{ row }: { row: ILocalImportedResource }">
        <BkTag :theme="METHOD_THEMES[row.method]">
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
      prop="method"
      :show-overflow-tooltip="false"
    >
      <template #default="{ row }: { row: ILocalImportedResource }">
        <BkTag
          :theme="METHOD_THEMES[row.backend?.config.method ?? row.method]"
        >
          {{ row.backend?.config.method ?? row.method }}
        </BkTag>
      </template>
    </BkTableColumn>
    <BkTableColumn
      :label="t('后端请求路径')"
      :min-width="160"
    >
      <template #default="{ row }: { row: ILocalImportedResource }">
        {{ row.backend?.config?.path ?? row.backend?.path ?? row.path }}
      </template>
    </BkTableColumn>
    <BkTableColumn
      :label="t('资源文档')"
      prop="doc"
    >
      <template #default="{ row }: { row: ILocalImportedResource }">
        <BkButton
          v-if="showDoc"
          text
          theme="primary"
          @click="() => handleShowResourceDoc(row)"
        >
          <AgIcon
            name="doc-2"
            class="mr-4px color-#3A84FF"
          />
          {{ t('详情') }}
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
          theme="primary"
          text
          class="text-12px!"
          @click="() => handleShowPluginsSlider(row)"
        >
          <span
            v-bk-tooltips="{ content: `${row.plugin_configs?.map((c) => c.name || c.type).join('，') || '无插件'}` }"
          >
            {{ row.plugin_configs?.length ?? 0 }}
          </span>
        </BkButton>
      </template>
    </BkTableColumn>
    <BkTableColumn
      :label="t('操作')"
      width="100"
      fixed="right"
      prop="act"
    >
      <template #default="{ row }: { row: ILocalImportedResource }">
        <BkButton
          text
          theme="primary"
          @click="() => toggleRowUnchecked(row)"
        >
          {{ t('恢复导入') }}
        </BkButton>
      </template>
    </BkTableColumn>
  </BkTable>
</template>

<script setup lang="tsx">
import { type ILocalImportedResource } from '@/types/resource';
import { METHOD_THEMES } from '@/enums';
import { useTextGetter } from '@/hooks';

interface IProps {
  tableData?: ILocalImportedResource[]
  showDoc?: boolean
}

const {
  tableData = [],
  showDoc = true,
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

const pagination = ref({
  count: tableData.length,
  limit: 10,
});

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
