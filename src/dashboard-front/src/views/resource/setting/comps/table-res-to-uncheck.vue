<template>
  <bk-table
    :data="tableData"
    row-key="name"
    show-overflow-tooltip
    :pagination="pagination"
    v-bind="$attrs"
  >
    <bk-table-column
      :label="t('资源名称')"
      prop="name"
      :min-width="160"
      width="160"
      fixed="left"
    >
    </bk-table-column>
    <bk-table-column
      :label="t('认证方式')"
    >
      <template #default="{ row }: { row: ILocalImportedResource }">
        <span v-bk-tooltips="{ content: `${getAuthConfigText(row?.auth_config)}`, placement: 'top' }">
          {{ getAuthConfigText(row?.auth_config) }}
        </span>
      </template>
    </bk-table-column>
    <bk-table-column
      :label="t('校验应用权限')"
    >
      <template #default="{ row }: { row: ILocalImportedResource }">
        <span
          :class="{ 'warning-c': getPermRequiredText(row?.auth_config) === '是' }"
        >{{ getPermRequiredText(row?.auth_config) }}</span>
      </template>
    </bk-table-column>
    <bk-table-column
      :label="t('是否公开')"
    >
      <template #default="{ row }: { row: ILocalImportedResource }">
        <span :class="{ 'warning-c': getPublicSettingText(row.is_public) === '是' }">
          {{ getPublicSettingText(row.is_public) }}
        </span>
      </template>
    </bk-table-column>
    <bk-table-column
      :label="t('允许申请权限')"
    >
      <template #default="{ row }: { row: ILocalImportedResource }">
        <span :class="{ 'warning-c': getAllowApplyPermissionText(row.allow_apply_permission) === '是' }">
          {{ getAllowApplyPermissionText(row.allow_apply_permission) }}
        </span>
      </template>
    </bk-table-column>
    <bk-table-column
      :label="t('前端请求路径')"
      :min-width="160"
    >
      <template #default="{ row }">
        <span>{{ row.match_subpath ? row.path_display : row.path }}</span>
      </template>
    </bk-table-column>
    <bk-table-column
      :label="t('前端请求方法')"
      prop="method"
      :show-overflow-tooltip="false"
    >
      <template #default="{ row }: { row: ILocalImportedResource }">
        <bk-tag :theme="methodsEnum[row.method]">{{ row.method }}</bk-tag>
      </template>
    </bk-table-column>
    <bk-table-column
      :label="t('后端服务')"
      prop="method"
    >
      <template #default="{ row }: { row: ILocalImportedResource }">
        {{ row.backend?.name ?? 'default' }}
      </template>
    </bk-table-column>
    <bk-table-column
      :label="t('后端请求方法')"
      prop="method"
      :show-overflow-tooltip="false"
    >
      <template #default="{ row }: { row: ILocalImportedResource }">
        <bk-tag
          :theme="methodsEnum[row.backend?.config.method ?? row.method]"
        >
          {{ row.backend?.config.method ?? row.method }}
        </bk-tag>
      </template>
    </bk-table-column>
    <bk-table-column
      :label="t('后端请求路径')"
      :min-width="160"
    >
      <template #default="{ row }: { row: ILocalImportedResource }">
        {{ row.backend?.config?.path ?? row.backend?.path ?? row.path }}
      </template>
    </bk-table-column>
    <bk-table-column
      :label="t('资源文档')"
      prop="doc"
    >
      <template #default="{ row }: { row: ILocalImportedResource }">
        <bk-button
          v-if="showDoc"
          text
          theme="primary"
          @click="handleShowResourceDoc(row)"
        >
          <i class="apigateway-icon icon-ag-doc-2 mr4 f14 default-c" />
          {{ t('详情') }}
        </bk-button>
        <span v-else>{{ t('未生成') }}</span>
      </template>
    </bk-table-column>
    <bk-table-column
      :label="t('插件数量')"
      width="85"
    >
      <template #default="{ row }: { row: ILocalImportedResource }">
        <bk-button
          theme="primary"
          text style="font-size: 12px;"
          @click="handleShowPluginsSlider(row)"
        >
          <span
            v-bk-tooltips="{ content: `${row.plugin_configs?.map((c) => c.name || c.type).join('，') || '无插件'}` }"
          >
            {{ row.plugin_configs?.length ?? 0 }}
          </span>
        </bk-button>
      </template>
    </bk-table-column>
    <bk-table-column
      :label="t('操作')"
      width="100"
      fixed="right"
      prop="act"
    >
      <template #default="{ row }: { row: ILocalImportedResource }">
        <bk-button
          text
          theme="primary"
          @click="() => {
            toggleRowUnchecked(row)
          }"
        >
          {{ t('恢复导入') }}
        </bk-button>
      </template>
    </bk-table-column>
  </bk-table>
</template>

<script setup lang="tsx">
import { ILocalImportedResource } from '@/views/resource/setting/types';
import { ref, toRefs } from 'vue';
import { useI18n } from 'vue-i18n';
import { MethodsEnum } from '@/types';
import useTextGetter from '@/views/resource/setting/hooks/useTextGetter';

const {
  getAuthConfigText,
  getPermRequiredText,
  getPublicSettingText,
  getAllowApplyPermissionText,
} = useTextGetter();

const { t } = useI18n();
const methodsEnum = Object.freeze(MethodsEnum);

interface IProps {
  tableData: ILocalImportedResource[];
  showDoc: boolean;
}

const props = withDefaults(defineProps<IProps>(), {
  tableData: () => [],
  showDoc: true,
});

const emit = defineEmits<{
  'show-row-doc': [row: ILocalImportedResource]
  'show-row-plugin': [row: ILocalImportedResource]
  'toggle-row-unchecked': [row: ILocalImportedResource]
}>();

const {
  tableData,
  showDoc,
} = toRefs(props);

const pagination = ref({
  count: tableData.value.length,
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

<style scoped lang="scss">

</style>
