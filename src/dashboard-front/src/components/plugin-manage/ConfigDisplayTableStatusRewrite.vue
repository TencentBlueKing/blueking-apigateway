<template>
  <!--  插件配置展示态组件  -->
  <!--  网关错误使用HTTP状态码200插件  -->
  <BkTable
    :data="tableData"
    :columns="tableCols"
    v-bind="$attrs"
  />
</template>

<script setup lang="ts">
import type {
  IColumn,
  IPlugin,
  ValueRenderType,
} from '@/components/plugin-manage/types';

interface IGenericConfig { [key: string]: unknown }

interface IProps {
  plugin: IPlugin<IGenericConfig>
  firstColWidth: string
  valueRender: ValueRenderType
}

const {
  firstColWidth,
  valueRender,
} = defineProps<IProps>();

const { t } = useI18n();

// 通用表格列
const tableCols = ref<IColumn[]>([
  {
    label: t('键'),
    align: 'right',
    field: 'key',
    width: firstColWidth,
    index: 0,
    rowspan: ({ row }) => row.rowSpan || 1,
  },
  {
    label: t('值'),
    field: 'value',
    render: valueRender,
  },
]);

// 通用表格数据
const tableData = ref([
  {
    id: 1,
    key: t('已开启'),
    value: t('是'),
  },
]);

</script>

<style lang="scss" scoped>
:deep(.multi-line-table-cell-pre) {
  font: inherit;
  line-height: 1.4 !important;
  color: inherit;
}
</style>
