<template>
  <!--  插件配置展示态组件  -->
  <!--  网关错误使用HTTP状态码200插件  -->
  <bk-table
    :data="tableData"
    :columns="tableCols"
    v-bind="$attrs"
  />
</template>

<script setup lang="ts">
import {
  ref,
  toRefs,
} from 'vue';
import {
  IColumn,
  IPlugin,
  ValueRenderType,
} from '@/views/components/plugin-manage/types';
import { useI18n } from 'vue-i18n';

interface IGenericConfig {
  [key: string]: unknown
}

interface IProps {
  plugin: IPlugin<IGenericConfig>
  firstColWidth: string
  valueRender: ValueRenderType
}

const { t } = useI18n();

const props = defineProps<IProps>();

const { firstColWidth } = toRefs(props);

// 通用表格列
const tableCols = ref<IColumn[]>([
  {
    label: t('键'),
    align: 'right',
    field: 'key',
    width: firstColWidth.value,
    index: 0,
    rowspan: ({ row }) => row.rowSpan,
  },
  {
    label: t('值'),
    field: 'value',
    render: props.valueRender,
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
  line-height: 1.4 !important;
  font: inherit;
  color: inherit;
}
</style>
